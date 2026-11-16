"""Run a reproducible stage analysis on an isolated synthetic SQLite database."""

import json
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker import connect

AS_OF = "2026-10-15T00:00:00Z"
SAMPLE = (
    ("CORE-100", ((1, "DRAFT"), (2, "SUBMITTED"), (3, "IN_REVIEW"),
                  (9, "APPROVED"), (10, "RELEASED"))),
    ("BRKT-200", ((1, "DRAFT"), (2, "SUBMITTED"), (4, "IN_REVIEW"),
                  (12, "APPROVED"), (14, "RELEASED"))),
    ("SEAL-300", ((2, "DRAFT"), (3, "SUBMITTED"), (5, "IN_REVIEW"))),
    ("BOLT-400", ((9, "DRAFT"), (10, "SUBMITTED"))),
    ("CAP-500", ((8, "DRAFT"), (9, "SUBMITTED"), (11, "REJECTED"))),
)


def run_demo():
    query = (Path(__file__).resolve().parents[1] / "sql" / "stage_metrics.sql").read_text(
        encoding="utf-8"
    )
    with TemporaryDirectory() as directory:
        with closing(connect(Path(directory) / "demo.sqlite")) as database:
            with database:
                for part, events in SAMPLE:
                    change = database.execute(
                        """INSERT INTO changes (part_number, from_rev, to_rev, description, status)
                           VALUES (?, 'A', 'B', 'Synthetic revision change', ?)""",
                        (part, events[-1][1]),
                    )
                    previous = None
                    for day, stage in events:
                        database.execute(
                            """INSERT INTO history (change_id, from_status, to_status, actor, timestamp)
                               VALUES (?, ?, ?, 'demo', ?)""",
                            (change.lastrowid, previous, stage, f"2026-10-{day:02d}T00:00:00Z"),
                        )
                        previous = stage
            return [
                dict(row) for row in database.execute(query, {"as_of": AS_OF})
            ]


if __name__ == "__main__":
    print(json.dumps({"as_of": AS_OF, "stages": run_demo()}, indent=2))
