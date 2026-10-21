"""只使用临时目标验证安装、备份和回退的实际行为。"""

from __future__ import annotations

import contextlib
import fnmatch
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check
import config_lib as lib
import install

SKILLS_READY = all((lib.ROOT / "config/skills" / name / ".git").exists()
                   for name in lib.load_json(lib.ROOT / "config/skills/sources.json"))


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.target = self.base / "opencode"
        self.payloads = [lib.Payload("opencode.json", data=b'{"new": true}\n'),
                         lib.Payload("agents/developer.md", source=lib.ROOT / "config/agents/developer.md")]

    def plan(self, payloads=None):
        return lib.plan_install(self.target, self.payloads if payloads is None else payloads)

    @unittest.skipUnless(SKILLS_READY, "技能子模块未初始化，稍后运行集成测试。")
    def test_default_cli_is_a_write_free_preview(self):
        result = subprocess.run([sys.executable, str(lib.ROOT / "scripts/install.py"),
                                 "--target", str(self.target)], capture_output=True, text=True,
                                env={**os.environ, "XDG_CONFIG_HOME": str(self.base / "xdg")})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("仅预览", result.stdout)
        self.assertFalse(self.target.exists())

    def test_conflict_fails_before_any_mutation(self):
        self.target.mkdir()
        old = self.target / "opencode.json"
        old.write_text("existing configuration")
        service = self.target / "service.json"
        service.write_text("service state")
        with self.assertRaises(lib.ConfigError):
            install.apply_plan(self.target, self.plan())
        self.assertEqual(old.read_text(), "existing configuration")
        self.assertEqual(service.read_text(), "service state")
        self.assertEqual({p.name for p in self.target.iterdir()}, {"opencode.json", "service.json"})

    def test_replace_backs_up_existing_and_preserves_unmanaged_files(self):
        self.target.mkdir()
        (self.target / "opencode.json").write_text("original")
        (self.target / "service.json").write_text("private state")
        skills = self.target / "skills/other"
        skills.mkdir(parents=True)
        (skills / "SKILL.md").write_text("existing skill")
        backup = install.apply_plan(self.target, self.plan(), replace_existing=True)
        self.assertEqual((backup / "opencode.json").read_text(), "original")
        self.assertEqual((self.target / "opencode.json").read_bytes(), self.payloads[0].data)
        self.assertTrue((self.target / "agents/developer.md").is_symlink())
        self.assertEqual((self.target / "service.json").read_text(), "private state")
        self.assertEqual((skills / "SKILL.md").read_text(), "existing skill")
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.target / "opencode.json").stat().st_mode & 0o777, 0o600)

    def test_repeated_install_is_a_noop(self):
        install.apply_plan(self.target, self.plan())
        paths = [self.target / "opencode.json", self.target / lib.STATE]
        times = [p.stat().st_mtime_ns for p in paths]
        plan = self.plan()
        self.assertTrue(all(change.status == "unchanged" for change in plan))
        self.assertIsNone(install.apply_plan(self.target, plan))
        self.assertEqual([p.stat().st_mtime_ns for p in paths], times)
        self.assertFalse((self.target / lib.BACKUPS).exists())

    def test_owned_generated_file_updates_with_backup(self):
        install.apply_plan(self.target, self.plan())
        newer = [lib.Payload("opencode.json", data=b'{"new": "version two"}\n'), self.payloads[1]]
        plan = self.plan(newer)
        self.assertEqual(plan[0].status, "update")
        backup = install.apply_plan(self.target, plan)
        self.assertEqual((backup / "opencode.json").read_bytes(), self.payloads[0].data)

    def test_manual_edits_are_not_overwritten_as_owned(self):
        install.apply_plan(self.target, self.plan())
        (self.target / "opencode.json").write_text("manual edit")
        self.assertEqual(self.plan()[0].status, "conflict")
        with self.assertRaises(lib.ConfigError):
            install.apply_plan(self.target, self.plan())
        self.assertEqual((self.target / "opencode.json").read_text(), "manual edit")

    def test_regular_directory_can_be_replaced_only_with_backup(self):
        folder = self.target / "agents/developer.md"
        folder.mkdir(parents=True)
        (folder / "keep.txt").write_text("keep")
        backup = install.apply_plan(self.target, self.plan(), replace_existing=True)
        self.assertEqual((backup / "agents/developer.md/keep.txt").read_text(), "keep")
        self.assertTrue(folder.is_symlink())

    def test_jsonc_is_retired_to_backup_instead_of_loading_two_configs(self):
        self.target.mkdir()
        (self.target / "opencode.jsonc").write_text("// old settings")
        plan = self.plan()
        self.assertEqual(plan[-1].payload.relative, "opencode.jsonc")
        with self.assertRaises(lib.ConfigError):
            install.apply_plan(self.target, plan)
        backup = install.apply_plan(self.target, plan, replace_existing=True)
        self.assertEqual((backup / "opencode.jsonc").read_text(), "// old settings")
        self.assertFalse((self.target / "opencode.jsonc").exists())

    def test_failed_write_restores_originals_and_removes_new_files(self):
        self.target.mkdir()
        (self.target / "opencode.json").write_text("original")
        original = install.write_payload

        def fail_on_agent(path, payload):
            if payload.relative == "agents/developer.md":
                raise OSError("simulated full disk")
            original(path, payload)

        with mock.patch.object(install, "write_payload", side_effect=fail_on_agent):
            with self.assertRaises(OSError):
                install.apply_plan(self.target, self.plan(), replace_existing=True)
        self.assertEqual((self.target / "opencode.json").read_text(), "original")
        self.assertFalse((self.target / "agents/developer.md").exists())
        self.assertFalse((self.target / lib.STATE).exists())
        self.assertFalse((self.target / lib.LOCK).exists())

    def test_changed_target_aborts_stale_plan(self):
        plan = self.plan()
        self.target.mkdir()
        (self.target / "opencode.json").write_text("concurrent edit")
        with self.assertRaises(lib.ConfigError):
            install.apply_plan(self.target, plan, replace_existing=True)
        self.assertEqual((self.target / "opencode.json").read_text(), "concurrent edit")
        self.assertFalse((self.target / lib.BACKUPS).exists())

    def test_symlinked_parent_is_rejected_without_touching_its_target(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.target.mkdir()
        (self.target / "agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(lib.ConfigError):
            self.plan()
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_state_and_backup_directory_are_rejected(self):
        self.target.mkdir()
        state = self.target / lib.STATE
        state.symlink_to(self.base / "missing.json")
        with self.assertRaises(lib.ConfigError):
            self.plan()
        state.unlink()
        (self.target / lib.BACKUPS).symlink_to(self.base / "outside")
        with self.assertRaises(lib.ConfigError):
            install.apply_plan(self.target, self.plan())
        self.assertFalse((self.target / "opencode.json").exists())

    def test_existing_lock_does_not_get_removed(self):
        self.target.mkdir()
        lock = self.target / lib.LOCK
        lock.write_text("other process")
        with self.assertRaises(lib.ConfigError):
            install.apply_plan(self.target, self.plan())
        self.assertEqual(lock.read_text(), "other process")

    def test_paths_cannot_escape_target(self):
        for relative in ("../outside", "/outside"):
            with self.subTest(relative=relative), self.assertRaises(lib.ConfigError):
                lib.plan_install(self.target, [lib.Payload(relative, data=b"bad")])

    @unittest.skipUnless(SKILLS_READY, "技能子模块未初始化，稍后运行集成测试。")
    def test_new_snapshot_links_and_installed_check(self):
        payloads = lib.build_payloads({})
        install.apply_plan(self.target, self.plan(payloads))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check.main(["--installed", "--target", str(self.target)]), 0)
        self.assertTrue((self.target / "skills/diagram-design/SKILL.md").is_file())
        skills = lib.registered_skills()
        self.assertEqual(len(skills), 28)
        self.assertEqual({p.name for p in (self.target / "skills").iterdir()}, set(skills))
        for name, source in skills.items():
            self.assertEqual((self.target / f"skills/{name}").resolve(), source.resolve())
            self.assertFalse((self.target / f"skills/{name}/.git").exists())


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        # 配置合并测试独立于第三方内容；真实技能链接由集成测试覆盖。
        patcher = mock.patch.object(lib, "registered_skills", return_value={})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_local_merge_replaces_arrays_and_preserves_other_keys(self):
        base = {"nested": {"keep": 1, "replace": [1, 2]}, "plain": True}
        override = {"nested": {"replace": [3]}}
        merged = lib.merge(base, override)
        self.assertEqual(merged, {"nested": {"keep": 1, "replace": [3]}, "plain": True})
        self.assertEqual(base["nested"]["replace"], [1, 2])

    def test_local_mcp_and_cli_overrides_reach_generated_files(self):
        payloads = lib.build_payloads({
            "opencode": {"mcp": {"servers": {"example": {"type": "local", "command": ["tool"]}}}},
            "cli": {"theme": {"mode": "light"}},
        })
        config = json.loads(payloads[0].data)
        cli = json.loads(payloads[1].data)
        self.assertEqual(config["mcp"]["servers"]["example"]["command"], ["tool"])
        self.assertEqual(config["providers"]["openai"]["body"]["service_tier"], "fast")
        self.assertEqual(cli["theme"], {"name": "opencode", "mode": "light"})

    def test_codegraph_is_portable_and_can_be_disabled_locally(self):
        config = json.loads(lib.build_payloads({})[0].data)
        server = config["mcp"]["servers"]["codegraph"]
        self.assertEqual(server, {"type": "local", "command": ["codegraph", "serve", "--mcp"],
                                  "codemode": False})
        config = json.loads(lib.build_payloads({"opencode": {"mcp": {"servers": {
            "codegraph": {"disabled": True}}}}})[0].data)
        self.assertTrue(config["mcp"]["servers"]["codegraph"]["disabled"])
        self.assertEqual(config["mcp"]["servers"]["codegraph"]["command"], server["command"])

    def test_old_mcp_shape_is_rejected(self):
        with self.assertRaises(lib.ConfigError):
            lib.build_payloads({"opencode": {"mcp": {"old": {"type": "local", "command": ["tool"]}}}})

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "local.json"
            path.write_text('{"opencode": {}, "opencode": {}}')
            with self.assertRaises(lib.ConfigError):
                lib.load_json(path)

    def test_configured_role_permissions_have_expected_boundaries(self):
        config = lib.load_json(lib.ROOT / "config/opencode.json")

        def decision(role, action, resource):
            effect = "allow"
            rules = config["permissions"] + config["agents"][role].get("permissions", [])
            for rule in rules:
                if fnmatch.fnmatchcase(action, rule["action"]) and fnmatch.fnmatchcase(resource, rule["resource"]):
                    effect = rule["effect"]
            return effect

        for role in ("developer", "architect", "reviewer", "brainstorm", "explore"):
            self.assertEqual(decision(role, "browser", "*"), "deny")
        for role in ("architect", "reviewer", "brainstorm"):
            self.assertEqual(decision(role, "edit", "src/example"), "deny")
            self.assertEqual(decision(role, "execute", "*"), "deny")
            self.assertEqual(decision(role, "read", ".env"), "ask")
            self.assertEqual(decision(role, "codegraph_codegraph_explore", "*"), "allow")
            self.assertEqual(decision(role, "codegraph_codegraph_index", "*"), "deny")
            self.assertEqual(decision(role, "other_tool", "*"), "deny")
        self.assertEqual(decision("reviewer", "shell", "python -m unittest"), "ask")
        self.assertEqual(decision("architect", "shell", "touch example"), "deny")
        self.assertEqual(decision("developer", "subagent", "reviewer"), "allow")
        self.assertEqual(decision("developer", "subagent", "general"), "deny")


class SkillRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.parent = self.root / "config/skills"
        self.source = self.parent / "example-skills"
        self.leaf = self.source / "skills/example"
        self.leaf.mkdir(parents=True)
        (self.source / ".git").write_text("gitdir: test-fixture\n")
        (self.leaf / "SKILL.md").write_text("---\nname: example\ndescription: >-\n  示例技能\n  用于检查\n---\n\n技能正文。\n")
        (self.root / ".gitmodules").write_text('[submodule "example-skills"]\n'
            '\tpath = config/skills/example-skills\n\turl = https://github.com/example/skills.git\n')
        self.definition = {"example-skills": {"repository": "https://github.com/example/skills.git",
            "description": "示例技能来源", "skills": {"example": "skills/example"}}}
        self.save()

    def save(self):
        (self.parent / "sources.json").write_text(json.dumps(self.definition))

    def test_registry_selects_only_leaf_and_reads_block_description(self):
        (self.source / "AGENTS.md").write_text("不应安装的上游指令。")
        extra = self.source / "skills/extra"
        extra.mkdir()
        (extra / "SKILL.md").write_text("未登记技能。")
        self.assertEqual(lib.registered_skills(self.root), {"example": self.leaf})
        metadata, _ = lib.frontmatter(self.leaf / "SKILL.md", {"name", "description"})
        self.assertEqual(metadata["description"], "示例技能 用于检查")

    def test_missing_submodule_is_reported_with_initialization_command(self):
        (self.source / ".git").unlink()
        with self.assertRaisesRegex(lib.ConfigError, "git submodule update --init --recursive"):
            lib.registered_skills(self.root)

    def test_repository_address_must_match_submodule(self):
        self.definition["example-skills"]["repository"] = "https://github.com/other/skills.git"
        self.save()
        with self.assertRaises(lib.ConfigError):
            lib.registered_skills(self.root)

    def test_invalid_or_escaping_skill_paths_are_rejected(self):
        for relative in ("../outside", "/outside", "skills/missing", "skills\\example"):
            with self.subTest(relative=relative):
                self.definition["example-skills"]["skills"]["example"] = relative
                self.save()
                with self.assertRaises(lib.ConfigError):
                    lib.registered_skills(self.root)

    def test_duplicate_ids_across_sources_are_rejected(self):
        other = self.parent / "other-skills"
        other.mkdir()
        (other / ".git").write_text("gitdir: test-fixture\n")
        with (self.root / ".gitmodules").open("a") as output:
            output.write('[submodule "other-skills"]\n\tpath = config/skills/other-skills\n'
                         '\turl = https://github.com/example/other.git\n')
        self.definition["other-skills"] = {"repository": "https://github.com/example/other.git",
            "description": "另一个来源", "skills": {"example": "skills/example"}}
        self.save()
        with self.assertRaisesRegex(lib.ConfigError, "重复"):
            lib.registered_skills(self.root)

    def test_resource_symlinks_cannot_escape_source(self):
        (self.leaf / "outside").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(lib.ConfigError):
            lib.registered_skills(self.root)


if __name__ == "__main__":
    unittest.main()
