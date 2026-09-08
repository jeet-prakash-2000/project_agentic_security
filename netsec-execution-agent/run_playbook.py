"""Headless playbook runner: read an Excel workbook and execute a playbook.

The web bulk-upload flow lives in ``netsec_service``; this module offers the
same behaviour from the command line so playbooks can be executed directly
against a YAML catalogue entry::

    python -m netsec_execution.run_playbook --list
    python -m netsec_execution.run_playbook changes.xlsx objects-addresses
    python -m netsec_execution.run_playbook changes.xlsx network-zones --json

The workbook's sheet is matched to the playbook (by title), each data row is
run through the playbook's handler and the engine returns per-row outcomes
plus aggregate counts. Connectivity and dry-run/apply mode come from the
``NETSEC_FW_*`` environment variables (see ``connector.panos``).

Exit codes: 0 when every row succeeded, 1 when any row errored, 2 for usage
or configuration errors.
"""

import argparse
import json
import os
import sys

from netsec_execution.connector.panos import PanosClient
from netsec_execution.services import catalog
from netsec_execution.services import engine


def _print_playbooks():
    rows = catalog.list_playbooks()
    header = "{0:<26} {1:<14} {2:<24} {3}".format(
        "id", "category", "sheet", "title"
    )
    sys.stdout.write(header + "\n")
    sys.stdout.write("-" * len(header) + "\n")
    for row in rows:
        sys.stdout.write(
            "{0:<26} {1:<14} {2:<24} {3}\n".format(
                row["id"], row["category"], row["sheet"], row["title"]
            )
        )


def _print_rows(rows):
    for record in rows:
        prefix = "row {0}".format(record.get("row", "?"))
        if record.get("op") == "error":
            sys.stdout.write(
                "  {0}  ERROR  {1}\n".format(prefix, record.get("error", ""))
            )
        else:
            sys.stdout.write(
                "  {0}  {1:<6}  {2}  {3}\n".format(
                    prefix,
                    record.get("op", "?"),
                    record.get("name", ""),
                    record.get("detail", ""),
                )
            )


def _main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read an Excel workbook and execute a YAML playbook."
    )
    parser.add_argument(
        "workbook", nargs="?", help="path to the filled-in .xlsx workbook"
    )
    parser.add_argument(
        "playbook", nargs="?", help="playbook id, e.g. objects-addresses"
    )
    parser.add_argument(
        "--list", action="store_true", help="list the available playbooks and exit"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="process at most this many data rows from the sheet",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="commit the candidate changes after the run (requires "
        "NETSEC_FW_DRY_RUN=0)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the engine result as JSON"
    )
    args = parser.parse_args(argv)

    if args.list:
        _print_playbooks()
        return 0
    if not args.workbook or not args.playbook:
        parser.print_help()
        return 2
    if not os.path.exists(args.workbook):
        sys.stderr.write("Workbook not found: {0}\n".format(args.workbook))
        return 2

    client = PanosClient()
    if not client.configured:
        sys.stderr.write(
            "NetSec Execution agent is not connected to a firewall. Missing "
            "environment configuration: {0}\n".format(
                ", ".join(client.missing_config())
            )
        )
        return 2

    try:
        result = engine.run_playbook(
            client,
            args.playbook,
            workbook_path=args.workbook,
            row_limit=args.limit,
            commit=True if args.commit else None,
        )
    except ValueError as exc:
        sys.stderr.write("{0}\n".format(exc))
        return 2

    result["host"] = client.host
    counts = result.get("counts", {})
    if args.json:
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        sys.stdout.write(str(result.get("summary", "")) + "\n")
        sys.stdout.write(
            "  rows={0} created={1} updated={2} deleted={3} errors={4} "
            "committed={5}\n".format(
                counts.get("rows", 0),
                counts.get("created", 0),
                counts.get("updated", 0),
                counts.get("deleted", 0),
                counts.get("errors", 0),
                bool(result.get("committed")),
            )
        )
        if counts.get("errors"):
            sys.stdout.write("  per-row results:\n")
            _print_rows(result.get("rows", []))
    return 0 if not counts.get("errors") else 1


if __name__ == "__main__":
    sys.exit(_main())
