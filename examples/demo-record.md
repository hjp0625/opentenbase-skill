# 本地演示记录

提交者：何金鹏（学号 2601210327）


## 已实际运行

### 1. 单元测试

命令：`python -m unittest discover -s tests -v`

结果：6 项通过，退出码 `0`。完整输出见 [test-results.txt](test-results.txt)。这些测试使用模拟的外部命令，验证参数构造、SQL 白名单、错误处理和 JSON 输出。

### 2. 启停保护

命令：`python otb.py --json stop`

实际输出：

```json
{"ok": false, "error": "stop 需要 --yes 确认"}
```

退出码：`1`。没有执行集群停止命令。

### 3. 缺少运维程序时的错误输出

命令：`python otb.py --json status --ctl __missing_opentenbase_ctl__`

实际输出：

```json
{"ok": false, "error": "[WinError 2] 系统找不到指定的文件。"}
```

退出码：`1`。此演示只验证错误路径，不代表集群状态。

### 4. Skill 结构校验

命令：`python quick_validate.py opentenbase-ops`（使用 Codex skill-creator 随附的校验脚本）

实际输出：`Skill is valid!`

## 真实集群验收步骤

在已部署 OpenTenBase 5、可执行 `opentenbase_ctl` 与 `psql` 的环境中，将下列占位符替换为实际地址和文件路径：

```bash
python otb.py --json status --ctl opentenbase_ctl --config /path/to/config.ini
python otb.py --json nodes --host CN_HOST --port CN_PORT --user opentenbase
python otb.py --json create-table --host CN_HOST --port CN_PORT --schema public --table skill_demo --columns 'id integer PRIMARY KEY, name text' --distribution 'SHARD(id)' --group default_group
python otb.py --json logs --path /path/to/pg_log --lines 20
```

