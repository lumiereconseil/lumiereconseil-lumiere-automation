#!/usr/bin/env python3
"""Public health/SEO/compliance monitor for rakutenmobile.pages.dev."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path


BASE_URL = "https://rakutenmobile.pages.dev/"
SITEMAP_URL = urllib.parse.urljoin(BASE_URL, "sitemap.xml")
ROBOTS_URL = urllib.parse.urljoin(BASE_URL, "robots.txt")
REFERRAL_URL = "https://r10.to/h90H6D"
OFFICIAL_URL = "https://network.mobile.rakuten.co.jp/campaign/referral/"
LOTTERY_URL = "https://network.mobile.rakuten.co.jp/campaign/referral-one-million/"
INDEXNOW_URL = "https://api.indexnow.org/indexnow"
INDEXNOW_KEY = "7f4c96da748191bab16cd5ad7d8e30"
REQUIRED_LANGS = {"ja", "en", "hi", "my", "zh-Hans", "x-default"}
FALLBACK_PATHS = [
    "/", "/en/", "/hi/", "/my/", "/zh/", "/mnp/", "/new-number/",
    "/campaign-20260830/", "/campaign-current/", "/share/", "/esim/",
    "/foreign-residents/", "/mnp-one-stop/", "/rakuten-mobile-referral/",
    "/application-checklist/", "/points-schedule/", "/rakuten-link-condition/",
    "/data-type-not-eligible/", "/iphone-esim/", "/mnp-opening-time/",
]


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.links: list[str] = []
        self.hreflang: set[str] = set()
        self.canonical = ""
        self.jsonld: list[str] = []
        self._jsonld = False
        self._jsonld_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "title":
            self._in_title = True
        elif tag.lower() == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "").strip()
        elif tag.lower() == "link":
            rel = a.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = a.get("href", "").strip()
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang.add(a["hreflang"])
        elif tag.lower() == "a" and a.get("href"):
            self.links.append(a["href"].strip())
        elif tag.lower() == "script" and a.get("type", "").lower() == "application/ld+json":
            self._jsonld = True
            self._jsonld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "script" and self._jsonld:
            self.jsonld.append("".join(self._jsonld_parts).strip())
            self._jsonld = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._jsonld:
            self._jsonld_parts.append(data)
        elif data.strip():
            self.text_parts.append(data.strip())


@dataclass
class FetchResult:
    url: str
    status: int
    final_url: str
    content_type: str
    body: str
    elapsed_ms: int


def fetch(url: str, *, method: str = "GET", data: bytes | None = None,
          headers: dict[str, str] | None = None) -> FetchResult:
    merged_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xml,text/plain,application/json;q=0.9,*/*;q=0.8",
    }
    if headers:
        merged_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=merged_headers, method=method)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(3_000_000)
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="replace")
            return FetchResult(
                url=url,
                status=response.status,
                final_url=response.geturl(),
                content_type=response.headers.get("Content-Type", ""),
                body=body,
                elapsed_ms=round((time.monotonic() - started) * 1000),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read(500_000).decode("utf-8", errors="replace")
        return FetchResult(url, exc.code, exc.geturl(), exc.headers.get("Content-Type", ""), body,
                           round((time.monotonic() - started) * 1000))


def parse_sitemap(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    urls = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            urls.append(element.text.strip())
    return list(dict.fromkeys(urls))


def jsonld_types(doc: DocumentParser) -> set[str]:
    found: set[str] = set()
    for raw in doc.jsonld:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            found.add("INVALID_JSON_LD")
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if isinstance(node, dict) and isinstance(node.get("@graph"), list):
                nodes.extend(node["@graph"])
            if isinstance(node, dict):
                kind = node.get("@type")
                if isinstance(kind, list):
                    found.update(str(x) for x in kind)
                elif kind:
                    found.add(str(kind))
    return found


def audit_page(result: FetchResult) -> tuple[dict, list[str], list[str], str]:
    errors: list[str] = []
    warnings: list[str] = []
    if result.status != 200:
        snippet = re.sub(r"\s+", " ", result.body).strip()[:240]
        errors.append(f"HTTP {result.status}: {result.url} response={snippet!r}")
        return {
            "url": result.url,
            "status": result.status,
            "final_url": result.final_url,
            "response_snippet": snippet,
        }, errors, warnings, ""
    if "text/html" not in result.content_type.lower():
        errors.append(f"HTMLでないContent-Type: {result.url} ({result.content_type})")
    doc = DocumentParser()
    doc.feed(result.body)
    path = urllib.parse.urlparse(result.url).path
    if not doc.title.strip():
        errors.append(f"title欠落: {result.url}")
    if not doc.meta.get("description"):
        errors.append(f"description欠落: {result.url}")
    if not doc.canonical:
        errors.append(f"canonical欠落: {result.url}")
    else:
        canonical_host = urllib.parse.urlparse(doc.canonical).netloc
        if canonical_host != "rakutenmobile.pages.dev":
            errors.append(f"canonicalホスト不一致: {result.url} -> {doc.canonical}")
    for key in ("og:title", "og:description", "og:url", "og:image", "twitter:card"):
        if not doc.meta.get(key):
            errors.append(f"{key}欠落: {result.url}")
    if path in {"/", "/en/", "/hi/", "/my/", "/zh/"}:
        missing = REQUIRED_LANGS - doc.hreflang
        if missing:
            errors.append(f"hreflang欠落 {sorted(missing)}: {result.url}")
    types = jsonld_types(doc)
    if "INVALID_JSON_LD" in types:
        errors.append(f"JSON-LD構文エラー: {result.url}")
    if path in {"/", "/rakuten-mobile-referral/"} and "FAQPage" not in types:
        warnings.append(f"FAQPage未検出: {result.url}")
    if result.elapsed_ms > 4000:
        warnings.append(f"応答遅延 {result.elapsed_ms}ms: {result.url}")
    record = {
        "url": result.url,
        "status": result.status,
        "final_url": result.final_url,
        "elapsed_ms": result.elapsed_ms,
        "title": doc.title.strip(),
        "description": doc.meta.get("description", ""),
        "canonical": doc.canonical,
        "hreflang": sorted(doc.hreflang),
        "jsonld_types": sorted(types),
    }
    text = " ".join(doc.text_parts)
    return record, errors, warnings, text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit-indexnow", action="store_true")
    parser.add_argument("--report", default="rakuten-monitor-report.json")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, object] = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": BASE_URL,
    }

    sitemap = fetch(SITEMAP_URL)
    report["sitemap_status"] = sitemap.status
    if sitemap.status != 200:
        errors.append(f"sitemap.xml HTTP {sitemap.status}")
        urls = [urllib.parse.urljoin(BASE_URL, path.lstrip("/")) for path in FALLBACK_PATHS]
    else:
        try:
            urls = parse_sitemap(sitemap.body)
        except ET.ParseError as exc:
            errors.append(f"sitemap.xml XMLエラー: {exc}")
            urls = [urllib.parse.urljoin(BASE_URL, path.lstrip("/")) for path in FALLBACK_PATHS]
    urls = list(dict.fromkeys([BASE_URL] + urls))
    foreign = [u for u in urls if urllib.parse.urlparse(u).netloc != "rakutenmobile.pages.dev"]
    if foreign:
        errors.append(f"sitemapに外部URL: {foreign}")
    urls = [u for u in urls if urllib.parse.urlparse(u).netloc == "rakutenmobile.pages.dev"]
    report["url_count"] = len(urls)

    robots = fetch(ROBOTS_URL)
    report["robots_status"] = robots.status
    if robots.status != 200:
        errors.append(f"robots.txt HTTP {robots.status}")
    else:
        if re.search(r"(?im)^\s*disallow:\s*/\s*$", robots.body):
            errors.append("robots.txtが全体をDisallow")
        if SITEMAP_URL.lower() not in robots.body.lower():
            errors.append("robots.txtにSitemap指定なし")

    page_records = []
    site_text_parts = []
    for url in urls:
        try:
            result = fetch(url)
            record, page_errors, page_warnings, page_text = audit_page(result)
            page_records.append(record)
            errors.extend(page_errors)
            warnings.extend(page_warnings)
            site_text_parts.append(page_text)
        except Exception as exc:  # continue auditing remaining pages
            errors.append(f"取得例外 {url}: {type(exc).__name__}: {exc}")
    report["pages"] = page_records

    try:
        referral = fetch(REFERRAL_URL)
        report["referral"] = {"status": referral.status, "final_url": referral.final_url}
        host = urllib.parse.urlparse(referral.final_url).netloc.lower()
        if referral.status != 200 or not (host.endswith("rakuten.co.jp") or host.endswith("rakuten.com")):
            errors.append(f"紹介URL到達先異常: HTTP {referral.status} {referral.final_url}")
    except Exception as exc:
        errors.append(f"紹介URL取得例外: {exc}")

    official = fetch(OFFICIAL_URL)
    lottery = fetch(LOTTERY_URL)
    report["official"] = {"referral_status": official.status, "lottery_status": lottery.status}
    official_text = re.sub(r"\s+", " ", official.body)
    site_text = re.sub(r"\s+", " ", " ".join(site_text_parts))
    required_terms = ["7,000", "13,000", "10,000", "翌々月", "10秒", "データタイプ"]
    for term in required_terms:
        if term not in official_text:
            warnings.append(f"公式ページで条件語を検出できず（要手動確認）: {term}")
        if term not in site_text:
            errors.append(f"サイト本文に現行条件語なし: {term}")
    if "2026年8月30日" in lottery.body or "2026/08/30" in lottery.body:
        for term in ("最大10万", "8月30日"):
            if term not in site_text:
                errors.append(f"開催中キャンペーン情報なし: {term}")

    if args.submit_indexnow and urls:
        payload = json.dumps({
            "host": "rakutenmobile.pages.dev",
            "key": INDEXNOW_KEY,
            "keyLocation": f"{BASE_URL}{INDEXNOW_KEY}.txt",
            "urlList": urls,
        }, ensure_ascii=False).encode("utf-8")
        try:
            sent = fetch(INDEXNOW_URL, method="POST", data=payload,
                         headers={"Content-Type": "application/json; charset=utf-8"})
            report["indexnow"] = {"status": sent.status, "response": sent.body[:500]}
            if sent.status not in {200, 202}:
                errors.append(f"IndexNow送信失敗: HTTP {sent.status}")
        except Exception as exc:
            errors.append(f"IndexNow送信例外: {exc}")

    report["errors"] = list(dict.fromkeys(errors))
    report["warnings"] = list(dict.fromkeys(warnings))
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"checked={len(urls)} errors={len(report['errors'])} warnings={len(report['warnings'])}")
    for item in report["errors"]:
        print(f"ERROR: {item}")
    for item in report["warnings"]:
        print(f"WARN: {item}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
