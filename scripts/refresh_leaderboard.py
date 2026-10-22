#!/usr/bin/env python3
"""Refresh an evidence-labelled snapshot from the official DrivenData public leaderboard.

The fetch is deliberately fail-closed: redirects to login or a page-layout change do not
replace the last published JSON with an empty or guessed board. This is a public leaderboard
feed, not a project submission receipt.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SOURCE_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
USER_AGENT = "GEMSDOE86-auditable-leaderboard-feed/1.0 (public competition page)"


@dataclass
class Cell:
    tag: str
    parts: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


class TableParser(HTMLParser):
    """Extract top-level HTML tables and retain visible link labels for participant names."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[Cell]]] = []
        self.table_depth = 0
        self.table: list[list[Cell]] | None = None
        self.row: list[Cell] | None = None
        self.cell: Cell | None = None
        self.anchor_depth = 0
        self.anchor_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            if self.table_depth == 0:
                self.table = []
                self.tables.append(self.table)
            self.table_depth += 1
            return
        if self.table_depth != 1:
            return
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = Cell(tag=tag)
        elif tag == "a" and self.cell is not None:
            self.anchor_depth += 1
            if self.anchor_depth == 1:
                self.anchor_parts = []
        elif tag in ("br",) and self.cell is not None:
            self.cell.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "table":
            if self.table_depth:
                self.table_depth -= 1
            if self.table_depth == 0:
                self.row = None
                self.cell = None
                self.table = None
            return
        if self.table_depth != 1:
            return
        if tag == "a" and self.anchor_depth and self.cell is not None:
            self.anchor_depth -= 1
            if self.anchor_depth == 0:
                link_text = " ".join(" ".join(self.anchor_parts).split())
                if link_text:
                    self.cell.links.append(link_text)
                self.anchor_parts = []
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None

    def handle_data(self, data: str) -> None:
        if self.cell is None:
            return
        self.cell.parts.append(data)
        if self.anchor_depth:
            self.anchor_parts.append(data)


def _header_key(cell: Cell) -> str:
    return re.sub(r"[^a-z0-9]+", " ", cell.text.lower()).strip()


def _header_indices(table: list[list[Cell]]) -> tuple[int, int, int] | None:
    for row in table[:8]:
        keys = [_header_key(cell) for cell in row]
        rank_i = next((i for i, text in enumerate(keys) if text in {"rank", "place"}), None)
        participant_i = next(
            (i for i, text in enumerate(keys) if "participant" in text or text == "team name"),
            None,
        )
        score_i = next(
            (i for i, text in enumerate(keys) if "tversky" in text or "public score" in text),
            None,
        )
        if rank_i is not None and participant_i is not None and score_i is not None:
            return rank_i, participant_i, score_i
    return None


def _first_number(text: str) -> float | None:
    match = re.search(r"(?<![\w.])(?:0(?:\.\d+)?|1(?:\.0+)?)(?![\w.])", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_leaderboard_html(html: str) -> list[dict]:
    parser = TableParser()
    parser.feed(html)
    for table in parser.tables:
        indices = _header_indices(table)
        if indices is None:
            continue
        rank_i, participant_i, score_i = indices
        data: list[dict] = []
        for row in table:
            if max(indices) >= len(row):
                continue
            rank_match = re.search(r"\d+", row[rank_i].text)
            score = _first_number(row[score_i].text)
            name_cell = row[participant_i]
            name = name_cell.links[0] if name_cell.links else name_cell.text.split("\n", 1)[0].strip()
            if not rank_match or not name or score is None or not 0.0 <= score <= 1.0:
                continue
            data.append({
                "rank": int(rank_match.group(0)),
                "participant": name,
                "score": score,
                "evidence_class": "ORGANIZER-CONFIRMED",
                "evidence_scope": "official public leaderboard listing; not a GEMSDOE86 result or artifact receipt",
            })
        if data:
            data.sort(key=lambda item: item["rank"])
            ranks = [item["rank"] for item in data]
            if len(ranks) != len(set(ranks)) or ranks[0] != 1:
                raise ValueError("Leaderboard table is malformed: ranks are missing or duplicated")
            return data
    raise ValueError("Could not identify the official leaderboard table; feed was not updated")


def fetch_html(url: str = SOURCE_URL, timeout: int = 30) -> tuple[str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            status = getattr(response, "status", 200)
            host = (urlparse(final_url).hostname or "").lower()
            if status != 200 or host not in {"drivendata.org", "www.drivendata.org"}:
                raise ValueError(f"Unexpected leaderboard response (HTTP {status}, {final_url})")
            if "/competitions/306/competition-doe-gems/leaderboard" not in urlparse(final_url).path:
                raise ValueError(f"Leaderboard request left the official board URL: {final_url}")
            return response.read().decode("utf-8", errors="replace"), final_url
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch the official public leaderboard: {exc}") from exc


def build_snapshot(html: str, fetched_url: str = SOURCE_URL) -> dict:
    rows = parse_leaderboard_html(html)
    return {
        "schema_version": 1,
        "source_url": fetched_url,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence_class": "ORGANIZER-CONFIRMED",
        "evidence_scope": "official public leaderboard snapshot; entries are not project receipts",
        "row_count": len(rows),
        "rows": rows,
        "notice": "A board entry is not evidence that GEMSDOE86 produced or submitted that artifact.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/data/leaderboard.json"))
    parser.add_argument("--input-html", type=Path, help="parse a saved HTML file (tests/review only; no network)")
    args = parser.parse_args(argv)
    try:
        if args.input_html:
            html = args.input_html.read_text(encoding="utf-8")
            fetched_url = SOURCE_URL
        else:
            html, fetched_url = fetch_html()
        snapshot = build_snapshot(html, fetched_url)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"leaderboard refresh failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {snapshot['row_count']} official public leaderboard rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
