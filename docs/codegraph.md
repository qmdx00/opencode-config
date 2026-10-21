# CodeGraph 接入说明

上游仓库：[colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)。CodeGraph 提供本地符号索引、调用路径和影响范围调查；它作为外部程序与 MCP 工具接入，不复制源码到技能目录。

## 每台设备的准备

按上游说明安装 CodeGraph CLI，并让启动 OpenCode 的进程能够从 `PATH` 找到 `codegraph`。本次核对的设备已有 `1.6.1`，没有替换或升级程序；其他设备可使用相同版本以减少行为差异。

使用 Node.js 安装时可显式指定版本：

```bash
npm install --global @colbymchenry/codegraph@1.6.1
codegraph version
codegraph serve --help
```

也可使用上游仓库提供的独立安装包。CLI 版本与本配置的 Git 子模块版本分别管理。安装器不会自动下载程序或修改系统 `PATH`；图形界面启动的 OpenCode 若找不到命令，可在本机覆盖中填写可执行文件的真实绝对路径，保留完整参数。

本仓库已管理 OpenCode 的 MCP 定义和指令，不再运行 `codegraph install` 来重复改写同一份全局配置。上游安装命令输出的片段可能面向其他 OpenCode 版本，应以本仓库的 V2 字段为准。

## 公共配置

```json
{
  "mcp": {
    "servers": {
      "codegraph": {
        "type": "local",
        "command": ["codegraph", "serve", "--mcp"],
        "codemode": false
      }
    }
  }
}
```

`codemode: false` 让工具直接暴露，便于只读角色使用。`architect`、`reviewer`、`brainstorm` 只放行 `codegraph_codegraph_explore`，不会因此开放其他 MCP 工具或 Code Mode。该调用是读取接口，服务自身仍可能自动维护已有索引。

这里没有固定工作目录或项目路径。查询其他仓库时向 `codegraph_explore` 传入其 `projectPath`；不会把某台设备的工作区路径同步给其他设备。

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

全局连接不意味着自动给所有项目创建索引。需要启用时由用户在相应项目中执行：

```bash
codegraph init
codegraph status
codegraph explore "相关符号或需要理解的问题"
```

已有 `.codegraph/` 时，Agent 在定位和理解代码前优先使用 CodeGraph；没有时继续使用常规文件读取与搜索。Agent 不主动执行初始化、升级或清理索引。

各设备独立建立项目索引，不同步数据库、后台服务状态或本机路径；将项目的 `.codegraph/` 作为本地副产物处理。本配置仓库已忽略该目录，但没有为验证而创建索引。

## 验证

本仓库检查确认 MCP 定义、合并结果与角色权限；不启动真实 OpenCode 会话。应用配置后，在 OpenCode 中查看 `/mcps`，确认 `codegraph` 已连接，再在已有索引的项目中发起一次符号查询。连接或索引失败时按上游排障说明处理，不把失败当作不存在相关代码。

配置字段依据：[OpenCode MCP 文档](https://opencode.ai/v2/docs/mcp-servers/)与[权限文档](https://opencode.ai/v2/docs/permissions/)。
