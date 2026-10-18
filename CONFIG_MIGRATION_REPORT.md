# 正式配置文件迁移报告

## 结果

删除两份模板，统一使用仓库根目录的 `config.yaml` 与 `downloader.json` 作为配置来源。
实际下载器文件名为 `downloader.json`，本次未更名为 `download.json`。

## 改动清单

| 文件 | 改动 |
| --- | --- |
| `.gitignore` | 用户已移除对两份正式配置的忽略规则；本次保留此修改 |
| `config.yaml`、`downloader.json` | 用户计划纳入 Git；当前为未跟踪文件，本次未修改内容 |
| `config.yaml.sample`、`downloader.json.sample.json` | 删除模板 |
| `start.sh`、`start.bat` | 移除从模板生成配置的逻辑；启动前要求正式配置文件存在，缺失时沿用明确报错机制 |
| `Dockerfile`、`Dockerfile.gpu` | 直接复制正式配置到镜像；同步修正模板相关注释 |
| `desktop/VideoPrinterTurbo.spec` | 将两份正式配置作为桌面版内置资源 |
| `desktop/launcher.py` | 首次运行从内置正式配置复制到用户数据目录，已有文件保持不变 |
| `desktop/README.md` | 更新配置来源、首次复制行为及配置随产物分发的说明 |
| `AGENTS.md` | 同步配置纳入版本控制及各运行方式的配置约定 |
| `CONFIG_MIGRATION_REPORT.md` | 本报告 |

## 行为影响

- 源码启动：直接读取仓库正式配置，不再自动生成配置文件。
- Docker：CPU/GPU 镜像都携带仓库正式配置，保留既有容器配置补齐逻辑。
- 桌面版：Windows/macOS 共用的打包与初始化逻辑均已更新；升级后仍保留用户已有配置。
- 后端、前端业务逻辑和 API 均未修改。
- 两份正式配置会进入仓库和分发产物，应保持为可公开的默认配置。

## 验证结果

已通过：

- 两套启动脚本内嵌 Python 语法检查及共享逻辑一致性检查。
- 桌面启动器与打包 spec 的 Python 语法检查。
- 临时隔离数据目录内的桌面首次配置复制检查。
- 再次初始化保留已有 YAML/JSON 用户配置的检查。
- 两份 Dockerfile 的正式配置来源存在性检查。
- Shell 启动脚本语法检查和 Git 差异空白检查。
- 全仓库搜索旧模板文件名无残留引用（本报告说明除外）。

验证边界：未执行完整 Docker 镜像构建、Windows/macOS 桌面打包或完整服务启动。
未修改前端，因此未运行前端类型检查、测试和构建。
未执行 Git 暂存、提交或推送；提交时需要包含两份尚未跟踪的正式配置。
