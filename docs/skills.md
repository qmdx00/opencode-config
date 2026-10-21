# 技能使用说明

当前技能来自 [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) 和 [mattpocock/skills](https://github.com/mattpocock/skills)，以固定提交的 Git 子模块保存。完整列表、入口及添加方法见 [`config/skills/README.md`](../config/skills/README.md)，许可与版本见 [`THIRD_PARTY.md`](../THIRD_PARTY.md)。

## 按需使用

OpenCode 通过 `skill` 工具按 ID 加载正文，不会把所有技能全文加入每次对话。可以在提示中明确指定：

```text
@diagram-design 根据当前模块绘制架构图
@diagnosing-bugs 调查这个间歇性失败的根因
@to-spec 把已确认的需求整理为实施规格
@tdd 为这项行为变化设计测试并实现
@handoff 整理当前工作进度、证据与待办
```

上游标记 `disable-model-invocation: true` 的技能保留该设置，应由用户显式指定。技能入口不会自动变成同名斜杠命令；本仓库的 `/dev`、`/design`、`/review`、`/audit` 等命令独立维护。依据：[OpenCode 技能文档](https://opencode.ai/v2/docs/skills/)。

上游正文中的 `/技能名` 应按技能 ID 通过 `skill` 工具加载，或改用 `@技能名` 显式指定；其他工具专属的提问与委派接口使用 OpenCode 当前可用的等价能力。

工作流技能可能要求初始化项目约定、操作问题跟踪系统、提交或发布，也可能要求并行 Agent 和浏览器。安装技能不意味着授权这些动作：沿用用户当前任务范围、项目规则和角色权限；保持中文沟通与禁止浏览器验证的个人约定。只读角色不能借助技能绕过编辑、执行或委派限制，需要实施时交给 developer。

`setup-matt-pocock-skills` 仅在用户明确要求时对具体项目使用，不自动为所有仓库设置问题跟踪系统、标签或文档路径。`code-review` 的上游完整流程需要并行调查，可由 developer 协调已有角色；只需要独立只读审查时使用 `/review`。不为适配技能而扩大 reviewer 的权限。

## 绘图

diagram-design 的实际技能入口位于 `config/skills/diagram-design/skills/diagram-design/`。安装后 `~/.config/opencode/skills/diagram-design` 直接链接到该入口，包含类型参考、模板与静态检查脚本。

当图比文字或表格更清楚时使用，例如架构图、流程图、时序图、数据流图、状态机、部署图和依赖图。先确定表达目标、读者和关键关系，再选择图类型。

```text
/diagram 绘制当前模块的架构图，突出边界与外部依赖
/diagram 将已确认的处理流程绘成流程图
/diagram 根据当前调用链绘制请求时序图
```

`/diagram` 使用 developer 创建产物。`/design` 使用只读 architect，提供图的结构与说明；需要输出文件时再交给 developer。

1. 从实际代码、资料或已确认方案中提取节点、关系和边界，区分事实与假设。
2. 按上游入口选择图类型并读取对应参考，不加载全部类型说明。
3. 沿用项目输出目录与风格。上游可能要求首次确认风格，没有既定选择时按其流程确认，不修改共享技能的样式文件。
4. 默认生成自包含 HTML，保留可编辑 SVG；需要其他格式时再导出，不自动安装浏览器或运行浏览器导出。
5. 使用技能附带的本地检查脚本；静态通过不代表实际字体、布局或交互经过视觉验证。

在安装后的技能目录中运行：

```bash
python3 scripts/self_check.py /绝对路径/设计图.html
```

只有技能入口下的资源被安装，上游仓库根目录的维护工具不属于全局技能路径。上游涉及浏览器字体测量、截图与视觉检查时遵循个人验证约束，并明确未验证部分。

## Ponytail 原则与审计

[Ponytail](https://github.com/DietrichGebert/ponytail) 的通用原则已中文适配到全局指令与 developer、architect、reviewer：先理解行为与调用者，优先复用，控制复杂度，按证据审查。这里不安装 Ponytail 插件或额外同名技能，也不依赖其激活状态与会话钩子。

`/review` 检查当前改动；`/audit` 调查指定范围或整个仓库的入口、数据流与跨模块风险。二者都交给只读 reviewer，按严重程度报告有触发条件的问题，并说明未深入范围。规则来源与原始许可保存在 `THIRD_PARTY.md` 和 `licenses/ponytail-LICENSE`。

## 同步与更新

拉取父仓库后运行 `git submodule update --init --recursive`，再检查和预览安装。安装器只链接 `sources.json` 中登记的入口，不自动启用上游新增技能；既有其他全局技能不被删除。同名入口冲突时停止，明确替换会先备份。

主动升级需选择新提交、检查许可和资源变化、更新来源记录，再运行本仓库检查及相关技能检查。不要在子模块中保存个人修改；个人使用约定维护在父仓库。
