#!/usr/bin/env python3
"""Copy English pages from kakobuysspreadsheets and adapt URLs/utm/hreflang for kakobuy.pt."""
from __future__ import annotations

import re
from pathlib import Path

SS = Path(__file__).resolve().parent.parent / "kakobuysspreadsheets"
OUT = Path(__file__).resolve().parent

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


def strip_gtag(html: str) -> str:
    """Remove GA4 + Ads loader: HTML comment, async gtm/js script, and inline gtag config."""
    return re.sub(
        r"\n\s*<!-- Google tag \(gtag\.js\): GA4 \+ Google Ads -->\s*\n"
        r"\s*<script async src=\"https://www\.googletagmanager\.com/gtag/js\?id=[^\"]+\"></script>\s*\n"
        r"\s*<script>.*?</script>",
        "\n",
        html,
        count=1,
        flags=re.DOTALL,
    )


def swap_domain(html: str) -> str:
    html = html.replace("https://kakobuysspreadsheets.com", "https://kakobuy.pt")
    html = html.replace("utm_source=kakobuysspreadsheets", "utm_source=kakobuy.pt")
    return html


def hreflang_block(basename: str) -> str:
    if basename == "index.html":
        en_url, pt_url = "https://kakobuy.pt/", "https://kakobuy.pt/pt/"
    else:
        en_url = f"https://kakobuy.pt/{basename}"
        pt_url = f"https://kakobuy.pt/pt/{basename}"
    return (
        f'    <link rel="alternate" hreflang="en" href="{en_url}" />\n'
        f'    <link rel="alternate" hreflang="pt-PT" href="{pt_url}" />\n'
        f'    <link rel="alternate" hreflang="x-default" href="{en_url}" />\n'
    )


def replace_hreflang(html: str, basename: str) -> str:
    return re.sub(
        r"<link rel=\"alternate\" hreflang=\"en\" href=\"[^\"]+\" />\s*\n"
        r"(?:\s*<link rel=\"alternate\" hreflang=\"[^\"]+\" href=\"[^\"]+\" />\s*\n)+",
        hreflang_block(basename),
        html,
        count=1,
    )


def replace_lang_switcher(html: str, basename: str) -> str:
    pt_href = "/pt/" if basename == "index.html" else f"/pt/{basename}"
    en_href = "/" if basename == "index.html" else f"/{basename}"
    replacement = (
        f'        <div class="header-end">\n'
        f'          <div class="header-cta">\n'
        f'            <a class="btn btn-primary" href="https://maisonlooks.com/?utm_source=kakobuy.pt">Open hub</a>\n'
        f"          </div>\n"
        f'          <nav class="header-lang" aria-label="Language">\n'
        f'            <a href="{en_href}" hreflang="en" aria-current="page">EN</a>\n'
        f'            <span class="header-lang-sep" aria-hidden="true">·</span>\n'
        f'            <a href="{pt_href}" hreflang="pt-PT">PT</a>\n'
        f"          </nav>\n"
        f"        </div>"
    )
    html2 = re.sub(
        r'<div class="header-end">\s*<div class="header-cta">.*?</div>\s*<nav class="language-switcher has-lang.*?</nav>\s*</div>',
        replacement,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if html2 == html:
        raise RuntimeError("language-switcher block not found — check template header")
    return html2


def fix_faq_corporate_question(html: str) -> str:
    """Align FAQ wording with kakobuy.pt property."""
    return html.replace(
        '"name": "Is kakobuysspreadsheets.com run by Kakobuy corporate?",',
        '"name": "Is kakobuy.pt run by Kakobuy corporate?",',
    ).replace(
        "keep kakobuysspreadsheets.com for explainers",
        "keep kakobuy.pt for explainers",
    )


def process_file(basename: str) -> None:
    src = SS / basename
    text = src.read_text(encoding="utf-8")
    text = strip_gtag(text)
    text = swap_domain(text)
    text = replace_hreflang(text, basename)
    text = replace_lang_switcher(text, basename)
    text = fix_faq_corporate_question(text)
    (OUT / basename).write_text(text, encoding="utf-8")
    print("wrote", basename)


def main() -> None:
    for f in FILES:
        process_file(f)


if __name__ == "__main__":
    main()
