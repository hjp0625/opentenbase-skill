# OpenTenBase Agent 运维 Skill

课程作业的工具贡献：把 OpenTenBase 5 的常见运维操作封装为可供 Agent 调用的 Skill 和命令行工具。范围包括集群及节点状态、集群启停、节点查看、库表创建、权限管理和日志查看。

## 安装

需要 Python 3.10+、已部署的 OpenTenBase 5 集群，以及能执行 `opentenbase_ctl` 和 `psql` 的环境。工具本身只依赖 Python 标准库。

```bash
python otb.py --help
python otb.py status --ctl /path/to/opentenbase_ctl --config /path/to/config.ini
```

Agent Skill 位于 [`opentenbase-ops/SKILL.md`](opentenbase-ops/SKILL.md)。将整个 `opentenbase-ops` 目录复制到 Codex 的 skills 目录后即可使用；也可直接让 Agent 阅读此文件。命令通过 `--json` 输出结构化结果，失败时返回非零退出码。

连接参数可通过 `--host`、`--port`、`--user`、`--database` 指定，也可使用 `OTB_HOST`、`OTB_PORT`、`OTB_USER`、`OTB_DATABASE` 环境变量。密码交给 libpq 的 `.pgpass` 或 `PGPASSWORD`，工具不会接收或记录密码。

## 示例

```bash
python otb.py --json status --ctl opentenbase_ctl --config config.ini
python otb.py --json nodes --host 127.0.0.1 --port 11000 --user opentenbase
python otb.py --json create-table --schema public --table demo --columns 'id integer PRIMARY KEY, name text' --distribution 'SHARD(id)' --group default_group
python otb.py --json grant --privilege SELECT --schema public --table demo --role reader
python otb.py --json logs --path /data/opentenbase/data/pg_log --lines 100
python otb.py --json start --ctl opentenbase_ctl --config config.ini --yes
```

`start`、`stop`、创建库表和 `grant` 是写操作；`start`/`stop` 需要 `--yes`。日志路径必须是当前机器可读的本地文件或目录，目录模式读取最新修改的普通日志文件。工具不会运行任意 shell 命令。

## 测试

```bash
python -m unittest discover -s tests -v
```

测试通过模拟外部命令校验参数、SQL 构造、错误处理和 JSON 输出；没有可连接的课程集群时，不把模拟结果当作真实集群验证。实际演示步骤和记录见 [`DEMO.md`](DEMO.md)。

## 课程知识对应

| 课程知识 | 工具中的应用 |
| --- | --- |
| GTM / CN / DN 分布式架构 | `nodes` 查询 `pgxc_node`，`status` 查询各节点运行状态 |
| 分片表与复制表 | `create-table` 支持 `SHARD(列)` 和 `REPLICATION` |
| 集群部署与运维 | `opentenbase_ctl status/start/stop`，保留配置文件参数 |
| 数据库权限 | `grant` 指定表级权限与角色 |
| 故障定位 | `logs` 读取近期日志，结合状态输出排查 |

以上语法参考本地课程材料《OpenTenBase 课程4 集群部署与运维》的运维与建表章节。实际支持的语法和参数应以目标集群版本的 `--help` 与 SQL 测试结果为准。

