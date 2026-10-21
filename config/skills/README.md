# 技能来源与启用清单

本目录保存第三方技能的 Git 子模块与显式启用清单。上游资源保留原文，中文使用约定放在父仓库；不把上游插件、根目录 `AGENTS.md` 或其他工具配置加载到个人全局指令。

| 来源目录 | 原始仓库 | 用途 | 安装入口 |
| --- | --- | --- | --- |
| `diagram-design/` | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | 架构、流程、时序和其他设计图 | `skills/diagram-design` |
| `mattpocock-skills/` | [mattpocock/skills](https://github.com/mattpocock/skills) | 工程实践与通用工作流程 | `skills/engineering/*`、`skills/productivity/*` 中登记的入口 |

固定版本及许可见根目录 [THIRD_PARTY.md](../../THIRD_PARTY.md)。Ponytail 以规则适配方式接入，CodeGraph 以 MCP 接入，二者不作为此目录的 Skill 安装。

## 已登记技能

安装器读取 [sources.json](sources.json)，逐项链接到全局配置的 `skills/<技能名>`。目录通配符只用于说明，实际安装严格使用清单中的完整路径。

| 技能 | 用途 |
| --- | --- |
| `diagram-design` | 设计图绘制与本地静态检查 |
| `ask-matt` | 根据当前情况选择技能和工作流程 |
| `code-review` | 按规范和需求审查代码 |
| `codebase-design` | 探索代码库设计与模块职责 |
| `diagnosing-bugs` | 调查缺陷并缩小根因范围 |
| `domain-modeling` | 梳理领域概念、数据和不变量 |
| `grill-with-docs` | 结合文档澄清方案和约束 |
| `implement-spec` | 根据既有规格实施 |
| `implement` | 执行开发任务 |
| `improve-codebase-architecture` | 识别并改进架构边界 |
| `pr` | 编写拉取请求说明 |
| `prototype` | 通过最小原型验证想法 |
| `research` | 针对问题开展调查与研究 |
| `retro` | 回顾工作过程并提炼改进 |
| `setup-matt-pocock-skills` | 按项目配置该技能集的工作流约定 |
| `tdd` | 以行为验证推动实现 |
| `to-spec` | 将讨论整理为可实施规格 |
| `to-tickets` | 拆分工作项与依赖 |
| `triage` | 分析问题并安排下一步 |
| `wayfinder` | 识别当前工作流所处阶段和下一步 |
| `wizard` | 为必须由人操作的步骤生成交互式引导 |
| `grill-me` | 通过深入提问完善想法 |
| `grilling` | 结构化澄清需求与重要取舍 |
| `handoff` | 整理工作交接上下文 |
| `teach` | 针对概念或代码进行讲解 |
| `to-questionnaire` | 将待确认事项整理为问卷 |
| `wait-what` | 重新澄清疑问与分歧 |
| `writing-for-agents` | 编写供 Agent 使用的清晰资料 |

上游的 `deprecated`、`in-progress` 和 `misc` 目录未启用。工作流技能按需调用，具体步骤以固定提交中的 `SKILL.md` 为准；使用方式见 [中文说明](../../docs/skills.md)。

## 初始化与同步

```bash
git submodule update --init --recursive
python3 scripts/check.py
```

从父仓库根目录执行。首次克隆也可用 `git clone --recurse-submodules <本仓库地址>`。子模块未初始化时检查与安装会停止并提示初始化，不悄悄跳过技能。

## 添加其他来源

1. 先审查仓库用途、技能入口和许可，选择固定提交。
2. 使用来源名称作为子模块名称和目录名称，例如：

   ```bash
   git submodule add --name example-skills https://github.com/作者/仓库.git config/skills/example-skills
   git -C config/skills/example-skills checkout --detach <固定提交>
   ```

3. 在 `sources.json` 增加同名对象，填写 `repository`、中文 `description` 和 `skills` 映射；映射键为入口中的 `name`，值为相对子模块根目录的技能目录。每个目录必须含 `SKILL.md`，名称不得与其他来源重复。
4. 在本文件登记用途和原始仓库，在根目录 `THIRD_PARTY.md` 记录提交与许可。保留子模块中的上游许可证，不直接改写上游文件。
5. 运行结构检查，并用临时目标预览和验证新增链接。提交父仓库时同时包含 `.gitmodules`、子模块提交记录、清单及说明。

## 主动升级

进入对应子模块获取上游更新，明确选择新提交，再回到父仓库检查差异、更新来源记录并测试。常规同步使用父仓库固定的提交，不运行 `update --remote`。上游新增技能不会自动启用，仍需修改清单。
