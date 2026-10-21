# 安装、迁移与恢复

## 管理范围

安装器只管理以下路径，默认仅预览：

| 目标 | 安装方式 |
| --- | --- |
| `opencode.json` | 公共配置与本机覆盖合并后生成，权限为仅当前用户读写 |
| `cli.json` | 公共终端设置与本机覆盖合并后生成，权限为仅当前用户读写 |
| `AGENTS.md` | 链接到仓库中的个人通用指令 |
| `agents/*.md` | 按文件链接，不替换整个目录 |
| `commands/*.md` | 按文件链接，不替换整个目录 |
| `skills/<技能名>` | 按 `config/skills/sources.json` 链接固定版本的技能入口目录 |

未管理的文件和目录保留。

## 本机代理

代理需配置到 OpenCode 后台服务；终端中的 `export` 不会更新已运行的后台进程。

以下以本地 HTTP/混合代理端口 `1086` 为例，先启动代理程序；其他设备按实际端口调整：

```bash
opencode service set env HTTP_PROXY http://127.0.0.1:1086
opencode service set env HTTPS_PROXY http://127.0.0.1:1086
opencode service set env NO_PROXY localhost,127.0.0.1,::1
opencode service start
opencode api GET /api/info
```

两个代理地址均使用 `http://`，`NO_PROXY` 排除本地连接。修改服务环境会停止已有服务，最后需执行 `service start`。

`/api/info` 只验证本地服务；出站代理需通过一次真实模型请求验证。

如果只在当前终端使用临时代理，可执行：

```bash
export HTTP_PROXY=http://127.0.0.1:1086
export HTTPS_PROXY=http://127.0.0.1:1086
export NO_PROXY=localhost,127.0.0.1,::1
opencode --standalone
```

`--standalone` 启动使用当前终端环境的独立服务。

关闭持久代理：

```bash
opencode service unset env HTTP_PROXY
opencode service unset env HTTPS_PROXY
opencode service unset env NO_PROXY
opencode service start
```

不要提交带凭据的代理 URL 或分享完整服务环境。参考：[网络与代理文档](https://opencode.ai/v2/docs/network/)。

## 先准备本机覆盖

仅使用公共配置时无需创建额外文件。需要设备差异时，创建 `~/.config/opencode-config/local.json`，按需填写以下分区：

```json
{
  "opencode": {},
  "cli": {}
}
```

如果设置了 `XDG_CONFIG_HOME`，使用该目录下的 `opencode-config/local.json`，也可通过 `--local` 显式指定文件。

本机 MCP、绝对路径等设备差异放在此文件中。CodeGraph 的禁用示例见[接入说明](codegraph.md)。

本机覆盖由安装器读取，OpenCode 不会自动发现名为 `local.json` 的额外配置。对象递归合并，数组和标量整体替换；例如覆盖 `permissions` 数组意味着替换该层的整个数组，应保留仍需要的规则。

凭据优先通过 OpenCode 登录保存，或在 JSON 中使用 `{env:变量名}`。不要把真实密钥写进版本控制，也不要分享含认证信息的生成配置和备份。

## 迁移已有全局配置

首次安装不会自动导入已有 `opencode.json` 或 `opencode.jsonc`。先将仍需要的设置整理进本机覆盖文件，再预览替换。

- MCP 放入 `opencode.mcp.servers`；原 `enabled: true` 改为 `disabled: false`，OAuth 使用 V2 下划线字段。
- 终端设置放入 `cli` 分区。

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

生成文件被手动修改后，再次安装会报告冲突。内容一致但权限不是 `0600` 时会列为更新，备份后重新生成；`check.py --installed` 也会报告权限不符。

提示词和 Skill 使用链接，仓库内容更新会直接体现在链接目标上；JSON 修改则需要重新运行安装器。建议新建 OpenCode 会话应用新的默认 Agent 和指令。

Agent 权限控制不是操作系统沙箱，Shell 仍以当前用户权限执行。

## 备份与恢复

每次实际替换会创建私有备份目录：

```text
~/.config/opencode/.opencode-config-backups/时间戳-随机后缀/
```

备份保留原文件或链接。写入异常时尝试回退；强制结束进程或断电后需人工检查。

恢复时停止相关会话，将备份移回原位置。相对符号链接需回到原位置才能正确解析。保留备份并重新预览；若报告冲突，核对内容后再明确替换。

异常退出留下 `.opencode-config.lock` 时，先确认安装进程已结束，再删除锁文件。

从源仓库移除的旧安装项不会自动删除，预览会标记为保留旧项；请核对后手动处理。

## 在隔离目录测试

使用临时目标和空的本机覆盖，避免隐式读取真实设备设置。下列命令在支持符号链接的 macOS/Linux 上运行，退出时自动清理临时目录：

```bash
(
  set -eu
  sandbox=$(mktemp -d)
  trap 'rm -rf "$sandbox"' EXIT
  printf '{}\n' > "$sandbox/local.json"
  python3 scripts/install.py --target "$sandbox/target" --local "$sandbox/local.json" --dry-run
  python3 scripts/install.py --target "$sandbox/target" --local "$sandbox/local.json" --apply
  python3 scripts/check.py --target "$sandbox/target" --local "$sandbox/local.json" --installed
)
```

修改安装器时还需验证重复安装、手改冲突、替换备份、JSONC 停用、权限修复及异常回退。

## Fast 参数

使用 `providers.openai.body.service_tier: "priority"`。订阅通道不接受 `fast`，会返回 `Unsupported service_tier: fast`，安装器也会拒绝该值。实际 Fast 档位需通过真实请求确认。参考 [OpenAI Fast 模式文档](https://developers.openai.com/api/docs/guides/fast-mode)。

## 配置依据

- [OpenCode 主配置](https://opencode.ai/v2/docs/config/)
- [OpenCode 主配置 Schema](https://opencode.ai/config.json)
- [终端配置](https://opencode.ai/v2/docs/cli/config/)
- [终端配置 Schema](https://opencode.ai/v2/cli.json)
- [Agent 与权限](https://opencode.ai/v2/docs/agents/)
- [权限规则](https://opencode.ai/v2/docs/permissions/)
- [命令与子会话](https://opencode.ai/v2/docs/commands/)
- [OpenAI Fast 请求参数](https://developers.openai.com/api/docs/guides/fast-mode)
