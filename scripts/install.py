#!/usr/bin/env python3
"""默认只预览；显式应用时备份旧文件，普通写入失败时回退本次修改。"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config_lib import (
    BACKUPS, LOCK, ROOT, STATE, Change, ConfigError, Payload, build_payloads,
    default_target, fingerprint, guard_path, json_bytes, load_local, load_state,
    plan_install, validate_repository,
)


def write_payload(path: Path, payload: Payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / (".opencode-config-tmp-" + uuid.uuid4().hex)
    try:
        if payload.source is not None:
            temporary.symlink_to(payload.source, target_is_directory=payload.source.is_dir())
        elif payload.data is not None:
            descriptor, filename = tempfile.mkstemp(prefix=".opencode-config-tmp-", dir=path.parent)
            temporary = Path(filename)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload.data)
        else:
            return
        os.replace(temporary, path)
    finally:
        if temporary.is_symlink() or temporary.exists():
            temporary.unlink()


def apply_plan(target: Path, changes: list[Change], replace_existing: bool = False) -> Path | None:
    if any(c.status == "conflict" for c in changes) and not replace_existing:
        raise ConfigError("现有内容存在冲突。请先预览并迁移必要配置，再用 --replace-existing 明确替换。")
    # 创建锁或目录前，重新检查状态与父目录。
    load_state(target)
    for change in changes:
        path = guard_path(target, change.payload.relative)
        if fingerprint(path) != change.before:
            raise ConfigError(f"预览后目标已变化：{change.payload.relative}，请重新预览。")
    guard_path(target, f"{BACKUPS}/placeholder")
    target.mkdir(parents=True, exist_ok=True)
    lock = guard_path(target, LOCK)
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ConfigError("可能有另一个安装进程正在运行，请先检查现有锁文件。") from exc
    os.close(descriptor)
    journal: list[tuple[Path, Path | None]] = []
    backup_root = None
    try:
        # 另一个安装进程可能恰好在获取锁之前完成，再检查一次。
        for change in changes:
            if fingerprint(guard_path(target, change.payload.relative)) != change.before:
                raise ConfigError("获取锁期间目标发生变化，请重新预览。")
        for change in changes:
            if change.status == "unchanged":
                continue
            path = guard_path(target, change.payload.relative)
            if fingerprint(path) != change.before:
                raise ConfigError(f"安装期间目标发生变化：{change.payload.relative}。")
            backup = None
            if change.before is not None:
                if backup_root is None:
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
                    backups = target / BACKUPS
                    backups.mkdir(mode=0o700, exist_ok=True)
                    os.chmod(backups, 0o700)
                    backup_root = backups / stamp
                    backup_root.mkdir(mode=0o700)
                backup = backup_root / change.payload.relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, backup)
            journal.append((path, backup))
            write_payload(path, change.payload)
        state = {
            "version": 1,
            "repository": str(ROOT),
            "entries": {c.payload.relative: c.payload.signature for c in changes if c.payload.signature is not None},
        }
        previous = load_state(target)
        if state != previous:
            write_payload(target / STATE, Payload(STATE, data=json_bytes(state)))
    except BaseException:
        for path, backup in reversed(journal):
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                # 本脚本只创建文件或链接，不能删除意外出现的目录。
                raise ConfigError(f"回退需要人工检查 {path}，备份位置：{backup}。")
            if backup is not None:
                os.replace(backup, path)
        raise
    finally:
        lock.unlink()
    return backup_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=default_target(), help="OpenCode 全局配置目录")
    parser.add_argument("--local", type=Path, help="本机 JSON 覆盖文件，默认位于配置根目录的 opencode-config/local.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="应用显示的安装计划")
    mode.add_argument("--dry-run", action="store_true", help="仅预览，默认行为")
    parser.add_argument("--replace-existing", action="store_true", help="备份并替换发生冲突的受管理文件")
    args = parser.parse_args(argv)
    target = args.target.expanduser().absolute()
    try:
        validate_repository()
        local_path = args.local.expanduser() if args.local is not None else None
        payloads = build_payloads(load_local(local_path))
        if target.resolve().is_relative_to(ROOT.resolve() / "config"):
            raise ConfigError("安装目标不能位于仓库的 config 源目录中。")
        changes = plan_install(target, payloads)
        print(f"目标目录：{target}")
        for change in changes:
            label = "停用 JSONC 并备份" if change.payload.signature is None else {"create": "新增", "unchanged": "无需更改", "update": "更新", "conflict": "冲突"}[change.status]
            print(f"  {label:22} {change.payload.relative}")
        stale = set(load_state(target)["entries"]) - {c.payload.relative for c in changes}
        for name in sorted(stale):
            print(f"  保留旧安装项     {name}")
        conflicts = any(c.status == "conflict" for c in changes)
        if not args.apply:
            print("仅预览，未修改任何文件。")
            if conflicts:
                print("冲突需先迁移，再使用 --apply --replace-existing；不会自动导入旧设置。")
            return 0
        backup = apply_plan(target, changes, args.replace_existing)
        print("安装完成，未受管理的文件和目录已保留。")
        if backup is not None:
            print(f"备份位置：{backup}")
        return 0
    except (ConfigError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
