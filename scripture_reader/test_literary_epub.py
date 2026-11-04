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


def test_verified_videos_use_allowed_https_hosts_and_are_embedded():
    allowed_hosts = {"www.youtube.com", "youtube.com", "bibleproject.com", "www.bibleproject.com", "www.thechosen.tv", "thechosen.tv"}
    videos = [video for manuscript in manuscripts() for video in manuscript["videos"]]
    assert videos, "At least one independently verified video is required"
    from urllib.parse import urlparse
    assert all(urlparse(video["url"]).scheme == "https" and urlparse(video["url"]).hostname in allowed_hosts for video in videos)
    output = builder.build()
    with zipfile.ZipFile(output) as archive:
        content = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist() if name.endswith(".xhtml"))
        for video in videos:
            assert video["url"].replace("&", "&amp;") in content
            assert video["note"] in content


def test_accessible_vector_cover_is_packaged():
    output = builder.build()
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        cover_svg = next((name for name in names if name.endswith("/cover.svg")), None)
        cover_page = next((name for name in names if name.endswith("/cover.xhtml")), None)
        assert cover_svg is not None
        assert cover_page is not None
        svg = archive.read(cover_svg).decode("utf-8")
        assert "<title id=\"cover-title\">The Bible, Retold</title>" in svg
        assert "<desc id=\"cover-desc\">" in svg

def test_coverage_report_partitions_all_canonical_books():
    builder.build()
    report = json.loads((ROOT / "generated" / "retelling-coverage.json").read_text())
    completed = report["completed_books"]
    missing = report["missing_books"]
    assert len(completed) + len(missing) == 66
    assert set(completed).isdisjoint(missing)
    assert completed == [name for name in builder.BOOK_ORDER if name in completed]
    assert missing == [name for name in builder.BOOK_ORDER if name in missing]
    assert set(completed) | set(missing) == set(builder.BOOK_ORDER)
