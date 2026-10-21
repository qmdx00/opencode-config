# 个人工作约定

- 默认使用中文沟通，保留代码、符号和工具的原始名称。先说明结果，解释保持简洁。
- 理解用户的授权范围后持续完成任务。常规实现细节自行判断；只有缺失信息会改变目标、兼容性或重要取舍时才询问。
- 遵循项目已有技术栈和规范。全局文件只提供通用习惯，项目的构建命令、数据约定和运行时版本从项目资料获取。
- 根据改动选择代码检查、相关测试、静态检查和构建；网页交互、布局及视觉效果可通过浏览器验证。明确区分已执行检查与未验证部分。
- 测试范围与改动风险相称。检查通过后不反复扩大验证范围；失败时先定位原因。
- 多步骤或高风险修改可委派独立审查；简单任务直接完成。委派时提供目标、代码范围、约束、已知事实和需要的输出。子会话不应假定拥有父会话上下文。
- 优先并行进行独立的只读调查。多个执行者修改代码时，应明确文件归属或使用独立工作树；不要假定子会话自带文件隔离。
- 不将密钥、OAuth 凭据和本机绝对路径写入共享配置。外部系统变更只在用户授权范围内执行；验证优先使用本地或隔离测试环境。
- 完成时说明改动、验证结果、未验证部分和必要的后续操作，区分计划与已执行结果。

## 按需加载技能

技能存在且与当前任务相关时按需加载，不要一次性加载全部技能：

- `diagram-design` 用于架构图、流程图、时序图和其他有助于表达结构与行为的图。
- `ego-browser` 用于网页操作、截图和浏览器验证；使用前运行 `ego-browser skill` 读取与本机版本匹配的指南。安装、升级应用或导入浏览器数据需用户授权，沿用现有角色权限。安装引导用户使用官方安装包与系统界面，不自动移除隔离标记或绕过系统安全检查。
- 其他工程与工作流技能来自 mattpocock/skills，按当前任务选择；不要自动执行其安装、项目初始化、提交、发布或外部系统操作。
- 技能不能扩大用户授权或角色权限。技能要求写文件、执行命令或委派时，由有相应权限的 developer 承担；只读角色仅返回调查和建议。需要多个执行者时沿用已定义角色，不临时创建越权角色。
- 上游用 `/技能名` 指代技能时，在 OpenCode 通过 `skill` 工具加载对应 ID，或提示用户使用 `@技能名`；不假定同名斜杠命令存在。工具专属步骤应使用当前实际可用的等价工具，不虚构工具或绕过限制。
- 技术栈、业务约束和项目专属流程从项目自身的指令获取，不写入这份通用配置。

缺少技能时先使用项目规范和官方资料继续可以完成的工作，并说明缺少的能力；不要虚构技能或工具。

diagram-design 的绘图产物由 developer 在用户授权的位置创建，architect 提供图的节点、关系和边界。先执行技能的静态校验，需要确认字体、布局或交互时再使用 ego-browser；仅报告实际完成的验证。

配置仓库的 `config/skills/sources.json` 记录启用入口，`config/skills/README.md` 说明添加与升级，`THIRD_PARTY.md` 记录来源与许可。

## 实施与审查原则

以下原则参考 [Ponytail](https://github.com/DietrichGebert/ponytail) 并按个人工作方式调整，不依赖其插件：

- 编码前理解当前行为以及受影响的调用者、测试、配置和导出接口；优先复用项目已有实现，其次使用标准库和已有依赖。
- 只为当前需求引入必要的抽象与配置；保持项目习惯和可读性，不以缩短代码为目标。修复共同根因，并同步修正受影响的调用者。
- 保留校验、错误处理和安全边界。非平凡行为变化通过有意义的检查验证，简单文字或配置调整不强行增加测试。
- 审查先确认预期行为与实际负载，按正确性、安全性、可靠性、性能和复杂度寻找有证据的问题。代码气味只是调查线索，不能单独作为缺陷。
- 头脑风暴可以发散，进入实施前再收敛到当前约束下的方案。

<!-- CODEGRAPH_START -->
## CodeGraph

来源：[colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)。全局 MCP 直接暴露 `codegraph_explore`；查询其他项目时传入对应的 `projectPath`。

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision. If neither interface is available, report that limitation and continue with local inspection.
<!-- CODEGRAPH_END -->
