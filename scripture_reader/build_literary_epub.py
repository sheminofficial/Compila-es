#!/usr/bin/env python3
"""Build the honest literary-manuscript EPUB.

Only chapters present in scripture_reader/manuscript are included. The final
filename is emitted only after all 1,189 chapters and review rows are present.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

from ebooklib import epub

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPTS = ROOT / "scripture_reader" / "manuscript"
GENERATED = ROOT / "generated"
EXPECTED_CHAPTERS = 1189
FINAL_NAME = "The_Bible_Retold_Complete_English_Edition.epub"
PREVIEW_NAME = "The_Bible_Retold_Editorial_Preview.epub"

BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Songs", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark",
    "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus",
    "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
]
CHAPTER_COUNTS = dict(zip(BOOK_ORDER, [50,40,27,36,34,24,21,4,31,24,22,25,29,36,10,13,10,42,150,31,12,8,66,52,5,48,12,14,3,9,1,4,7,3,3,3,2,14,4,28,16,24,21,28,16,16,13,6,6,4,4,5,3,6,4,3,1,13,5,5,3,5,1,1,1,22]))
ALIASES = {"Song of Solomon": "Song of Songs"}

CSS = """
:root { color-scheme: light dark; }
body { font-family: Georgia, 'Noto Serif', serif; line-height: 1.68; margin: 5%; max-width: 42em; }
h1,h2,.eyebrow,.meta { font-family: Arial, 'Noto Sans', sans-serif; }
h1 { color: #8b5634; line-height: 1.15; } h2 { color: #a36b43; }
p { margin: .82em 0; } .eyebrow { letter-spacing: .12em; text-transform: uppercase; font-size: .72em; color: #936d51; }
.meta,.notice { font-size: .86em; color: #6f625a; }
.notice { border-left: .28em solid #b98256; padding: .65em 1em; background: rgba(185,130,86,.12); }
a { color: #8b5634; } a.vocab { color: inherit; text-decoration-line: underline; text-decoration-style: dashed; text-decoration-color: #b47a50; text-underline-offset: .2em; }
dl { margin: 0; } dt { font-weight: bold; color: #8b5634; margin-top: 1.1em; } dd { margin: .25em 0 0 1em; }
@media (prefers-color-scheme: dark) { h1,h2,a,dt { color: #e2ae82; } .meta,.notice,.eyebrow { color: #c9b6a7; } }
"""


def slug(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def inline(text: str) -> str:
    text = html.escape(text.strip())
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def parse(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", raw, re.M)
    if not title_match:
        raise ValueError(f"Missing book title: {path}")
    book = ALIASES.get(title_match.group(1).strip(), title_match.group(1).strip())
    starts = list(re.finditer(r"^## Chapter (\d+)\s+—\s+(.+)$", raw, re.M))
    chapters = []
    for i, match in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(raw)
        section = raw[match.end():end]
        section = section.split("## Glossary", 1)[0].split("## Editorial review", 1)[0]
        source = re.search(r"\*Original Scripture \[([^]]+)\]\((https://ebible\.org/[^)]+)\)\.\*", section)
        if not source:
            raise ValueError(f"Missing official source link: {book} {match.group(1)}")
        prose = section[:source.start()].strip()
        paragraphs = [p.replace("\n", " ").strip() for p in re.split(r"\n\s*\n", prose) if p.strip()]
        chapters.append({"number": int(match.group(1)), "title": match.group(2).strip(), "paragraphs": paragraphs, "source_label": source.group(1), "source_url": source.group(2)})
    glossary = []
    for term, chapter, meaning in re.findall(r"^\| ([^|]+?) \| (\d+) \| ([^|]+?) \|$", raw, re.M):
        if term.strip().lower() in {"expression", "term"}:
            continue
        glossary.append({"term": term.strip(), "chapter": int(chapter), "meaning": meaning.strip()})
    review_part = raw.split("## Editorial review", 1)
    reviewed = [int(n) for n in re.findall(r"^\| (\d+) \| (?:Compared with |\d+:)", review_part[1], re.M)] if len(review_part) == 2 else []
    return {"book": book, "chapters": chapters, "glossary": glossary, "reviewed": reviewed, "path": str(path)}


def mark_terms(text: str, entries: list[dict], used: set[str]) -> str:
    escaped = inline(text)
    for entry in sorted(entries, key=lambda e: len(e["term"]), reverse=True):
        term = entry["term"]
        key = term.casefold()
        if key in used:
            continue
        pattern = re.compile(r"(?<![\w-])(" + re.escape(html.escape(term)) + r")(?![\w-])", re.I)
        escaped, count = pattern.subn(lambda m: f'<a class="vocab" href="glossary.xhtml#{slug(term)}">{m.group(1)}</a>', escaped, count=1)
        if count:
            used.add(key)
    return escaped


def page(title: str, filename: str, body: str) -> epub.EpubHtml:
    item = epub.EpubHtml(title=title, file_name=filename, lang="en")
    item.content = f'<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style/book.css"/></head><body>{body}</body></html>'
    item.add_item(STYLE)
    return item


def build() -> Path:
    manuscripts = [parse(p) for p in MANUSCRIPTS.glob("*.md")]
    order = {name: i for i, name in enumerate(BOOK_ORDER)}
    manuscripts.sort(key=lambda m: order.get(m["book"], 999))
    if any(m["book"] not in order for m in manuscripts):
        raise ValueError("Unknown book name in manuscripts")
    chapter_count = sum(len(m["chapters"]) for m in manuscripts)
    reviewed_count = sum(len(m["reviewed"]) for m in manuscripts)
    for manuscript in manuscripts:
        actual = [c["number"] for c in manuscript["chapters"]]
        if actual != manuscript["reviewed"]:
            raise ValueError(f"Review rows do not match chapters in {manuscript['book']}: {actual} != {manuscript['reviewed']}")
        expected = list(range(1, CHAPTER_COUNTS[manuscript["book"]] + 1))
        if actual != expected:
            raise ValueError(f"Incomplete canonical manuscript for {manuscript['book']}: {actual} != {expected}")
    complete = chapter_count == EXPECTED_CHAPTERS and reviewed_count == EXPECTED_CHAPTERS and len(manuscripts) == 66
    output = GENERATED / (FINAL_NAME if complete else PREVIEW_NAME)
    GENERATED.mkdir(exist_ok=True)

    book = epub.EpubBook()
    book.set_identifier("the-bible-retold-complete" if complete else "the-bible-retold-editorial-preview")
    book.set_title("THE BIBLE, RETOLD — A Literary Adaptation for Young English Readers" + ("" if complete else " (Editorial Preview)"))
    book.set_language("en-US")
    book.add_author("Shemin Official editorial project")
    book.add_metadata("DC", "description", "Educational literary adaptation for young English readers; not a replacement for Scripture.")
    book.add_item(STYLE)

    notice = page("Start Here", "start.xhtml", f'<p class="eyebrow">Faith · Literature · English</p><h1>THE BIBLE, RETOLD</h1><h2>A Literary Adaptation for Young English Readers</h2><div class="notice"><p>This is an educational literary adaptation, not a new revelation, an official translation, or a replacement for the Bible. Compare every retelling with Scripture.</p></div><p>This build contains {chapter_count} fully drafted and source-compared chapters. It is {"the complete edition" if complete else "an editorial work in progress"}.</p>')
    book.add_item(notice)
    spine = ["nav", notice]
    toc = [epub.Link("start.xhtml", "Start Here", "start")]
    all_glossary = {}

    for manuscript in manuscripts:
        chapter_links = []
        terms = manuscript["glossary"]
        for chapter in manuscript["chapters"]:
            filename = f'{slug(manuscript["book"])}-{chapter["number"]:03d}.xhtml'
            used = set()
            paras = "".join(f'<p>{mark_terms(p, terms, used)}</p>' for p in chapter["paragraphs"])
            body = f'<p class="eyebrow">{html.escape(manuscript["book"])}</p><h1>Chapter {chapter["number"]} — {html.escape(chapter["title"])}</h1>{paras}<p class="meta">Original Scripture: <a href="{html.escape(chapter["source_url"], quote=True)}">{html.escape(chapter["source_label"])}</a></p>'
            item = page(f'{manuscript["book"]} {chapter["number"]} — {chapter["title"]}', filename, body)
            book.add_item(item); spine.append(item); chapter_links.append(item)
        toc.append((epub.Section(manuscript["book"]), chapter_links))
        for entry in terms:
            all_glossary.setdefault(entry["term"].casefold(), (entry, manuscript["book"]))

    glossary_body = ['<p class="eyebrow">Language help</p><h1>Interactive Glossary</h1><p>Use your reader’s Back button after opening a definition.</p><dl>']
    for _, (entry, source_book) in sorted(all_glossary.items()):
        glossary_body.append(f'<dt id="{slug(entry["term"])}">{html.escape(entry["term"])}</dt><dd>{html.escape(entry["meaning"])} <span class="meta">First selected in {html.escape(source_book)} {entry["chapter"]}.</span></dd>')
    glossary_body.append('</dl>')
    glossary = page("Interactive Glossary", "glossary.xhtml", "".join(glossary_body))
    book.add_item(glossary); spine.append(glossary); toc.append(epub.Link("glossary.xhtml", "Interactive Glossary", "glossary"))
    book.toc = tuple(toc); book.spine = spine
    book.add_item(epub.EpubNcx()); book.add_item(epub.EpubNav())
    epub.write_epub(str(output), book, {"epub3_pages": False})
    report = {"books": len(manuscripts), "expected_books": 66, "chapters": chapter_count, "expected_chapters": EXPECTED_CHAPTERS, "remaining_chapters": EXPECTED_CHAPTERS - chapter_count, "reviewed_chapters": reviewed_count, "glossary_terms": len(all_glossary), "complete": complete, "output": str(output)}
    (GENERATED / "retelling-coverage.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return output


STYLE = epub.EpubItem(uid="style_book", file_name="style/book.css", media_type="text/css", content=CSS.encode())

if __name__ == "__main__":
    build()
