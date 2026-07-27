from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
TEMP_ROOT = ROOT / ".test-tmp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pipeline = load_module("vidmuse_pipeline", SKILLS / "vidmuse-style-pipeline" / "scripts" / "run_pipeline.py")
normalizer = load_module("vidmuse_normalizer", SKILLS / "vidmuse-style-source-mining" / "scripts" / "normalize_evidence.py")
evidence_validator = load_module("vidmuse_evidence_validator", SKILLS / "vidmuse-style-source-mining" / "scripts" / "validate_evidence.py")
concept_validator = load_module("validate_concepts", SKILLS / "vidmuse-style-concept-curation" / "scripts" / "validate_concepts.py")
catalog_snapshot = load_module("snapshot_official_catalog", SKILLS / "vidmuse-style-concept-curation" / "scripts" / "snapshot_official_catalog.py")
review_builder = load_module("vidmuse_review_builder", SKILLS / "vidmuse-style-concept-curation" / "scripts" / "build_review_packet.py")
record_validator = load_module("validate_style_record", SKILLS / "vidmuse-style-record-production" / "scripts" / "validate_style_record.py")
record_exporter = load_module("vidmuse_record_exporter", SKILLS / "vidmuse-style-record-production" / "scripts" / "export_records.py")
preview_packager = load_module("vidmuse_preview_packager", SKILLS / "vidmuse-style-record-production" / "scripts" / "package_previews.py")


class SkillSuiteTests(unittest.TestCase):
    def tempdir(self):
        return tempfile.TemporaryDirectory(dir=TEMP_ROOT)

    def make_image(self, path: Path, color: tuple[int, int, int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 36), color).save(path)

    def test_pipeline_gates_freeze_and_reopen_without_deleting(self) -> None:
        with self.tempdir() as directory:
            run_dir = Path(directory) / "run"
            args = type("Args", (), {
                "run_dir": run_dir,
                "name": "Cross Source Run",
                "source": ["art", "architecture"],
                "standards_manifest": None,
            })
            pipeline.command_init(args)
            source_dir = run_dir / "01-source-plan"
            (source_dir / "source-assessment.md").write_text("accepted source", encoding="utf-8")
            (source_dir / "collection-plan.json").write_text("{}", encoding="utf-8")
            (source_dir / "sample" / "raw-manifest.jsonl").write_text('{"id":"one"}\n', encoding="utf-8")
            (source_dir / "official-style-catalog.json").write_text('{"environment":"dev","styles":[]}', encoding="utf-8")
            approve = type("Args", (), {"run_dir": run_dir, "stage": "source-plan", "reviewer": "PM", "note": "approved"})
            pipeline.command_approve(approve)
            manifest = pipeline.load_manifest(run_dir)
            self.assertEqual("approved", manifest["stages"]["source-plan"]["status"])
            self.assertEqual("ready", manifest["stages"]["evidence"]["status"])
            self.assertEqual([], pipeline.approval_drift(run_dir, manifest, "source-plan"))
            (source_dir / "source-assessment.md").write_text("changed", encoding="utf-8")
            self.assertEqual(["source-assessment.md"], pipeline.approval_drift(run_dir, manifest, "source-plan"))
            reopen = type("Args", (), {"run_dir": run_dir, "stage": "source-plan", "reviewer": "PM", "note": "source changed"})
            pipeline.command_reopen(reopen)
            manifest = pipeline.load_manifest(run_dir)
            self.assertEqual("ready", manifest["stages"]["source-plan"]["status"])
            self.assertEqual("blocked", manifest["stages"]["evidence"]["status"])
            self.assertTrue((source_dir / "source-assessment.md").exists())
            self.assertTrue(list((run_dir / "approvals").glob("*.json")))

    def test_collection_plan_declares_independence_and_coverage(self) -> None:
        with self.tempdir() as directory:
            base = Path(directory)
            plan = {
                "source": {"name": "Artwork archive", "urls": ["https://example.test"]},
                "media": ["painting"],
                "evidenceUnit": {"unitType": "artwork", "capabilities": ["static_appearance"], "sourceGroupPolicy": "Series or collection at the claim level.", "contextPolicy": "Whole work and detail crops share one context.", "independencePolicy": "One original artwork after duplicate collapse."},
                "collection": {"primaryRoute": "public dataset", "checkpointKey": "page", "dedupeKey": "work id"},
                "coverage": {"catalogSnapshot": "official-style-catalog.json", "target": "Representative works across the declared collection.", "strata": ["period", "medium"], "stopConditions": ["planned strata covered", "source exhausted"]},
                "rights": {"licenseStatus": "research_only", "researchOnly": True},
                "pilot": {"routesToExercise": ["browse", "download"], "successConditions": ["assets and provenance resolve"], "stopConditions": ["access restriction"]},
                "channelMapping": {"style": ["palette", "mark making"], "content": ["subject"], "provenance": ["artist", "work"]},
            }
            path = base / "collection-plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            command = [sys.executable, str(SKILLS / "vidmuse-style-source-mining" / "scripts" / "validate_collection_plan.py"), str(path)]
            self.assertEqual(0, subprocess.run(command, capture_output=True, text=True).returncode)
            del plan["evidenceUnit"]["independencePolicy"]
            path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(1, subprocess.run(command, capture_output=True, text=True).returncode)

    def test_cross_source_normalization_is_not_film_specific(self) -> None:
        with self.tempdir() as directory:
            base = Path(directory)
            self.make_image(base / "assets" / "art.png", (20, 40, 100))
            self.make_image(base / "assets" / "building.png", (100, 90, 70))
            self.make_image(base / "assets" / "game.png", (30, 90, 120))
            (base / "assets" / "clip.mp4").write_bytes(b"continuous-video-fixture")
            rows = [
                {"id": "art-1", "url": "https://example.test/art/1", "path": "art.png", "unit": "artwork", "medium": "painting", "group": "collection-a", "context": "gallery-a", "caps": ["static_appearance", "authorship_context"], "color": ["muted blue"], "form": ["flat geometry"], "texture": ["visible brushwork"], "subject": ["portrait"], "creator": ["Artist A"], "anchor_type": "artist"},
                {"id": "building-1", "url": "https://example.test/building/1", "path": "building.png", "unit": "architecture_view", "medium": "spatial_design", "group": "building-a", "context": "facade-set", "caps": ["static_appearance"], "color": ["neutral stone"], "form": ["repeated bays"], "texture": ["weathered concrete"], "subject": ["office"], "creator": ["Architect A"], "anchor_type": "architect"},
                {"id": "game-1", "url": "https://example.test/game/1", "path": "game.png", "unit": "game_capture", "medium": "3d_render", "group": "game-a", "context": "environment-set", "caps": ["static_appearance"], "color": ["cyan accents"], "form": ["low-poly massing"], "texture": ["matte procedural material"], "subject": ["environment"], "creator": ["Studio A"], "anchor_type": "studio"},
                {"id": "clip-1", "url": "https://example.test/video/1", "path": "clip.mp4", "unit": "video_segment", "medium": "live_action", "group": "mv-a", "context": "sequence-1", "caps": ["continuous_motion"], "color": ["cyan shadows"], "form": ["off-axis staging"], "texture": ["digital noise"], "subject": ["performer"], "creator": ["Director A"], "anchor_type": "director"},
            ]
            mapping = {
                "sourceName": "multi-source",
                "fields": {"id": "id", "source": "url", "localAssetPath": "path", "unitType": "unit", "medium": "medium", "sourceGroupKey": "group", "contextKey": "context", "independenceKey": "id", "evidenceCapabilities": "caps"},
                "defaults": {"licenseStatus": "research_only", "researchOnly": True},
                "styleFields": {"color_tonality": "color", "form_shape": "form", "material_texture": "texture"},
                "contentFields": {"subjects": "subject"},
                "provenanceFields": {"creators": "creator"},
                "anchorMembershipFields": [{"anchorTypeField": "anchor_type", "anchorNameField": "creator", "basis": "source_metadata"}],
            }
            evidence, quarantine = normalizer.normalize(rows, mapping, base / "assets")
            self.assertEqual([], quarantine)
            self.assertEqual(4, len(evidence))
            self.assertEqual({"artwork", "architecture_view", "game_capture", "video_segment"}, {item["unitType"] for item in evidence})
            memberships = {item["provenance"]["anchorMemberships"][0]["anchorType"] for item in evidence}
            self.assertEqual({"artist", "architect", "studio", "director"}, memberships)
            clip = next(item for item in evidence if item["unitType"] == "video_segment")
            self.assertEqual(["continuous_motion"], clip["evidenceCapabilities"])
            self.assertIsNone(clip["differenceHash"])
            issues = evidence_validator.validate(evidence, base / "assets")
            self.assertEqual([], issues)

    def evidence_fixture(self, base: Path):
        rows = []
        for index, group in enumerate(("work-a", "work-b", "work-c", "work-d", "work-e", "work-f"), start=1):
            path = base / f"{index}.png"
            self.make_image(path, (index * 25, 40, 80))
            rows.append({
                "evidenceId": f"ev-{index}", "unitType": "photograph", "medium": "photography",
                "source": f"https://example.test/{index}", "localAssetPath": path.name,
                "sourceGroupKey": group, "contextKey": f"ctx-{index}", "independenceKey": f"unit-{index}",
                "styleFeatures": {"color_tonality": ["muted"], "lighting_shadow": ["directional"], "composition_spatial": ["layered"]},
                "contentFeatures": {"subjects": ["neutral"]}, "evidenceCapabilities": ["static_appearance"],
                "provenance": {"sourceId": [str(index)]}, "licenseStatus": "research_only", "researchOnly": True,
                "fileSha256": "a" * 63 + str(index % 10), "differenceHash": None, "duplicateOf": None, "nearDuplicateOf": None,
            })
        return rows

    def test_evidence_validator_rehashes_local_assets(self) -> None:
        with self.tempdir() as directory:
            base = Path(directory)
            evidence = self.evidence_fixture(base)[:1]
            evidence[0]["fileSha256"] = normalizer.sha256_file(base / "1.png")
            self.assertNotIn("asset.hash_mismatch", {item.code for item in evidence_validator.validate(evidence, base)})
            self.make_image(base / "1.png", (200, 10, 10))
            self.assertIn("asset.hash_mismatch", {item.code for item in evidence_validator.validate(evidence, base)})

    def anonymous_fixtures(self):
        signature_a = {
            "summary": "Layered restrained photographic grammar.",
            "transferableInvariants": [
                {"dimension": "color_tonality", "rule": "Restrained cool values.", "evidenceIds": ["ev-1", "ev-2"]},
                {"dimension": "lighting_shadow", "rule": "Directional soft light.", "evidenceIds": ["ev-1", "ev-2"]},
                {"dimension": "composition_spatial", "rule": "Layered off-center depth.", "evidenceIds": ["ev-1", "ev-2"]},
            ],
            "allowedVariation": ["Interior and exterior subjects remain inside the grammar."],
            "excludedSourceMotifs": ["Named performers and locations"],
        }
        signature_b = json.loads(json.dumps(signature_a))
        signature_b["summary"] = "Formal warm photographic grammar."
        signature_b["transferableInvariants"] = [
            {"dimension": "color_tonality", "rule": "Warm compressed values.", "evidenceIds": ["ev-4", "ev-5"]},
            {"dimension": "lighting_shadow", "rule": "Hard frontal light.", "evidenceIds": ["ev-4", "ev-5"]},
            {"dimension": "composition_spatial", "rule": "Centered shallow staging.", "evidenceIds": ["ev-4", "ev-5"]},
        ]
        return [
            {"anonymousCandidateId": "anon-0001", "anonymousLabel": "Cluster 0001", "sealedRangeRefs": ["range-0001"], "signature": signature_a, "evidence": {"memberEvidenceIds": ["ev-1", "ev-2"], "holdoutEvidenceIds": ["ev-3"]}, "candidateNeighbors": ["anon-0002"], "uncertainty": {"level": "medium", "reason": "Needs neighbor review."}},
            {"anonymousCandidateId": "anon-0002", "anonymousLabel": "Cluster 0002", "sealedRangeRefs": ["range-0002"], "signature": signature_b, "evidence": {"memberEvidenceIds": ["ev-4", "ev-5"], "holdoutEvidenceIds": ["ev-6"]}, "candidateNeighbors": ["anon-0001"], "uncertainty": {"level": "medium", "reason": "Needs neighbor review."}},
        ]

    def hypothesis_fixtures(self):
        anonymous = self.anonymous_fixtures()
        first = {
            "hypothesisId": "hyp-0001", "anonymousCandidateId": "anon-0001", "anonymousLabel": "Cluster 0001",
            "anchor": {"type": "work", "name": "Example Work", "scope": "one work"},
            "scope": {"media": ["photography"], "contentDependency": {"mode": "none", "values": []}},
            "signature": anonymous[0]["signature"],
            "evidence": {"coreEvidenceIds": ["ev-1", "ev-2"], "variationEvidenceIds": ["ev-3"]},
            "boundary": [{"jointTestId": "boundary-0001", "neighborHypothesisId": "hyp-0002", "relationTest": "peer", "targetEvidenceIds": ["ev-1", "ev-2"], "neighborEvidenceIds": ["ev-4", "ev-5"], "distinguishingRules": ["The target keeps cooler values and deeper layered space."], "status": "available"}],
            "aiRecommendation": {"outcome": "advance", "confidence": "medium", "reason": "Three invariant dimensions remain coherent across independent evidence."},
        }
        second = {
            "hypothesisId": "hyp-0002", "anonymousCandidateId": "anon-0002", "anonymousLabel": "Cluster 0002",
            "anchor": {"type": "work", "name": "Neighbor Work", "scope": "one work"},
            "scope": {"media": ["photography"], "contentDependency": {"mode": "none", "values": []}},
            "signature": anonymous[1]["signature"],
            "evidence": {"coreEvidenceIds": ["ev-4", "ev-5"], "variationEvidenceIds": ["ev-6"]},
            "boundary": [{"jointTestId": "boundary-0001", "neighborHypothesisId": "hyp-0001", "relationTest": "peer", "targetEvidenceIds": ["ev-4", "ev-5"], "neighborEvidenceIds": ["ev-1", "ev-2"], "distinguishingRules": ["The target keeps warmer values and shallower centered space."], "status": "available"}],
            "aiRecommendation": {"outcome": "advance", "confidence": "medium", "reason": "Three invariant dimensions remain coherent across independent evidence."},
        }
        return [first, second]

    def test_live_catalog_snapshot_paginates_cli_results(self) -> None:
        with self.tempdir() as directory:
            config = Path(directory) / "dev-config.json"
            config.write_text(json.dumps({"baseUrl": "https://vidmuse-dev.example.test", "sessionToken": "secret"}), encoding="utf-8")
            calls = []

            def fake_runner(command, **kwargs):
                calls.append((command, kwargs))
                if command[-1] == "--version" or command[1:] == ["--version"]:
                    return subprocess.CompletedProcess(command, 0, stdout="v-test\n", stderr="")
                offset = int(command[command.index("--offset") + 1])
                page = [{"id": f"style-{offset + index}", "name": f"Style {offset + index}"} for index in range(2 if offset == 0 else 1)]
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"data": page}), stderr="")

            payload = catalog_snapshot.capture("vidmuse", page_size=2, config_path=config, runner=fake_runner)
            self.assertEqual(3, payload["styleCount"])
            self.assertEqual("dev", payload["environment"])
            self.assertEqual("https://vidmuse-dev.example.test", payload["endpoint"])
            self.assertEqual("official", payload["scope"])
            commands = [command for command, _ in calls]
            self.assertEqual([0, 2], [int(call[call.index("--offset") + 1]) for call in commands if "--offset" in call])
            self.assertTrue(all(kwargs["env"]["VIDMUSE_CONFIG"] == str(config) for _, kwargs in calls))

            prod_config = Path(directory) / "prod-config.json"
            prod_config.write_text(json.dumps({"baseUrl": "https://vidmuse.ai", "sessionToken": "secret"}), encoding="utf-8")
            self.assertEqual("https://vidmuse.ai", catalog_snapshot.load_config(prod_config, "prod"))
            prod_payload = catalog_snapshot.capture("vidmuse", page_size=2, environment="prod", config_path=prod_config, runner=fake_runner)
            self.assertEqual("prod", prod_payload["environment"])
            self.assertEqual("https://vidmuse.ai", prod_payload["endpoint"])
            with self.assertRaises(catalog_snapshot.SnapshotError):
                catalog_snapshot.load_config(prod_config, "dev")

    def test_concept_boundary_requires_disjoint_evidence_and_source_groups(self) -> None:
        with self.tempdir() as directory:
            base = Path(directory)
            evidence = self.evidence_fixture(base)
            hypotheses = self.hypothesis_fixtures()
            anonymous = self.anonymous_fixtures()
            self.assertEqual([], concept_validator.validate(evidence, hypotheses, anonymous_candidates=anonymous))
            bad = json.loads(json.dumps(hypotheses))
            bad[0]["boundary"][0]["neighborEvidenceIds"] = ["ev-2", "ev-4"]
            codes = {item.code for item in concept_validator.validate(evidence, bad, anonymous_candidates=anonymous)}
            self.assertIn("boundary.shared_evidence", codes)

    def test_parent_child_boundary_excludes_child_source_groups(self) -> None:
        with self.tempdir() as directory:
            evidence = self.evidence_fixture(Path(directory))
            hypotheses = self.hypothesis_fixtures()
            for current, target_role, neighbor_role in ((hypotheses[0], "parent", "child"), (hypotheses[1], "child", "parent")):
                boundary = current["boundary"][0]
                boundary["relationTest"] = "parent_child"
                boundary["targetRole"] = target_role
                boundary["neighborRole"] = neighbor_role
                boundary["siblingExclusion"] = {"childSourceGroupKeys": ["work-d", "work-e"], "broadSideSourceGroupKeys": ["work-a", "work-b"], "coverageRationale": "The broad side represents the tested non-child range without reusing child evidence."}
            issues = concept_validator.validate(evidence, hypotheses, anonymous_candidates=self.anonymous_fixtures())
            self.assertEqual([], issues)
            hypotheses[0]["boundary"][0]["siblingExclusion"]["childSourceGroupKeys"] = ["work-a"]
            codes = {item.code for item in concept_validator.validate(evidence, hypotheses, anonymous_candidates=self.anonymous_fixtures())}
            self.assertIn("boundary.child_leak_into_parent", codes)

    def test_review_packet_is_source_hidden_and_self_contained(self) -> None:
        with self.tempdir() as directory:
            base = Path(directory)
            evidence = self.evidence_fixture(base)
            hypotheses = self.hypothesis_fixtures()
            rendered = review_builder.render_packet(evidence, hypotheses, base, reveal=False)
            self.assertIn("Cluster 0001", rendered)
            self.assertNotIn("Example Work", rendered)
            self.assertNotIn("ev-1", rendered)
            self.assertNotIn("hyp-0001", rendered)
            self.assertIn("data:image/png;base64,", rendered)

    def test_decision_template_is_jsonl_and_matches_validator_contract(self) -> None:
        with self.tempdir() as directory:
            path = Path(directory) / "decision-registry.template.jsonl"
            hypotheses = self.hypothesis_fixtures()
            review_builder.write_decision_template(path, hypotheses)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(2, len(rows))
            self.assertIn("relations", rows[0])
            self.assertIn("resultingHypothesisIds", rows[0])
            self.assertEqual("ai_proposed", rows[0]["reviewStatus"])
            self.assertEqual(hypotheses[0]["aiRecommendation"]["outcome"], rows[0]["decision"])
            issues = concept_validator.validate(self.evidence_fixture(Path(directory)), hypotheses, decisions=rows, anonymous_candidates=self.anonymous_fixtures())
            self.assertEqual([], issues)

    def valid_record(self):
        return {
            "name": "Risograph Print",
            "tags": ["Graphic Design", "Risograph Printmaking", "Limited Spot Colors", "Misregistered Layers", "Halftone Grain"],
            "description": "A tactile graphic identity built from limited spot-color layers, translucent overprint, registration drift, and porous paper texture. It suits lyric videos, album visuals, and rhythmic graphic MVs that need handmade editorial energy rather than clean vector polish.",
            "analysis": "**Print Process & Form:** Stencil-like ink layers keep shapes flat and separated. **Color System:** Limited translucent spot colors create secondary hues through overprint. **Composition & Graphic Space:** Bold crops, negative space, and repeated forms organize the frame. **Texture & Finish:** Halftone dots, porous ink, paper fiber, and small registration offsets remain visible. **Transfer & Boundary:** The grammar transfers across abstract forms, objects, environments, and simplified figures without collapsing into clean vector minimalism.",
            "promptSample": "Risograph printmaking, limited translucent spot-color layers, visible overprint interactions, slight misregistration, flat graphic shapes, coarse halftone and paper-fiber texture",
            "imageUrl": "",
        }

    def test_staging_schema_accepts_empty_url_and_production_rejects_it(self) -> None:
        record = self.valid_record()
        staging = record_validator.load_schema(record_validator.STAGING_SCHEMA_PATH)
        production = record_validator.load_schema(record_validator.SCHEMA_PATH)
        staging_codes = {item.code for item in record_validator.validate_records([record], schema=staging)}
        production_codes = {item.code for item in record_validator.validate_records([record], schema=production)}
        self.assertNotIn("schema.pattern", staging_codes)
        self.assertTrue({"schema.pattern", "schema.format"} & production_codes)
        https_record = self.valid_record()
        https_record["imageUrl"] = "https://example.test/preview.png"
        self.assertIn("schema.const", {item.code for item in record_validator.validate_records([https_record], schema=staging)})

    def test_prompt_sample_may_omit_the_style_name(self) -> None:
        record = self.valid_record()
        record["promptSample"] = "Poetic naturalism, luminous natural backlight, intimate wide-angle perspective, layered threshold depth, restrained organic color, tactile film texture"
        self.assertNotIn("prompt.anchor_not_first", {item.code for item in record_validator.validate_records([record], schema=record_validator.load_schema(record_validator.STAGING_SCHEMA_PATH))})

    def test_export_round_trip_and_one_reference_image_mapping(self) -> None:
        with self.tempdir() as directory:
            base = Path(directory)
            record = self.valid_record()
            prompts = {record["name"]: "An original arrangement of bold abstract forms with translucent spot-color overlaps, slight registration drift, coarse halftone grain, and porous paper texture."}
            output = base / "delivery"
            record_exporter.write_outputs([record], prompts, output)
            self.assertEqual(record, json.loads((output / "styles.json").read_text(encoding="utf-8"))[0])
            with (output / "preview-manifest.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(1, len(rows))
            self.make_image(output / "previews" / rows[0]["fileName"], (50, 30, 90))
            result = preview_packager.validate(output / "preview-manifest.csv", output / "previews")
            self.assertEqual([], result["errors"])
            self.assertEqual([], result["warnings"])
            self.assertEqual(1, result["styles"])
            self.assertEqual(1, result["images"])

    def test_active_skill_links_schemas_and_metadata_are_self_contained(self) -> None:
        skill_dirs = [
            SKILLS / "vidmuse-style-pipeline",
            SKILLS / "vidmuse-style-source-mining",
            SKILLS / "vidmuse-style-concept-curation",
            SKILLS / "vidmuse-style-record-production",
        ]
        for skill_dir in skill_dirs:
            metadata = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn("$" + skill_dir.name, metadata)
            for schema_path in skill_dir.rglob("*.schema.json"):
                Draft202012Validator.check_schema(json.loads(schema_path.read_text(encoding="utf-8")))
            for markdown_path in skill_dir.rglob("*.md"):
                if "historical" in markdown_path.parts:
                    continue
                text = markdown_path.read_text(encoding="utf-8")
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                    target = target.strip().strip("<>").split("#", 1)[0]
                    if not target or re.match(r"^(?:https?://|mailto:)", target):
                        continue
                    self.assertTrue((markdown_path.parent / target).resolve().exists(), f"broken link {target} in {markdown_path}")

    def test_chinese_skill_mirrors_are_synchronized(self) -> None:
        command = [sys.executable, str(SKILLS / "vidmuse-style-pipeline" / "scripts" / "validate_localizations.py"), "--skills-root", str(SKILLS)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_standards_manifest_verifies_bundled_references(self) -> None:
        command = [sys.executable, str(SKILLS / "vidmuse-style-pipeline" / "scripts" / "verify_standards.py"), "check"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()