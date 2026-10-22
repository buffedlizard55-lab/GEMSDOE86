"""Validate every local HTML href/src in the GitHub Pages site."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LocalLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.links.append(value.strip())


def check_local_links() -> list[str]:
    errors: list[str] = []
    for html in sorted(DOCS.rglob("*.html")):
        parser = LocalLinkParser()
        parser.feed(html.read_text(encoding="utf-8"))
        for link in parser.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or link.startswith("#"):
                continue
            target_path = unquote(parsed.path)
            if not target_path:
                continue
            target = (html.parent / target_path).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{html.relative_to(ROOT)}: link escapes repository: {link}")
                continue
            if not target.exists():
                errors.append(f"{html.relative_to(ROOT)}: missing local target: {link}")
    return errors


def main() -> int:
    errors = check_local_links()
    if errors:
        print("Broken local documentation links:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("All local HTML links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
