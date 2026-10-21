"""可移植配置的读取与安装规划，仅依赖 Python 标准库。"""

from __future__ import annotations

import copy
import configparser
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ".opencode-config-state.json"
BACKUPS = ".opencode-config-backups"
LOCK = ".opencode-config.lock"
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MODEL = re.compile(r"^[^/#]+/[^#]+(?:#[^#]+)?$")
ROLES = {"developer": "primary", "architect": "all", "reviewer": "all", "brainstorm": "primary"}


class ConfigError(Exception):
    """不包含敏感值的输入错误或安装冲突。"""


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser().absolute()


def default_local() -> Path:
    return config_home() / "opencode-config/local.json"


def default_target() -> Path:
    return config_home() / "opencode"


def load_json(path: Path) -> dict:
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ConfigError(f"{path} 中存在重复的 JSON 键，请先移除。")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} 的 JSON 格式错误，位置：第 {exc.lineno} 行、第 {exc.colno} 列。") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{path} 的顶层必须是 JSON 对象。")
    return value


def merge(base: dict, override: dict) -> dict:
    """递归合并对象；数组与标量整体替换，不追加。"""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def frontmatter(path: Path, selected: set[str] | None = None) -> tuple[dict, str]:
    """读取自编文件使用的扁平 YAML 子集；上游技能只提取指定字段。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ConfigError(f"{path} 缺少前置元数据。")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ConfigError(f"{path} 的前置元数据缺少结束标记。") from exc
    metadata = {}
    for index, line in enumerate(lines[1:end], 1):
        if not line.strip():
            continue
        if selected is not None and not any(line.startswith(key + ":") for key in selected):
            continue
        match = re.fullmatch(r"([a-z_]+):\s*(.+)", line)
        if not match or match[1] in metadata:
            raise ConfigError(f"{path} 的自编元数据应使用不重复的扁平标量字段。")
        key, raw = match.groups()
        if selected is not None and raw in {">", ">-", "|", "|-"}:
            continuation = []
            for following in lines[index + 1:end]:
                if following and not following[0].isspace():
                    break
                continuation.append(following.strip())
            value = (" " if raw.startswith(">") else "\n").join(continuation).strip()
        elif raw.startswith("'") and raw.endswith("'"):
            value = raw[1:-1].replace("''", "'")
        elif raw.startswith('"'):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ConfigError(f"{path} 中带引号的元数据值无效。") from exc
            if not isinstance(value, str):
                raise ConfigError(f"{path} 的元数据值必须是字符串。")
        elif raw in {"true", "false"}:
            value = raw == "true"
        else:
            value = raw
        metadata[key] = value
    body = "\n".join(lines[end + 1:]).strip()
    if not body or not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        raise ConfigError(f"{path} 必须有描述和非空正文。")
    return metadata, body


def registered_skills(root: Path = ROOT) -> dict[str, Path]:
    """只登记明确选择的子模块技能入口，不加载上游插件和仓库指令。"""
    parent = root / "config/skills"
    sources = load_json(parent / "sources.json")
    modules = configparser.ConfigParser(interpolation=None)
    try:
        modules.read(root / ".gitmodules", encoding="utf-8")
    except configparser.Error as exc:
        raise ConfigError(".gitmodules 格式无效。") from exc
    result = {}
    for source, definition in sources.items():
        if not IDENTIFIER.fullmatch(source) or not isinstance(definition, dict):
            raise ConfigError("技能来源必须使用有效的名称和对象。")
        if set(definition) != {"repository", "description", "skills"}:
            raise ConfigError(f"技能来源 {source} 必须登记仓库地址、描述和技能映射。")
        repository, description, skills = (definition[key] for key in ("repository", "description", "skills"))
        if (not isinstance(repository, str) or not repository.startswith("https://github.com/")
                or not isinstance(description, str) or not description.strip()
                or not isinstance(skills, dict) or not skills):
            raise ConfigError(f"技能来源 {source} 的地址、描述或技能列表无效。")
        section = f'submodule "{source}"'
        if (not modules.has_section(section)
                or modules.get(section, "path", fallback="") != f"config/skills/{source}"
                or modules.get(section, "url", fallback="") != repository):
            raise ConfigError(f"技能来源 {source} 与 .gitmodules 的路径或地址不一致。")
        source_root = parent / source
        if source_root.is_symlink() or not (source_root / ".git").exists():
            raise ConfigError(f"技能子模块 {source} 尚未初始化，请运行 git submodule update --init --recursive。")
        for name, relative in skills.items():
            if not IDENTIFIER.fullmatch(name) or name in result:
                raise ConfigError(f"Skill ID 无效或重复：{name}。")
            if (not isinstance(relative, str) or not relative or Path(relative).is_absolute()
                    or ".." in Path(relative).parts or "\\" in relative):
                raise ConfigError(f"技能 {name} 的路径必须位于对应子模块中。")
            leaf = source_root / relative
            if leaf.is_symlink() or not leaf.resolve().is_relative_to(source_root.resolve()):
                raise ConfigError(f"技能 {name} 的路径越过了对应子模块。")
            if not (leaf / "SKILL.md").is_file():
                raise ConfigError(f"技能 {name} 缺少 SKILL.md，请检查登记路径和子模块版本。")
            metadata, _ = frontmatter(leaf / "SKILL.md", selected={"name", "description"})
            if metadata.get("name") != name:
                raise ConfigError(f"技能 {name} 的入口名称与登记名称不一致。")
            for path in leaf.rglob("*"):
                if path.is_symlink():
                    raise ConfigError(f"技能资源中不能包含本机符号链接：{path}。")
            result[name] = leaf
    return result


def validate_config(value: dict) -> None:
    legacy = {"provider", "agent", "command", "permission", "snapshot", "attachment", "autoupdate"}
    if legacy.intersection(value):
        raise ConfigError("请使用 V2 原生复数字段，迁移说明见 docs/setup.md。")
    if not isinstance(value.get("model"), str) or not MODEL.fullmatch(value["model"]):
        raise ConfigError("默认模型必须使用 provider/model 格式。")
    agents = value.get("agents")
    if not isinstance(agents, dict):
        raise ConfigError("agents 必须是对象。")
    for name, mode in ROLES.items():
        agent = agents.get(name)
        if not isinstance(agent, dict) or agent.get("mode") != mode:
            raise ConfigError(f"Agent {name} 必须使用 {mode} 模式。")
        if not isinstance(agent.get("model"), str) or not MODEL.fullmatch(agent["model"]):
            raise ConfigError(f"Agent {name} 必须指定 provider/model[#variant] 格式的模型。")
    if value.get("default_agent") not in {"developer", "architect", "reviewer", "brainstorm"}:
        raise ConfigError("default_agent 必须选择已安装且支持主会话的角色。")
    providers = value.get("providers", {})
    if not isinstance(providers, dict) or not isinstance(providers.get("openai"), dict):
        raise ConfigError("必须配置 openai 服务商。")
    body = providers["openai"].get("body", {})
    if not isinstance(body, dict) or body.get("service_tier") != "priority":
        raise ConfigError("Fast 模式应使用订阅通道兼容的 service_tier=priority。")
    rule_sets = [value.get("permissions", [])]
    for agent in agents.values():
        if not isinstance(agent, dict):
            raise ConfigError("每个 Agent 配置都必须是对象。")
        rule_sets.append(agent.get("permissions", []))
    for rules in rule_sets:
        if not isinstance(rules, list):
            raise ConfigError("permissions 必须是有序数组。")
        for rule in rules:
            if (not isinstance(rule, dict) or set(rule) != {"action", "resource", "effect"}
                    or not all(isinstance(v, str) for v in rule.values())
                    or rule["effect"] not in {"allow", "ask", "deny"}):
                raise ConfigError("权限规则的 action、resource 或 effect 无效。")
    mcp = value.get("mcp", {})
    if not isinstance(mcp, dict) or set(mcp) - {"servers", "timeout"}:
        raise ConfigError("V2 MCP 服务必须定义在 mcp.servers 下。")
    servers = mcp.get("servers", {})
    if not isinstance(servers, dict):
        raise ConfigError("mcp.servers 必须是对象。")
    for server in servers.values():
        if not isinstance(server, dict) or "enabled" in server:
            raise ConfigError("MCP 服务必须是对象，并使用 disabled 而非 enabled。")
        if server.get("type") == "local":
            command = server.get("command")
            if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
                raise ConfigError("本地 MCP 服务必须提供非空命令参数数组。")
        elif server.get("type") == "remote":
            if not isinstance(server.get("url"), str) or not server["url"].startswith(("http://", "https://")):
                raise ConfigError("远程 MCP 服务必须提供 HTTP(S) 地址。")
        else:
            raise ConfigError("MCP 类型必须是 local 或 remote。")


def validate_repository(root: Path = ROOT) -> None:
    base = root / "config"
    validate_config(load_json(base / "opencode.json"))
    cli = load_json(base / "cli.json")
    if cli.get("$schema") != "https://opencode.ai/v2/cli.json":
        raise ConfigError("终端配置必须引用 V2 CLI Schema。")
    for name in ROLES:
        metadata, _ = frontmatter(base / f"agents/{name}.md")
        if set(metadata) != {"description"}:
            raise ConfigError("模型、模式和权限应集中维护在 config/opencode.json。")
    for command in (base / "commands").glob("*.md"):
        metadata, body = frontmatter(command)
        if metadata.get("agent") not in ROLES or not isinstance(metadata.get("subagent"), bool):
            raise ConfigError(f"命令 {command.name} 必须选择角色并明确是否启动子会话。")
        if "$ARGUMENTS" not in body:
            raise ConfigError(f"命令 {command.name} 必须接收参数。")
        if "!`" in body:
            raise ConfigError(f"命令 {command.name} 不得在模板展开时执行 Shell 片段。")
    registered_skills(root)
    own_paths = [base / "AGENTS.md", base / "opencode.json", base / "cli.json", base / "skills"]
    for kind in ("agents", "commands"):
        own_paths.extend((base / kind).rglob("*"))
        own_paths.append(base / kind)
    for path in own_paths:
        if path.is_symlink():
            raise ConfigError(f"配置源中不能包含本机符号链接：{path}。")


def load_local(path: Path | None) -> dict:
    if path is None:
        path = default_local()
        if not path.exists() and not path.is_symlink():
            return {}
    result = load_json(path)
    if set(result) - {"opencode", "cli"}:
        raise ConfigError("本机覆盖只接受 opencode 和 cli 两个分区。")
    if any(not isinstance(v, dict) for v in result.values()):
        raise ConfigError("本机覆盖的每个分区都必须是对象。")
    return result


@dataclass(frozen=True)
class Payload:
    relative: str
    data: bytes | None = None
    source: Path | None = None

    @property
    def signature(self) -> str | None:
        if self.source is not None:
            return "link:" + str(self.source)
        if self.data is not None:
            return "file:" + hashlib.sha256(self.data).hexdigest()
        return None  # 停用另一份配置，移走前必须备份。


def build_payloads(local: dict, root: Path = ROOT) -> list[Payload]:
    base = root.resolve() / "config"
    config = merge(load_json(base / "opencode.json"), local.get("opencode", {}))
    validate_config(config)
    cli = merge(load_json(base / "cli.json"), local.get("cli", {}))
    payloads = [Payload("opencode.json", data=json_bytes(config)), Payload("cli.json", data=json_bytes(cli)),
                Payload("AGENTS.md", source=base / "AGENTS.md")]
    for kind in ("agents", "commands"):
        for path in sorted((base / kind).rglob("*.md")):
            payloads.append(Payload(path.relative_to(base).as_posix(), source=path))
    for name, path in sorted(registered_skills(root.resolve()).items()):
        payloads.append(Payload(f"skills/{name}", source=path))
    return payloads


def fingerprint(path: Path) -> str | None:
    if path.is_symlink():
        return "link:" + os.readlink(path)
    if path.is_file():
        return "file:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if path.exists():
        return "directory" if path.is_dir() else "special"
    return None


def guard_path(target: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ConfigError("受管理路径必须位于目标目录内。")
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ConfigError("目标必须是真实目录，不能是符号链接或文件。")
    current = target
    for part in rel.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise ConfigError(f"父目录 {current} 存在冲突，必须使用真实目录。")
    return target / rel


@dataclass(frozen=True)
class Change:
    payload: Payload
    before: str | None
    status: str


def load_state(target: Path) -> dict:
    path = guard_path(target, STATE)
    if path.is_symlink():
        raise ConfigError("安装状态文件不能是符号链接。")
    if not path.exists():
        return {"version": 1, "entries": {}}
    state = load_json(path)
    if state.get("version") != 1 or not isinstance(state.get("entries"), dict):
        raise ConfigError("无法识别安装状态，请检查后再继续。")
    return state


def plan_install(target: Path, payloads: list[Payload]) -> list[Change]:
    owned = load_state(target)["entries"]
    if (target / "opencode.jsonc").exists() or (target / "opencode.jsonc").is_symlink():
        payloads = payloads + [Payload("opencode.jsonc")]
    changes = []
    for payload in payloads:
        path = guard_path(target, payload.relative)
        before = fingerprint(path)
        if payload.signature is not None and before == payload.signature:
            # 生成文件的私有权限也是安装要求；沿用更新、备份与回退流程。
            status = "update" if payload.data is not None and stat.S_IMODE(path.stat().st_mode) != 0o600 else "unchanged"
        elif before is None:
            status = "create"
        elif payload.signature is not None and owned.get(payload.relative) == before:
            status = "update"
        else:
            status = "conflict"
        changes.append(Change(payload, before, status))
    return changes
