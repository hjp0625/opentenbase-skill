#!/usr/bin/env python3
"""Small, dependency-free OpenTenBase 5 operations CLI."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


IDENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")
ALLOWED_PRIVILEGES = {"SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"}


def identifier(value):
    if not IDENT.fullmatch(value):
        raise ValueError(f"无效的 SQL 标识符: {value!r}")
    return '"' + value + '"'


def columns_sql(value):
    # A deliberately narrow DDL surface; no arbitrary SQL execution.
    parts = [part.strip() for part in re.split(r",(?![^()]*\))", value)]
    if not parts or any(not part for part in parts):
        raise ValueError("--columns 不能为空")
    result = []
    pattern = re.compile(r"^([A-Za-z_][A-Za-z_0-9]*)\s+(smallint|integer|int|bigint|text|boolean|date|timestamp|varchar\([1-9][0-9]{0,4}\)|numeric\([1-9][0-9]{0,2},[0-9]{1,2}\))(\s+(?:PRIMARY KEY|NOT NULL|UNIQUE))?$", re.I)
    for part in parts:
        match = pattern.fullmatch(part)
        if not match:
            raise ValueError(f"不支持的列定义: {part!r}")
        result.append(f"{identifier(match[1])} {match[2].upper()}{(match[3] or '').upper()}")
    return ", ".join(result)


def create_table_sql(args):
    distribution = args.distribution.strip()
    if distribution.upper() == "REPLICATION":
        dist_sql = "REPLICATION"
    else:
        match = re.fullmatch(r"SHARD\(([A-Za-z_][A-Za-z_0-9]*)\)", distribution, re.I)
        if not match:
            raise ValueError("--distribution 只能是 REPLICATION 或 SHARD(列名)")
        dist_sql = f"SHARD({identifier(match[1])})"
    return (f"CREATE TABLE {identifier(args.schema)}.{identifier(args.table)} "
            f"({columns_sql(args.columns)}) DISTRIBUTE BY {dist_sql} "
            f"TO GROUP {identifier(args.group)}")


def grant_sql(args):
    privilege = args.privilege.upper()
    if privilege not in ALLOWED_PRIVILEGES:
        raise ValueError("不支持的表级权限")
    return (f"GRANT {privilege} ON TABLE {identifier(args.schema)}."
            f"{identifier(args.table)} TO {identifier(args.role)}")


def run_command(argv):
    completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"命令失败（退出码 {completed.returncode}）：{detail}")
    return completed.stdout.strip()


def ctl_command(args):
    argv = [args.ctl, args.command]
    if args.config:
        argv += ["-c", args.config]
    if args.node:
        argv += ["-n", args.node]
    return run_command(argv)


def psql_command(args, sql):
    argv = ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-A", "-t", "-F", "\t",
            "-h", args.host, "-p", str(args.port), "-U", args.user, "-d", args.database,
            "-c", sql]
    return run_command(argv)


def read_logs(args):
    path = Path(args.path)
    if path.is_dir():
        files = [item for item in path.iterdir() if item.is_file() and not item.is_symlink()]
        if not files:
            raise ValueError("日志目录中没有普通文件")
        path = max(files, key=lambda item: item.stat().st_mtime)
    if not path.is_file() or path.is_symlink():
        raise ValueError("日志路径不是可读的普通文件")
    # Bound memory even if a log file is large.
    from collections import deque
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        lines = list(deque(stream, maxlen=args.lines))
    return {"path": str(path), "lines": "".join(lines).rstrip("\n")}


def build_parser():
    parser = argparse.ArgumentParser(description="OpenTenBase 5 Agent 运维 CLI")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "start", "stop"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--ctl", default="opentenbase_ctl")
        cmd.add_argument("--config", help="opentenbase_ctl 配置文件")
        cmd.add_argument("--node", help="节点名、类型或 host:port")
        if name != "status":
            cmd.add_argument("--yes", action="store_true", help="确认启停操作")
    for name in ("nodes", "create-database", "create-table", "grant"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--host", default=os.getenv("OTB_HOST", "127.0.0.1"))
        cmd.add_argument("--port", type=int, default=int(os.getenv("OTB_PORT", "11000")))
        cmd.add_argument("--user", default=os.getenv("OTB_USER", "opentenbase"))
        cmd.add_argument("--database", default=os.getenv("OTB_DATABASE", "postgres"))
        if name == "create-database":
            cmd.add_argument("--name", required=True)
        elif name == "create-table":
            cmd.add_argument("--schema", required=True)
            cmd.add_argument("--table", required=True)
            cmd.add_argument("--columns", required=True)
            cmd.add_argument("--distribution", required=True)
            cmd.add_argument("--group", required=True)
        elif name == "grant":
            cmd.add_argument("--schema", required=True)
            cmd.add_argument("--table", required=True)
            cmd.add_argument("--role", required=True)
            cmd.add_argument("--privilege", required=True)
    cmd = sub.add_parser("logs")
    cmd.add_argument("--path", required=True)
    cmd.add_argument("--lines", type=int, default=100)
    return parser


def execute(args):
    if args.command in ("start", "stop") and not args.yes:
        raise ValueError(f"{args.command} 需要 --yes 确认")
    if args.command in ("status", "start", "stop"):
        return {"command": args.command, "output": ctl_command(args)}
    if args.command == "logs":
        if not 1 <= args.lines <= 10000:
            raise ValueError("--lines 应在 1 到 10000 之间")
        return read_logs(args)
    if not 1 <= args.port <= 65535:
        raise ValueError("无效端口")
    if args.command == "nodes":
        sql = "SELECT node_name, node_type, node_host, node_port FROM pgxc_node ORDER BY node_name"
    elif args.command == "create-database":
        sql = f"CREATE DATABASE {identifier(args.name)}"
    elif args.command == "create-table":
        sql = create_table_sql(args)
    else:
        sql = grant_sql(args)
    return {"command": args.command, "sql": sql, "output": psql_command(args, sql)}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = {"ok": True, **execute(args)}
        code = 0
    except (ValueError, OSError, RuntimeError) as exc:
        result = {"ok": False, "error": str(exc)}
        code = 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result.get("output", result.get("lines", result.get("error", ""))))
    return code


if __name__ == "__main__":
    sys.exit(main())
