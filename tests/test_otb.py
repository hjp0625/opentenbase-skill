import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import otb


class OTBTests(unittest.TestCase):
    def test_status_command_and_node_filter(self):
        args = otb.build_parser().parse_args(["status", "--ctl", "ctl", "--config", "config.ini", "--node", "cn0001"])
        with patch("otb.subprocess.run") as run:
            run.return_value = argparse.Namespace(returncode=0, stdout="Running", stderr="")
            self.assertEqual(otb.execute(args)["output"], "Running")
            run.assert_called_once_with(["ctl", "status", "-c", "config.ini", "-n", "cn0001"], text=True, capture_output=True, check=False)

    def test_stop_requires_confirmation(self):
        args = otb.build_parser().parse_args(["stop"])
        with patch("otb.subprocess.run") as run:
            with self.assertRaisesRegex(ValueError, "--yes"):
                otb.execute(args)
            run.assert_not_called()

    def test_table_sql_and_injection_rejection(self):
        args = otb.build_parser().parse_args(["create-table", "--schema", "public", "--table", "orders", "--columns", "id integer PRIMARY KEY, amount numeric(10,2)", "--distribution", "SHARD(id)", "--group", "default_group"])
        self.assertEqual(otb.create_table_sql(args), 'CREATE TABLE "public"."orders" ("id" INTEGER PRIMARY KEY, "amount" NUMERIC(10,2)) DISTRIBUTE BY SHARD("id") TO GROUP "default_group"')
        args.table = "orders; DROP TABLE x"
        with self.assertRaises(ValueError):
            otb.create_table_sql(args)

    def test_grant_whitelist(self):
        args = otb.build_parser().parse_args(["grant", "--schema", "public", "--table", "orders", "--role", "reader", "--privilege", "SELECT"])
        self.assertEqual(otb.grant_sql(args), 'GRANT SELECT ON TABLE "public"."orders" TO "reader"')
        args.privilege = "ALL"
        with self.assertRaises(ValueError):
            otb.grant_sql(args)

    def test_logs_reads_latest_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "postgresql.log"
            path.write_text("one\ntwo\nthree\n", encoding="utf-8")
            args = otb.build_parser().parse_args(["logs", "--path", directory, "--lines", "2"])
            self.assertEqual(otb.execute(args)["lines"], "two\nthree")

    def test_json_error(self):
        from io import StringIO
        stream = StringIO()
        with patch("sys.stdout", stream):
            code = otb.main(["--json", "stop"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(stream.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
