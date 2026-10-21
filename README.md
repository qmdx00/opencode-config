# 个人 OpenCode 全局配置

面向通用代码开发、架构设计、代码审查和头脑风暴。配置不预设业务领域或技术栈，项目规则由各项目自己的 `AGENTS.md` 提供。

## 角色与模型

| 角色 | 模式 | 模型与推理强度 | 用途 |
| --- | --- | --- | --- |
| `developer` | 主会话 | GPT-6.1 Sol · medium | 开发、调试、验证和协调 |
| `architect` | 主会话或子会话 | GPT-6 Astra · high | 架构调查、技术取舍和实施规划 |
| `reviewer` | 主会话或子会话 | GPT-6.1 Sol · high | 独立审查与回归检查 |
| `brainstorm` | 主会话 | GPT-6.1 Sol · medium | 需求探索、方向比较与最小实验 |
| 内置 `explore` | 子会话 | GPT-6 Luna · high | 代码定位和资料梳理 |

OpenAI Fast 模式请求统一指定 `service_tier: "priority"`，使用兼容订阅通道的参数值。模型与权限集中维护在 [`config/opencode.json`](config/opencode.json)，各角色的提示词位于 [`config/agents/`](config/agents/)。配置表达请求意图，实际服务档位仍需在首次使用时确认。

架构与头脑风暴角色不修改文件；需要生成文档或图文件时切换到开发角色。审查角色不能直接编辑代码，运行额外 Shell 检查需确认。权限规则是工具访问控制，Shell 不是文件系统沙箱。

## 开始使用

需要 Python 3.10 及以上版本。安装与本地检查只依赖标准库，默认面向支持符号链接的 macOS/Linux；Windows 需要能创建符号链接，尚未验证。

首次克隆使用 `git clone --recurse-submodules <本仓库地址>`。已有仓库先初始化固定版本的技能来源：

```bash
git submodule update --init --recursive
```

CodeGraph 需要每台设备自行安装并放入 OpenCode 可见的 `PATH`，准备方法见 [CodeGraph 接入说明](docs/codegraph.md)。

需要代理时，按[本机代理配置](docs/setup.md#本机代理)为 OpenCode 后台服务设置代理地址和本地连接排除项。代理设置属于设备差异，单独保存在本机服务配置中；安装公共 JSON 不会覆盖它。

先检查并预览，以下两条命令都不修改全局配置：

```bash
python3 scripts/check.py
python3 scripts/install.py --dry-run
```

目标为空时，可应用安装：

```bash
python3 scripts/install.py --apply
python3 scripts/check.py --installed
```

已有全局配置时，先按[安装与迁移说明](docs/setup.md)保留本机设置，再决定是否使用 `--replace-existing`。本机覆盖文件默认位于 `~/.config/opencode-config/local.json`；`XDG_CONFIG_HOME` 可改变配置根目录。

安装后在 OpenCode 中执行 `/connect`，选择 OpenAI 并使用订阅登录，再用 `/models` 核对模型与变体。认证信息保留在每台设备，仓库不保存凭据。新建会话使用新的默认角色。

## 常用命令

```text
/dev 修复当前模块的错误处理
/design 比较任务调度模块的两个实现方案
/review 检查当前未提交的修改
/audit 审计当前仓库的入口、数据流与错误处理
/brainstorm 探索这项需求的几种实现方向
/diagram 根据已确认的方案绘制架构图
```

`/review` 和 `/audit` 在后台 reviewer 子会话运行，其余命令在当前会话切换角色。子会话需要完整任务说明，不应假定继承父会话上下文或获得独立工作树。

## 引用与集成

| 名称与上游仓库 | 用途 | 集成方式 |
| --- | --- | --- |
| [diagram-design](https://github.com/cathrynlavery/diagram-design) | 架构图、流程图、时序图等 | Git 子模块，仅链接技能入口 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 工程实践、需求探索、研究与交接 | Git 子模块，登记工程与工作流目录中的 27 个技能 |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | 简洁实现、基于证据的审查与仓库审计 | 中文适配进现有角色，增加 `/audit` |
| [CodeGraph](https://github.com/colbymchenry/codegraph) | 符号、调用链与改动影响调查 | 全局 MCP 接入，按项目启用索引 |

技能来源与添加方法统一放在 [`config/skills/README.md`](config/skills/README.md)，启用清单为 [`sources.json`](config/skills/sources.json)。当前共 28 个 Skill，按需加载；上游的插件、根目录指令、废弃和开发中技能不安装。现有全局目录中的其他 Skill 不会被清理。

中文使用说明见 [`docs/skills.md`](docs/skills.md)，所有第三方内容的来源、版本和许可见 [`THIRD_PARTY.md`](THIRD_PARTY.md)。

## 维护与跨设备同步

```bash
git pull
git submodule update --init --recursive
python3 scripts/check.py
python3 scripts/install.py --dry-run
python3 scripts/install.py --apply
```

每台设备自行维护 MCP 地址、路径等差异。安装器递归合并公共 JSON 与本机覆盖，数组整体替换；它与 OpenCode 自身的多层配置合并是两个过程。

生成的 `opencode.json`、`cli.json` 是普通文件；指令、Agent、命令和 Skill 按项建立符号链接。保留仓库在本机的位置；移动仓库后重新运行安装。通过链接修改全局提示词也会修改仓库源文件。

子模块版本由父仓库中的提交记录固定。正常同步不使用 `git submodule update --remote`；仅在主动升级并审查上游变化时更新版本。CodeGraph 程序和项目索引留在各设备，不随配置仓库同步。

## 本地验证

```bash
python3 scripts/check.py
git diff --check
```

仓库保留 Python 安装与检查脚本，不维护独立测试目录。默认检查核对 JSON 结构、角色与命令引用、Skill 元数据和配置源可移植性，不等同于完整官方 Schema 验证，不请求模型或 MCP，也不进行浏览器验证。安装行为可按[隔离目录验证步骤](docs/setup.md#在隔离目录测试)检查。

子模块未初始化时，`check.py` 与安装器会停止并提示初始化，完成下载后再运行检查。

临时依赖、缓存、日志、本机覆盖和安装副产物均在 `.gitignore` 中忽略。开发时使用的 `work/` 可以删除，不属于运行配置。
