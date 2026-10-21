# 技能来源与启用清单

[sources.json](sources.json) 登记来源地址、用途和技能 ID 到入口目录的映射。版本与许可见 [THIRD_PARTY.md](../../THIRD_PARTY.md)，使用方式见[技能说明](../../docs/skills.md)。

## 登记规则

- 来源名称与 `.gitmodules` 的子模块名称、目录名一致。
- 在 `.gitmodules` 中设置 `shallow = true`；初始化与获取提交仍显式使用 `--depth 1`，避免补取固定旧提交时下载额外历史。
- `repository` 填写上游仓库地址，`description` 使用中文说明用途。
- `skills` 的键为技能入口的 `name`，值为相对子模块根目录的路径；每个入口必须含 `SKILL.md`，ID 全局唯一。
- 安装器仅链接登记的入口到全局配置的 `skills/<技能名>`，不加载上游根目录指令或插件。
- 个人使用约定写在父仓库，不直接修改子模块内容。

## 添加其他来源

1. 先审查仓库用途、技能入口和许可，选择固定提交。
2. 使用来源名称作为子模块名称和目录名称，例如：

   ```bash
   git submodule add --depth 1 --name example-skills https://github.com/作者/仓库.git config/skills/example-skills
   git config -f .gitmodules submodule.example-skills.shallow true
   git -C config/skills/example-skills fetch --depth 1 origin <固定提交>
   git -C config/skills/example-skills checkout --detach FETCH_HEAD
   ```

3. 按上述规则在 `sources.json` 登记入口，在 `THIRD_PARTY.md` 记录固定提交与许可，保留上游许可证。
4. 运行 `python3 scripts/check.py`，并按[隔离验证步骤](../../docs/setup.md#在隔离目录测试)验证新增链接。提交父仓库时同时包含 `.gitmodules`、子模块提交记录、清单及来源记录。

## 主动升级

选择新提交后定向浅获取，不使用 `--unshallow` 或 `update --remote`：

```bash
git -C config/skills/<来源> fetch --depth 1 origin <新提交>
git -C config/skills/<来源> checkout --detach FETCH_HEAD
```

回到父仓库检查差异、更新来源记录并测试。上游新增技能不会自动启用，仍需修改清单。
