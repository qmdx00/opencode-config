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

## 浏览器

`ego-browser` 支持网页操作、截图和浏览器验证。每台设备从 [ego lite 官网](https://lite.ego.app/)下载安装包，通过系统界面安装并完成首次设置，确保 OpenCode 后台服务的 `PATH` 能找到 CLI：

```bash
command -v ego-browser
ego-browser skill
```

使用示例：`@ego-browser 验证本地页面的表单交互并截图`。操作前读取 `ego-browser skill` 输出的版本匹配指南；缺少 CLI 时先征得安装授权。

浏览器应用、登录状态和个人数据不随仓库同步。已有同名技能时，先预览安装冲突，核对后再使用 `--replace-existing`。浏览器操作由 developer 执行，其他角色保留现有权限；付款、发布、删除及表单提交等外部变更须在任务授权范围内。

## 绘图

```text
/diagram 绘制当前模块的架构图，突出边界与外部依赖
```

`/diagram` 使用 developer 创建产物。`/design` 使用只读 architect，提供图的结构与说明；需要输出文件时再交给 developer。

在全局配置的 `skills/diagram-design` 目录中运行静态检查：

```bash
python3 scripts/self_check.py /绝对路径/设计图.html
```

静态检查不验证实际字体和显示效果，需要时再通过 ego-browser 验证。
