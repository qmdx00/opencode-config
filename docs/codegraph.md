# CodeGraph 接入说明

CodeGraph 用于查询符号、调用链和影响范围。上游：[colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)。

## 每台设备的准备

安装 CLI，并确保 OpenCode 后台服务的 `PATH` 能找到 `codegraph`。例如：

```bash
npm install --global @colbymchenry/codegraph@1.6.1
codegraph version
codegraph serve --help
```

若找不到命令，在本机覆盖中将 `command` 的首项改为可执行文件的绝对路径，保留其余参数。

不要运行 `codegraph install`，以免重复改写本仓库管理的全局配置。

## 公共配置

MCP 定义见 [`config/opencode.json`](../config/opencode.json) 的 `mcp.servers.codegraph`。`codemode: false` 让工具直接暴露，只读角色仅放行 `codegraph_codegraph_explore`；服务可能自动维护已有索引。

查询其他仓库时，向 `codegraph_explore` 传入 `projectPath`。

未安装程序或暂时不用时，可以在本机覆盖中禁用：

```json
{
  "opencode": {
    "mcp": { "servers": { "codegraph": { "disabled": true } } }
  },
  "cli": {}
}
```

这里使用的是本仓库安装器的递归合并；若直接在 OpenCode 的项目配置中覆盖同名服务，需要按 V2 规则填写完整服务对象。

## 每个项目的索引

在需要索引的项目中执行：

```bash
codegraph init
codegraph status
codegraph explore "相关符号或需要理解的问题"
```

已有 `.codegraph/` 时，Agent 在定位和理解代码前优先使用 CodeGraph；没有时继续使用常规文件读取与搜索。Agent 不主动执行初始化、升级或清理索引。

索引由各设备独立建立，不同步 `.codegraph/`。

## 验证

在 `/mcps` 确认已连接，再对已有索引的项目查询一次符号。连接或索引报错时先排障，不将失败视为无相关代码。

配置字段依据：[OpenCode MCP 文档](https://opencode.ai/v2/docs/mcp-servers/)与[权限文档](https://opencode.ai/v2/docs/permissions/)。
