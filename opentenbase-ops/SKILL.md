---
name: opentenbase-ops
description: Diagnose and operate an OpenTenBase 5 cluster with the bundled CLI. Use for cluster and node status, logs, database tables, privileges, and controlled start or stop operations when the user provides cluster access.
---

# OpenTenBase 运维

使用本仓库的 `otb.py` 调用 OpenTenBase 5 的常见运维能力。先确认当前仓库路径、目标集群、`opentenbase_ctl` 配置文件和 CN 连接参数；不假设课程示例 IP、端口或路径适用于用户环境。通过 `python otb.py --json <command> ...` 获取可解析结果。首次使用先运行 `python otb.py --help`。

## 操作顺序

1. 状态排查：运行 `status`；需要节点路由时运行 `nodes`；需要故障线索时读取用户指定的本地日志路径。`status` 中的 `Unknown` 也可能是 SSH 或主机故障，不应直接判定数据库进程故障。
2. SQL 变更：确认 CN 连接成功、目标数据库/模式/表名、分布方式与节点组。分片表使用 `--distribution SHARD(column)`；小型维度表可用 `REPLICATION`。创建后用 `nodes` 和查询验证，不能仅根据命令退出码宣称业务可用。
3. 权限：按用户要求指定角色与权限，先核对目标对象。不要自动授予 `ALL` 或扩大到整个模式。
4. 启停：先读取当前状态并确认用户授权的目标。使用 `--yes` 执行 `start`/`stop`，之后再次运行 `status` 核对结果。生产集群中停止节点可能影响服务，必要时询问维护窗口。

`otb.py` 只允许预定义操作，不接受任意 SQL 或 shell 命令。连接密码由 libpq 管理，不写进命令或输出。若环境没有真实集群，就展示命令并明确标注未做集成验证。使用说明和模拟测试见仓库根目录的 `README.md`、`tests/`。
