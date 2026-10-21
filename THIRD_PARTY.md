# 第三方引用与来源

本文件统一登记引用的项目、原始仓库、集成方式及许可。第三方子模块保留上游原文，自编说明使用中文。

| 项目 | 原始仓库 | 集成方式 | 许可 |
| --- | --- | --- | --- |
| diagram-design | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | Git 子模块，安装单个技能入口 | MIT |
| Matt Pocock 技能集 | [mattpocock/skills](https://github.com/mattpocock/skills) | Git 子模块，显式登记技能入口 | MIT |
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | 通用规则中文适配与 `/audit` 命令 | MIT |
| CodeGraph | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | 外部 CLI 与 MCP，不复制源码 | MIT |

OpenCode 是本配置的运行平台：[anomalyco/opencode](https://github.com/anomalyco/opencode)，配置依据为 [V2 官方文档](https://opencode.ai/v2/docs/)。模型与订阅来自 [OpenAI](https://openai.com/)，请求参数依据官方文档，不纳入第三方源码。

## diagram-design

- 固定提交：[f2f4d49](https://github.com/cathrynlavery/diagram-design/tree/f2f4d49ea8d632f17cf196ba26599277a93f767b)
- 上游入口声明版本：`2.6`。
- 子模块位置：`config/skills/diagram-design`。
- 安装入口：子模块内 `skills/diagram-design`，不安装仓库根目录插件或命令。
- 许可：子模块根目录 `LICENSE`；附加说明见 `THIRD_PARTY_LICENSES.md`。

上游运行资源原样保留。浏览器验证等个人约束在父仓库中说明，不改写上游技能。

## mattpocock/skills

- 固定提交：[5beb35b](https://github.com/mattpocock/skills/tree/5beb35b040e3de97e54fa9e386d7e42d15c295c2)。
- 子模块位置：`config/skills/mattpocock-skills`。
- 安装范围：`skills/engineering` 的 20 个入口和 `skills/productivity` 的 7 个入口，逐项登记于 `config/skills/sources.json`。
- 未启用：`deprecated`、`in-progress`、`misc`，以及仓库根目录的 Agent 指令与其他工具配置。
- 许可：子模块根目录 `LICENSE`，Copyright (c) 2026 Matt Pocock。

保留上游文件和显式调用标记；个人授权、验证偏好及角色权限由父仓库说明约束，不运行项目初始化或发布流程。

## Ponytail

- 参考提交：[09c434a](https://github.com/DietrichGebert/ponytail/tree/09c434ab73ca43761c5d8b0c5d341926c2fba710)。
- 参考内容：仓库通用规则，以及 `ponytail`、`ponytail-review`、`ponytail-audit` 的实施与审查原则。
- 适配位置：`config/AGENTS.md`、`config/agents/developer.md`、`architect.md`、`reviewer.md` 和 `config/commands/audit.md`。
- 原始许可：[`licenses/ponytail-LICENSE`](licenses/ponytail-LICENSE)，Copyright (c) 2026 DietrichGebert。

这是按现有中文工作流进行的规则适配，没有安装其插件、技能集、全局模式状态或会话钩子。保留原许可及版权声明，不沿用特定工具或模型的效果承诺。

## CodeGraph

- 通过公共 MCP 定义 `codegraph serve --mcp` 接入，直接暴露工具。
- 本次核对的本机版本：`1.6.1`；未自动升级或修改现有安装。
- 使用规则：已有项目索引时优先调查符号与调用路径；初始化、升级及删除索引由用户决定。
- 没有复制程序或索引；CLI 由各设备独立安装，许可保留在上游发行包中。
- 详细接入与跨设备使用方式见 [`docs/codegraph.md`](docs/codegraph.md)。

## 维护约定

子模块提交由父仓库记录固定，正常同步执行 `git submodule update --init --recursive`。主动升级时检查新提交、许可和资源变化，更新本文件，再运行结构检查并在临时目录验证安装。缓存、依赖、索引和验证产物不作为引用内容提交。
