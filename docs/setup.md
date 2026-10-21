# 安装、迁移与恢复

## 管理范围

安装器只管理以下路径，默认仅预览：

| 目标 | 安装方式 |
| --- | --- |
| `opencode.json` | 公共配置与本机覆盖合并后生成，权限为仅当前用户读写 |
| `cli.json` | 公共终端设置与本机覆盖合并后生成 |
| `AGENTS.md` | 链接到仓库中的个人通用指令 |
| `agents/*.md` | 按文件链接，不替换整个目录 |
| `commands/*.md` | 按文件链接，不替换整个目录 |
| `skills/<技能名>` | 按 `config/skills/sources.json` 链接固定版本的技能入口目录 |

服务状态、数据库、OAuth 凭据、插件依赖和其他未管理文件原样保留。不自动更新、提交或推送 Git，不连接模型或 MCP 服务。

## 本机代理

OpenCode 的请求由后台服务发出。系统代理已启用，或当前终端设置了代理，都不能证明已有后台进程已经使用它。需要代理访问模型服务时，显式保存后台服务的代理环境。

以下以本地 HTTP/混合代理端口 `1086` 为例，先启动代理程序；其他设备按实际端口调整：

```bash
opencode service set env HTTP_PROXY http://127.0.0.1:1086
opencode service set env HTTPS_PROXY http://127.0.0.1:1086
opencode service set env NO_PROXY localhost,127.0.0.1,::1
opencode service start
opencode api GET /api/info
```

两个代理变量的地址都使用 `http://`；`HTTPS_PROXY` 表示 HTTPS 目标经此代理转发，不要求代理地址本身使用 HTTPS。`NO_PROXY` 让 CLI 与后台服务之间的本地连接直接通信。每次修改服务环境会停止已有服务，最后用 `service start` 重新启动。

健康检查通过只代表 CLI 能连接本地服务；再登录模型服务并发送一个简短请求，才能验证服务的出站代理和模型访问权限。模型参数兼容性仍需单独核对。

如果只在当前终端使用临时代理，可执行：

```bash
export HTTP_PROXY=http://127.0.0.1:1086
export HTTPS_PROXY=http://127.0.0.1:1086
export NO_PROXY=localhost,127.0.0.1,::1
opencode --standalone
```

这会运行独立服务，使用当前终端环境。已有共享后台服务不会因终端中的 `export` 自动更新；日常使用优先采用上面的持久设置。

关闭持久代理：

```bash
opencode service unset env HTTP_PROXY
opencode service unset env HTTPS_PROXY
opencode service unset env NO_PROXY
opencode service start
```

这些设置由各设备单独维护。不要将带账号密码的代理 URL 写入共享仓库或分享完整服务环境输出。配置依据：[OpenCode 网络与代理文档](https://opencode.ai/v2/docs/network/)。

## 先准备本机覆盖

公共配置内置不含路径和凭据的 CodeGraph MCP 定义，其他本机 MCP、绝对路径和凭据放在仓库外的本机配置目录。需要时复制示例：

```bash
mkdir -p ~/.config/opencode-config
cp examples/local.example.json ~/.config/opencode-config/local.json
```

如果设置了 `XDG_CONFIG_HOME`，请改用该目录下的 `opencode-config/local.json`，也可通过 `--local` 显式指定文件。

示例仅包含空的本机覆盖分区，不预设额外 MCP 服务。公共 CodeGraph 已启用，命令需要本机已安装相应程序；安装及禁用方式见 [CodeGraph 接入说明](codegraph.md)。添加其他服务时，地址与认证方式应以本机实际服务为准。

只需要公共配置时不创建本机覆盖文件即可；也可以使用最小文件：

```json
{
  "opencode": {},
  "cli": {}
}
```

本机覆盖由安装器读取，OpenCode 不会自动发现名为 `local.json` 的额外配置。对象递归合并，数组和标量整体替换；例如覆盖 `permissions` 数组意味着替换该层的整个数组，应保留仍需要的规则。

凭据优先通过 OpenCode 登录保存，或在 JSON 中使用 `{env:变量名}`。不要把真实密钥写进版本控制，也不要分享含认证信息的生成配置和备份。

## 迁移已有全局配置

首次安装不会自动导入已有 `opencode.json` 或 `opencode.jsonc`。先将仍需要的设置整理进本机覆盖文件，再预览替换。

迁移时关注：

- MCP 服务统一放进 `opencode.mcp.servers`，避免同一服务同时存在新旧定义。
- 原来的 `enabled: true` 对应 `disabled: false`；OAuth 字段使用 V2 的下划线命名。
- 只保留每个 MCP 服务的一份完整配置；服务命令、地址和请求头来自本机现有有效配置。
- 终端个性化设置放进本机文件的 `cli` 分区。
- 个人通用指令在 `config/AGENTS.md` 中维护，仓库维护规范在根目录 `AGENTS.md` 中维护。
- 技能按来源登记并逐项安装；其他现存 Skill 不会被清理。拉取本仓库后先执行 `git submodule update --init --recursive`。

检查和预览：

```bash
python3 scripts/check.py --local ~/.config/opencode-config/local.json
python3 scripts/install.py --local ~/.config/opencode-config/local.json --dry-run
```

确认旧设置已经迁移后，显式允许备份替换：

```bash
python3 scripts/install.py --local ~/.config/opencode-config/local.json --apply --replace-existing
python3 scripts/check.py --installed --local ~/.config/opencode-config/local.json
```

若目标同时有 `opencode.jsonc`，安装器将它列为冲突，在明确替换时移入备份，避免 JSON 与 JSONC 同时参与加载。脚本不会解析 JSONC 或自动转换其中的内容，迁移应在替换前完成。

如果父目录（例如 `agents/`）本身是符号链接，安装器会停止，防止沿链接修改另一处目录；请先整理为真实目录。单个受管理文件或 Skill 目录的旧链接可在明确替换时备份。

## 安装结果与后续更新

目标目录内的 `.opencode-config-state.json` 记录上次安装的文件指纹，不记录凭据值。后续运行可以更新仍与记录一致的生成文件；如果你手动改过生成文件，则作为冲突停止，不悄悄覆盖。

提示词和 Skill 使用链接，仓库内容更新会直接体现在链接目标上；JSON 修改则需要重新运行安装器。建议新建 OpenCode 会话应用新的默认 Agent 和指令。

本仓库的 `architect`、`reviewer`、`brainstorm` 使用权限白名单，Code Mode 关闭；明确允许直接调用 `codegraph_codegraph_explore`，其他 MCP 工具维持默认拒绝。CodeGraph 也可以走允许的 `codegraph explore`。`reviewer` 的额外 Shell 调用需确认。Shell 仍以宿主用户权限运行，白名单不是操作系统沙箱。

## 备份与恢复

每次实际替换会创建私有备份目录：

```text
~/.config/opencode/.opencode-config-backups/时间戳-随机后缀/
```

备份保留原来的文件或链接。脚本在普通写入异常或可处理的中断时尝试撤回本次替换；强制结束进程、断电等情况不能保证自动回退。

手动恢复时先停止相关会话，核对备份内容，然后将对应项移回原位置。备份中的相对符号链接可能只有回到原位置后才能正确解析。恢复安装状态文件时应同步考虑文件指纹；不确定时保留备份并重新预览。

`.opencode-config.lock` 防止多个安装器同时写入。异常退出留下锁时，先确认安装进程已经结束，再删除锁文件。安装器不会擅自清除其他进程的锁。

从源仓库移除的旧安装项不会自动删除，预览会标记为保留旧项；请核对后手动处理。

## 在隔离目录测试

可使用 `--target` 指定一个临时目录，测试结束后自行删除该目录。真实默认目录不会因此改变：

```bash
python3 scripts/install.py --target /tmp/opencode-config-preview --dry-run
python3 scripts/install.py --target /tmp/opencode-config-preview --apply
python3 scripts/check.py --target /tmp/opencode-config-preview --installed
```

正式启用后，用 `/connect` 完成该设备的 OpenAI 订阅登录，用 `/models` 核对模型和推理变体。首次真实请求还应核对服务档位确实为 Fast；离线检查无法证明订阅通道的运行行为。

Fast 模式统一使用 `providers.openai.body.service_tier: "priority"`。OpenAI API 文档也列出 `fast` 别名，但当前 OpenCode 订阅请求路径会拒绝该值并返回 `Unsupported service_tier: fast`。`priority` 保留 Fast 请求意图；本机覆盖也应使用该值，安装器会在写入前拒绝旧别名。参考 [OpenAI Fast 模式文档](https://developers.openai.com/api/docs/guides/fast-mode)。

## 配置依据

- [OpenCode 主配置](https://opencode.ai/v2/docs/config/)
- [OpenCode 主配置 Schema](https://opencode.ai/config.json)
- [终端配置](https://opencode.ai/v2/docs/cli/config/)
- [终端配置 Schema](https://opencode.ai/v2/cli.json)
- [Agent 与权限](https://opencode.ai/v2/docs/agents/)
- [权限规则](https://opencode.ai/v2/docs/permissions/)
- [命令与子会话](https://opencode.ai/v2/docs/commands/)
- [OpenAI Fast 请求参数](https://developers.openai.com/api/docs/guides/fast-mode)
