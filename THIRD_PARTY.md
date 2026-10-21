# 第三方引用与来源

| 项目 | 原始仓库 | 集成方式 | 许可 |
| --- | --- | --- | --- |
| diagram-design | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | Git 子模块，安装单个技能入口 | MIT |
| ego-lite | [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) | Git 子模块，仅安装 ego-browser 技能入口 | MIT（仓库内容） |
| Matt Pocock 技能集 | [mattpocock/skills](https://github.com/mattpocock/skills) | Git 子模块，显式登记技能入口 | MIT |
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | 通用规则中文适配与 `/audit` 命令 | MIT |
| CodeGraph | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | 外部 CLI 与 MCP，不复制源码 | MIT |

运行平台：[OpenCode](https://github.com/anomalyco/opencode)（[V2 文档](https://opencode.ai/v2/docs/)）；模型服务：[OpenAI](https://openai.com/)。

## diagram-design

- 固定提交：[f2f4d49](https://github.com/cathrynlavery/diagram-design/tree/f2f4d49ea8d632f17cf196ba26599277a93f767b)
- 上游入口声明版本：`2.6`。
- 子模块位置：`config/skills/diagram-design`。
- 安装入口：子模块内 `skills/diagram-design`，不安装仓库根目录插件或命令。
- 许可：子模块根目录 `LICENSE`；附加说明见 `THIRD_PARTY_LICENSES.md`。

## ego-lite

- 固定提交：[d392204](https://github.com/citrolabs/ego-lite/tree/d392204d1ea1a8027a591ab2b0129c2e11d85f26)。
- 子模块位置：`config/skills/ego-lite`。
- 安装入口：子模块内 `skills/ego-browser`，不安装上游插件或根目录指令。
- 许可：子模块根目录 `LICENSE`，Copyright (c) 2026 CitroLabs。

MIT 许可覆盖仓库中的技能与运行库，不包含闭源的 ego lite 浏览器应用；应用由各设备单独安装。

## mattpocock/skills

- 固定提交：[5beb35b](https://github.com/mattpocock/skills/tree/5beb35b040e3de97e54fa9e386d7e42d15c295c2)。
- 子模块位置：`config/skills/mattpocock-skills`。
- 安装范围：`skills/engineering` 和 `skills/productivity` 中逐项登记于 `config/skills/sources.json` 的入口。
- 未启用：`deprecated`、`in-progress`、`misc`，以及仓库根目录的 Agent 指令与其他工具配置。
- 许可：子模块根目录 `LICENSE`，Copyright (c) 2026 Matt Pocock。

## Ponytail

- 参考提交：[09c434a](https://github.com/DietrichGebert/ponytail/tree/09c434ab73ca43761c5d8b0c5d341926c2fba710)。
- 参考内容：仓库通用规则，以及 `ponytail`、`ponytail-review`、`ponytail-audit` 的实施与审查原则。
- 适配位置：`config/AGENTS.md`、`config/agents/developer.md`、`architect.md`、`reviewer.md` 和 `config/commands/audit.md`。
- 原始许可：[`licenses/ponytail-LICENSE`](licenses/ponytail-LICENSE)，Copyright (c) 2026 DietrichGebert。

仅适配规则，未安装 Ponytail 插件或会话钩子。

## CodeGraph

- 通过公共 MCP 定义 `codegraph serve --mcp` 接入，直接暴露工具。
- CLI 由各设备独立安装，许可保留在上游发行包中。
- 详细接入与跨设备使用方式见 [`docs/codegraph.md`](docs/codegraph.md)。

## 维护约定

升级第三方来源时核对固定提交与许可，更新本文件；具体步骤见[技能维护说明](config/skills/README.md#主动升级)。
