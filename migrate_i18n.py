#!/usr/bin/env python3
"""One-off: move PT pages to pt/, fix paths/URLs/canonicals, inject hreflang + lang switcher."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = [
    "index.html",
    "guides.html",
    "contact.html",
    "news.html",
    "spreadsheet.html",
    "kakobuy-spreadsheet-qc.html",
    "kakobuy-spreadsheet-shipping-weight.html",
    "kakobuy-spreadsheet-dead-links.html",
]

EN_SLUG = {
    "index.html": "/",
    "guides.html": "/guides.html",
    "spreadsheet.html": "/spreadsheet.html",
    "contact.html": "/contact.html",
    "news.html": "/news.html",
    "kakobuy-spreadsheet-qc.html": "/kakobuy-spreadsheet-qc.html",
    "kakobuy-spreadsheet-shipping-weight.html": "/kakobuy-spreadsheet-shipping-weight.html",
    "kakobuy-spreadsheet-dead-links.html": "/kakobuy-spreadsheet-dead-links.html",
}

PT_SLUG = {k: "/pt/" + ("" if k == "index.html" else k) for k in FILES}


def pt_canonical(name: str) -> str:
    base = "https://kakobuy.pt"
    if name == "index.html":
        return f"{base}/pt/"
    return f"{base}/pt/{name}"


def en_url(name: str) -> str:
    base = "https://kakobuy.pt"
    if name == "index.html":
        return f"{base}/"
    return f"{base}/{name}"


LANG_BLOCK_PT = '\n    <link rel="alternate" hreflang="en" href="{en}" />\n    <link rel="alternate" hreflang="pt-PT" href="{pt}" />\n    <link rel="alternate" hreflang="x-default" href="{en}" />'


def inject_after_canonical(content: str, name: str) -> str:
    pt = pt_canonical(name)
    en = en_url(name)
    block = LANG_BLOCK_PT.format(en=en, pt=pt)
    # Remove old single hreflang line if present
    content = re.sub(
        r'\n\s*<link rel="alternate" hreflang="pt-PT" href="https://kakobuy\.pt/[^"]*"\s*/>\s*',
        "\n",
        content,
        count=1,
    )
    return content.replace(
        f'<link rel="canonical" href="{pt}" />',
        f'<link rel="canonical" href="{pt}" />{block}',
        1,
    )


def rewrite_kakobuy_urls_to_pt_prefix(text: str) -> str:
    """https://kakobuy.pt/... → /pt/... except /images and already /pt/."""
    return re.sub(
        r"https://kakobuy\.pt/(?!pt/|images/)",
        "https://kakobuy.pt/pt/",
        text,
    )


def fix_json_ld_urls(content: str, name: str) -> str:
    """Point @id and same-domain URLs that referenced root to /pt/."""
    pt_prefix = "https://kakobuy.pt/pt"
    # website org ids
    content = content.replace(
        '"@id": "https://kakobuy.pt/#website"',
        f'"@id": "{pt_prefix}/#website"',
    )
    content = content.replace(
        '"@id": "https://kakobuy.pt/#org"',
        f'"@id": "{pt_prefix}/#org"',
    )
    content = content.replace('"url": "https://kakobuy.pt/"', f'"url": "{pt_prefix}/"')
    mapping = [
        ("https://kakobuy.pt/kakobuy-spreadsheet-dead-links.html", f"{pt_prefix}/kakobuy-spreadsheet-dead-links.html"),
        ("https://kakobuy.pt/kakobuy-spreadsheet-shipping-weight.html", f"{pt_prefix}/kakobuy-spreadsheet-shipping-weight.html"),
        ("https://kakobuy.pt/kakobuy-spreadsheet-qc.html", f"{pt_prefix}/kakobuy-spreadsheet-qc.html"),
        ("https://kakobuy.pt/spreadsheet.html", f"{pt_prefix}/spreadsheet.html"),
        ("https://kakobuy.pt/contact.html", f"{pt_prefix}/contact.html"),
        ("https://kakobuy.pt/news.html", f"{pt_prefix}/news.html"),
        ("https://kakobuy.pt/guides.html", f"{pt_prefix}/guides.html"),
    ]
    for old, new in mapping:
        content = content.replace(old, new)
    # Home in breadcrumbs often ends with kakobuy.pt/"
    content = content.replace(
        '"item": "https://kakobuy.pt/#',
        f'"item": "{pt_prefix}/#',
    )
    content = content.replace(
        '"item": "https://kakobuy.pt/"',
        f'"item": "{pt_prefix}/"',
    )
    # Article mainEntityOfPage
    content = content.replace("/pt/pt/", "/pt/")
    return content


def asset_paths(content: str) -> str:
    content = content.replace('href="images/', 'href="../images/')
    content = content.replace('src="images/', 'src="../images/')
    content = content.replace('srcset="images/', 'srcset="../images/')
    content = content.replace('href="styles.css"', 'href="../styles.css"')
    return content


def nav_and_links(content: str, basename: str) -> str:
    content = content.replace('<a class="brand" href="/"', '<a class="brand" href="/pt/"')
    content = content.replace('<a class="brand" href="/pt/pt/"', '<a class="brand" href="/pt/"')
    content = content.replace('href="/#', 'href="/pt/#')
    content = re.sub(
        r'(<nav aria-label="Principal">\s*<ul>\s*<li>)<a href="/">',
        r'\1<a href="/pt/">',
        content,
        count=1,
    )
    content = content.replace('href="/">Início</a>', 'href="/pt/">Início</a>')
    content = content.replace('href="/">', 'href="/pt/">')
    return content


def inject_lang_switcher(content: str, basename: str) -> str:
    en_href = EN_SLUG[basename].rstrip("/") or "/"
    if en_href != "/" and not en_href.startswith("/"):
        en_href = "/" + en_href
    pt_href = "/pt/" if basename == "index.html" else f"/pt/{basename}"
    switch = f"""
          <nav class="header-lang" aria-label="Idioma">
            <a href="{en_href}" hreflang="en">EN</a>
            <span class="header-lang-sep" aria-hidden="true">·</span>
            <a href="{pt_href}" hreflang="pt-PT" aria-current="page">PT</a>
          </nav>"""
    return re.sub(
        r'(<div class="header-end">\s*<div class="header-cta">.*?</div>\s*)</div>',
        r"\1" + switch + "\n        </div>",
        content,
        count=1,
        flags=re.DOTALL,
    )


def set_canonical_pt(content: str, name: str) -> str:
    pt = pt_canonical(name)
    # Replace any canonical that still points to non-/pt/ same file
    content = re.sub(
        r'<link rel="canonical" href="https://kakobuy\.pt/[^"]*"\s*/>',
        f'<link rel="canonical" href="{pt}" />',
        content,
        count=1,
    )
    return content


def main() -> None:
    pt_dir = ROOT / "pt"
    pt_dir.mkdir(exist_ok=True)
    for f in FILES:
        src = ROOT / f
        dst = pt_dir / f
        if src.exists():
            shutil.move(str(src), str(dst))
    for name in FILES:
        path = pt_dir / name
        text = path.read_text(encoding="utf-8")
        text = asset_paths(text)
        text = set_canonical_pt(text, name)
        text = rewrite_kakobuy_urls_to_pt_prefix(text)
        text = inject_after_canonical(text, name)
        text = fix_json_ld_urls(text, name)
        text = nav_and_links(text, name)
        text = inject_lang_switcher(text, name)
        path.write_text(text, encoding="utf-8")
    print("Moved and fixed Portuguese pages under pt/")


if __name__ == "__main__":
    main()
