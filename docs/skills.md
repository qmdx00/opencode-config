# 技能使用说明

启用清单见 [`sources.json`](../config/skills/sources.json)，添加与升级见[维护说明](../config/skills/README.md)。

## 按需使用

在提示中用 `@技能名` 指定技能：

```text
@diagram-design 根据当前模块绘制架构图
@diagnosing-bugs 调查这个间歇性失败的根因
@to-spec 把已确认的需求整理为实施规格
@tdd 为这项行为变化设计测试并实现
@handoff 整理当前工作进度、证据与待办
```

标记 `disable-model-invocation: true` 的技能需要显式指定。技能名不是斜杠命令；Agent 按 ID 通过 `skill` 工具加载，遇到上游 `/技能名` 写法时也按此处理。参考：[OpenCode 技能文档](https://opencode.ai/v2/docs/skills/)。

`setup-matt-pocock-skills` 只在明确要求时运行。`code-review` 的并行审查流程由 developer 协调；只需独立审查时用 `/review`。

## 绘图

```text
/diagram 绘制当前模块的架构图，突出边界与外部依赖
```

`/diagram` 使用 developer 创建产物。`/design` 使用只读 architect，提供图的结构与说明；需要输出文件时再交给 developer。

在全局配置的 `skills/diagram-design` 目录中运行静态检查：

```bash
python3 scripts/self_check.py /绝对路径/设计图.html
```

静态检查不验证实际字体和显示效果；授权与验证约束遵循通用指令。
