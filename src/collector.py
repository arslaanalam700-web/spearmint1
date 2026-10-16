"""
Multi-source Data Collector for Competitor Updates.
Ingests from Google News RSS and Hacker News Algolia API concurrently.
"""

import re
import html
import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from src.models import RawArticle


class CompetitorDataCollector:
    def __init__(self, request_timeout: int = 12, max_workers: int = 8):
        self.request_timeout = request_timeout
        self.max_workers = max_workers
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

    def _clean_html_snippet(self, raw_html: str) -> str:
        """Strips HTML tags and unescapes entities."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return html.unescape(text)

    def _fetch_url(self, url: str) -> Optional[bytes]:
        """Performs HTTP GET with standard headers and timeout."""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.request_timeout) as response:
                return response.read()
        except Exception:
            return None

    def fetch_google_news(self, company: str, days: int = 14) -> List[RawArticle]:
        """
        Fetches recent Google News articles via RSS.
        """
        articles: List[RawArticle] = []
        
        # Primary query: Broad & high signal
        encoded_query = urllib.parse.quote(f'"{company}"')
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}+when:{days}d&hl=en-US&gl=US&ceid=US:en"
        
        content = self._fetch_url(rss_url)
        if not content:
            # Fallback without the `when:Xd` operator if Google News blocks the operator
            fallback_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            content = self._fetch_url(fallback_url)
            
        if not content:
            return articles

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            root = ET.fromstring(content)
            items = root.findall("./channel/item")
            for item in items:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_elem = item.find("pubDate")
                desc_elem = item.find("description")
                source_elem = item.find("source")

                if title_elem is None or not title_elem.text:
                    continue

                full_title = title_elem.text.strip()
                # Google News RSS title format is typically: "Headline - Source Name"
                source_name = "Google News"
                if source_elem is not None and source_elem.text:
                    source_name = source_elem.text.strip()
                elif " - " in full_title:
                    parts = full_title.rsplit(" - ", 1)
                    full_title = parts[0].strip()
                    source_name = parts[1].strip()

                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                snippet = self._clean_html_snippet(desc_elem.text) if desc_elem is not None and desc_elem.text else ""

                pub_date = None
                if pub_elem is not None and pub_elem.text:
                    try:
                        pub_date = date_parser.parse(pub_elem.text)
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                # Filter by cutoff date if available
                if pub_date and pub_date < cutoff_date:
                    continue

                articles.append(
                    RawArticle(
                        title=full_title,
                        link=link,
                        source=source_name,
                        published_at=pub_date,
                        snippet=snippet,
                        company=company
                    )
                )
        except Exception:
            pass

        return articles

    def fetch_hacker_news(self, company: str, days: int = 14) -> List[RawArticle]:
        """
        Fetches high-signal developer updates from Hacker News Algolia Search API.
        """
        articles: List[RawArticle] = []
        cutoff_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        
        encoded_query = urllib.parse.quote(company)
        hn_url = (
            f"https://hn.algolia.com/api/v1/search?"
            f"query={encoded_query}&tags=story&numericFilters=created_at_i>{cutoff_timestamp}"
            f"&hitsPerPage=20"
        )

        content = self._fetch_url(hn_url)
        if not content:
            return articles

        try:
            data = json.loads(content.decode("utf-8"))
            hits = data.get("hits", [])
            for hit in hits:
                title = hit.get("title")
                if not title:
                    continue

                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                created_at_str = hit.get("created_at")
                pub_date = None
                if created_at_str:
                    try:
                        pub_date = date_parser.parse(created_at_str)
                    except Exception:
                        pass

                points = hit.get("points") or 0
                num_comments = hit.get("num_comments") or 0
                snippet = f"Hacker News discussion ({points} points, {num_comments} comments)."

                articles.append(
                    RawArticle(
                        title=title.strip(),
                        link=url,
                        source="Hacker News",
                        published_at=pub_date,
                        snippet=snippet,
                        company=company
                    )
                )
        except Exception:
            pass

        return articles

    def collect_for_company(self, company: str, days: int = 14) -> List[RawArticle]:
        """
        Collects from all sources for a single company.
        """
        all_articles: List[RawArticle] = []
        gnews = self.fetch_google_news(company, days=days)
        hn = self.fetch_hacker_news(company, days=days)
        all_articles.extend(gnews)
        all_articles.extend(hn)
        return all_articles

    def collect_all(self, companies: List[str], days: int = 14) -> Dict[str, List[RawArticle]]:
        """
        Concurrent multi-company collection across all sources.
        """
        results: Dict[str, List[RawArticle]] = {comp: [] for comp in companies}
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(companies) * 2)) as executor:
            future_to_company = {
                executor.submit(self.collect_for_company, comp, days): comp
                for comp in companies
            }
            for future in as_completed(future_to_company):
                comp = future_to_company[future]
                try:
                    articles = future.result()
                    results[comp] = articles
                except Exception:
                    results[comp] = []
        return results
