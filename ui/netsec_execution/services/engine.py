"""Playbook execution engine.

Runs a single playbook against a parsed workbook and a :class:`PanosClient`.
Every row is executed independently so one bad row never aborts the rest; the
engine returns per-row outcomes plus aggregate counts and a human summary
suitable for rendering in the AI Workspace chat.
"""

import logging

from netsec_execution.services import catalog
from netsec_execution.services import workbook

logger = logging.getLogger("netsec.engine")


def _find_sheet(rows, playbook):
    target = (playbook.get("sheet") or "").strip().lower().replace(" ", "")
    for title, data in rows.items():
        if title.strip().lower().replace(" ", "") == target:
            return data
    raise ValueError(
        "The uploaded workbook has no {0!r} sheet (found: {1}).".format(
            playbook.get("sheet"), ", ".join(sorted(rows.keys())) or "none"
        )
    )


def _op_label(op):
    return {
        "create": "created",
        "update": "updated",
        "delete": "deleted",
    }.get(op, op)


def _count_key(op):
    return {"create": "created", "update": "updated", "delete": "deleted"}.get(op, op)


def run_playbook(client, playbook_id, workbook_path=None, rows=None, row_limit=None):
    """Execute ``playbook_id`` against workbook rows.

    Pass either ``workbook_path`` (parsed automatically) or already-parsed
    ``rows``. Returns a result dict safe to JSON-serialize.
    """
    playbook = catalog.find_playbook(playbook_id)
    if playbook is None:
        raise ValueError("Unknown playbook id: {0}".format(playbook_id))
    if rows is None:
        if not workbook_path:
            raise ValueError("run_playbook requires a workbook path or rows.")
        rows = workbook.read_workbook(workbook_path)
    sheet = _find_sheet(rows, playbook)

    logger.info(
        "Running playbook %s (%s) dry_run=%s on %s rows",
        playbook_id, playbook.get("title"), client.dry_run, sheet["row_count"],
    )

    per_row = []
    counts = {
        "rows": 0,
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "errors": 0,
        "skipped": 0,
    }
    apply = playbook["apply"]

    for index, row in enumerate(sheet["rows"]):
        if row_limit is not None and index >= row_limit:
            break
        counts["rows"] += 1
        record = {"row": index + 2}
        try:
            result = apply(client, row)
            op = result.get("op", "create")
            counts[_count_key(op)] = counts.get(_count_key(op), 0) + 1
            record.update(
                {
                    "op": op,
                    "dry_run": bool(result.get("dry_run", client.dry_run)),
                    "kind": result.get("kind", playbook.get("title")),
                    "name": result.get("name", ""),
                    "detail": result.get("detail", ""),
                }
            )
        except Exception as exc:  # noqa: BLE001 - per-row isolation
            counts["errors"] += 1
            record.update({"op": "error", "error": str(exc)[:300]})
            logger.warning(
                "playbook %s row %s failed: %s", playbook_id, index + 2, exc
            )
        per_row.append(record)

    summary_text = _summary_text(playbook, counts, client.dry_run)
    return {
        "playbook_id": playbook_id,
        "playbook_title": playbook.get("title"),
        "category": playbook.get("category"),
        "sheet": playbook.get("sheet"),
        "dry_run": bool(client.dry_run),
        "counts": counts,
        "rows": per_row,
        "summary": summary_text,
    }


def _summary_text(playbook, counts, dry_run):
    label = "previewed" if dry_run else "applied"
    prefix = "Dry-run" if dry_run else "Applied"
    created = "{0} {1}".format(counts["created"], _op_label("create"))
    updated = "{0} {1}".format(counts["updated"], _op_label("update"))
    deleted = "{0} {1}".format(counts["deleted"], _op_label("delete"))
    segments = [created, updated, deleted]
    if counts["errors"]:
        segments.append("{0} errors".format(counts["errors"]))
    if counts["skipped"]:
        segments.append("{0} skipped".format(counts["skipped"]))
    if not counts["rows"]:
        return "{0} playbook {1}: no data rows found in sheet {2}.".format(
            prefix, playbook.get("title"), playbook.get("sheet")
        )
    return (
        "{0} playbook {1}: {2} row(s) {3} against the firewall "
        "({4}).".format(
            prefix,
            playbook.get("title"),
            counts["rows"],
            label,
            ", ".join(segments),
        )
    )
