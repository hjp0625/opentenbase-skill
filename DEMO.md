# 演示记录

## 本地模拟演示

环境：Python 3.10+，本仓库代码。没有使用真实 OpenTenBase 集群或真实生产数据。

```text
$ python -m unittest discover -s tests -v
Ran 6 tests
OK

$ python otb.py --json stop
{"ok": false, "error": "stop 需要 --yes 确认"}
```

测试覆盖状态命令与节点过滤、启停确认、分片表 SQL、标识符注入拦截、权限白名单、日志尾部读取和 JSON 错误输出。

## 真实集群演示步骤

以下命令需在已部署 OpenTenBase 5 且能访问 `opentenbase_ctl`、`psql` 的机器上执行。参数按实际集群替换；执行后把输出附在作业提交记录中。

```bash
python otb.py --json status --ctl opentenbase_ctl --config /path/to/config.ini
python otb.py --json nodes --host <CN_HOST> --port <CN_PORT> --user opentenbase
python otb.py --json create-table --host <CN_HOST> --port <CN_PORT> --user opentenbase --schema public --table skill_demo --columns 'id integer PRIMARY KEY, name text' --distribution 'SHARD(id)' --group default_group
python otb.py --json logs --path /path/to/pg_log --lines 20
```

预期：`status` 返回各节点运行情况，`nodes` 列出 CN/DN/GTM 路由，`create-table` 返回 SQL 成功结果，`logs` 返回指定日志尾部。真实集群验证尚未完成，不将这些预期写成已观察结果。
