import json
import zipfile
from pathlib import Path

import scripture_reader.build_literary_epub as builder

ROOT = Path(__file__).resolve().parents[1]


def manuscripts():
    return [builder.parse(path) for path in builder.MANUSCRIPTS.glob("*.md")]


def test_canonical_map_is_complete():
    assert builder.BOOK_ORDER == list(builder.CHAPTER_COUNTS)
    assert len(builder.BOOK_ORDER) == 66
    assert len(set(builder.BOOK_ORDER)) == 66
    assert sum(builder.CHAPTER_COUNTS.values()) == 1189


def test_every_manuscript_is_a_complete_book_with_review_evidence():
    for manuscript in manuscripts():
        actual = [chapter["number"] for chapter in manuscript["chapters"]]
        expected = list(range(1, builder.CHAPTER_COUNTS[manuscript["book"]] + 1))
        assert actual == expected, manuscript["book"]
        assert manuscript["reviewed"] == expected, manuscript["book"]
        assert all(chapter["source_url"].startswith("https://ebible.org/engwebp/") for chapter in manuscript["chapters"])


def test_preview_name_cannot_claim_completeness():
    output = builder.build()
    report = json.loads((builder.GENERATED / "retelling-coverage.json").read_text())
    if report["chapters"] < builder.EXPECTED_CHAPTERS or report["books"] < 66:
        assert report["complete"] is False
        assert output.name == builder.PREVIEW_NAME
        assert not (builder.GENERATED / builder.FINAL_NAME).exists()


def test_epub_contains_navigation_glossary_and_dashed_vocabulary_css():
    output = builder.build()
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "EPUB/glossary.xhtml" in names
        assert "EPUB/nav.xhtml" in names
        css = archive.read("EPUB/style/book.css").decode("utf-8")
        glossary = archive.read("EPUB/glossary.xhtml").decode("utf-8")
        chapters = [name for name in names if name.startswith("EPUB/") and name.endswith(".xhtml") and name not in {"EPUB/nav.xhtml", "EPUB/start.xhtml", "EPUB/glossary.xhtml"}]
        chapter_text = "\n".join(archive.read(name).decode("utf-8") for name in chapters)
        assert "text-decoration-style: dashed" in css
        assert 'class="vocab"' in chapter_text
        assert "Interactive Glossary" in glossary
