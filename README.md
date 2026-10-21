# 个人 OpenCode 全局配置

用于开发、架构设计、代码审查和头脑风暴。项目规则写在各项目的 `AGENTS.md` 中。

## 开始使用

需要 Python 3.10+ 和符号链接支持。适用于 macOS/Linux，Windows 未验证。

首次克隆使用 `git clone --recurse-submodules --shallow-submodules <本仓库地址>`。已有仓库执行：

```bash
git submodule update --init --recursive --depth 1
python3 scripts/check.py
python3 scripts/install.py --dry-run
```

确认预览无冲突后安装：

```bash
python3 scripts/install.py --apply
python3 scripts/check.py --installed
```

已有全局配置时，先按[迁移说明](docs/setup.md#迁移已有全局配置)保留必要设置，再使用 `--replace-existing`。

每台设备需[安装或禁用 CodeGraph](docs/codegraph.md)；浏览器操作需[准备 ego lite](docs/skills.md#浏览器)，代理设置见[本机代理](docs/setup.md#本机代理)。安装后用 `/connect` 登录 OpenAI、`/models` 核对模型与变体，再新建会话。

## 日常使用

| 命令 | 角色 | 用途 |
| --- | --- | --- |
| `/dev` | developer | 实施、调试和验证 |
| `/design` | architect | 只读调查与方案设计 |
| `/review` | reviewer，后台子会话 | 只读审查变更 |
| `/audit` | reviewer，后台子会话 | 只读审计指定范围或代码库 |
| `/brainstorm` | brainstorm | 探索方向与最小实验，不执行 |
| `/diagram` | developer | 根据代码或确认方案绘图 |

命令后附任务描述。

技能按需加载，不自动成为同名命令；使用方式见[技能说明](docs/skills.md)。

## 修改哪里

| 内容 | 维护位置 |
| --- | --- |
| 模型、角色权限、MCP | [`config/opencode.json`](config/opencode.json) |
| 终端设置 | [`config/cli.json`](config/cli.json) |
| 通用工作约定 | [`config/AGENTS.md`](config/AGENTS.md) |
| 角色职责与命令模板 | [`config/agents/`](config/agents/)、[`config/commands/`](config/commands/) |
| 技能启用清单 | [`config/skills/sources.json`](config/skills/sources.json)；[登记方法](config/skills/README.md) |
| 设备差异 | 仓库外的 `local.json`，见[本机覆盖](docs/setup.md#先准备本机覆盖) |

默认角色为 developer，内置 build 和 plan 已禁用。第三方来源、版本与许可见 [`THIRD_PARTY.md`](THIRD_PARTY.md)。

## 维护与跨设备同步

```bash
git pull --no-recurse-submodules
git submodule update --init --recursive --depth 1
python3 scripts/check.py
python3 scripts/install.py --dry-run
python3 scripts/install.py --apply
```

指令、角色、命令和技能使用符号链接，修改链接内容会修改仓库源文件；JSON 修改或仓库移动后需重新安装。子模块升级见[维护说明](config/skills/README.md#主动升级)，日常同步不使用 `update --remote`。

上述命令限制子模块克隆与补取提交的深度，不拉取完整历史。已下载的历史不会因这些选项自动清除。

## 本地验证

```bash
python3 scripts/check.py
git diff --check
```

检查覆盖配置结构、角色与命令引用、技能元数据和可移植性，不等同于完整 Schema 或实时模型、Fast、MCP 验证。修改安装器时使用[隔离目录验证](docs/setup.md#在隔离目录测试)。
