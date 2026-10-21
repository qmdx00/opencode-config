#!/usr/bin/env python3
"""检查配置源、本机覆盖与安装结果，不请求模型或外部服务。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config_lib import (
    ConfigError, build_payloads, default_local, default_target, load_local,
    plan_install, registered_skills, validate_repository,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, help="同时检查指定的本机覆盖文件")
    parser.add_argument("--installed", action="store_true", help="对比目标目录中的受管理文件")
    parser.add_argument("--target", type=Path, default=default_target())
    args = parser.parse_args(argv)
    try:
        validate_repository()
        # 仓库检查保持可复现，不隐式读取本机覆盖。
        local = load_local(args.local.expanduser()) if args.local is not None else {}
        if args.installed and args.local is None and default_local().exists():
            local = load_local(None)
        payloads = build_payloads(local)
        if args.installed:
            changes = plan_install(args.target.expanduser().absolute(), payloads)
            mismatched = [c for c in changes if c.status != "unchanged"]
            if mismatched:
                for change in mismatched:
                    print(f"安装结果与计划不符：{change.payload.relative}", file=sys.stderr)
                return 1
        print("通过：JSON 结构、V2 字段、角色与命令引用、Skill 元数据和配置源可移植性检查。")
        print(f"已登记 {len(registered_skills())} 个 Skill，仅安装其入口目录。")
        if args.installed:
            print("通过：受管理的安装文件与仓库及所选本机覆盖一致。")
        print("本检查离线运行；完整官方 Schema 和实时模型/Fast 可用性需要分别验证。")
        return 0
    except (ConfigError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
