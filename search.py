"""
search.py - Information Retrieval Module
Fetches real, publicly available competitor updates via Google News RSS and Hacker News Algolia API.
Handles date filtering, concurrent requests, network timeouts, and explicitly labeled fallback sample data.
"""

import re
import html
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    title: str
    link: str
    source: str
    published_at: Optional[datetime] = None
    snippet: str = ""
    company: str
    source_type: str = "news"  # 'news', 'hacker_news', or 'sample_fallback'
    is_sample_data: bool = False


class SearchEngine:
    """
    Retrieves public news and developer updates for specified competitors.
    """

    def __init__(self, timeout: int = 10, max_workers: int = 8):
        self.timeout = timeout
        self.max_workers = max_workers
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, application/json, text/html, */*",
        }

    def _clean_snippet(self, raw_html: str) -> str:
        """Strips HTML tags and decodes entities."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        return html.unescape(soup.get_text(separator=" ", strip=True))

    def _fetch_bytes(self, url: str) -> Optional[bytes]:
        """Safely fetches remote content with timeout and user-agent headers."""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read()
        except Exception:
            return None

    def search_google_news(self, company: str, days: int = 14) -> List[RawArticle]:
        """
        Retrieves recent verified news articles from Google News RSS.
        """
        articles: List[RawArticle] = []
        encoded = urllib.parse.quote(f'"{company}"')
        url = f"https://news.google.com/rss/search?q={encoded}+when:{days}d&hl=en-US&gl=US&ceid=US:en"

        content = self._fetch_bytes(url)
        if not content:
            # Fallback query without the when: operator if blocked
            url_fallback = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
            content = self._fetch_bytes(url_fallback)

        if not content:
            return articles

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            root = ET.fromstring(content)
            for item in root.findall("./channel/item"):
                title_node = item.find("title")
                link_node = item.find("link")
                pub_node = item.find("pubDate")
                desc_node = item.find("description")
                source_node = item.find("source")

                if title_node is None or not title_node.text:
                    continue

                full_title = title_node.text.strip()
                source_name = "Google News"
                if source_node is not None and source_node.text:
                    source_name = source_node.text.strip()
                elif " - " in full_title:
                    parts = full_title.rsplit(" - ", 1)
                    full_title = parts[0].strip()
                    source_name = parts[1].strip()

                link = link_node.text.strip() if link_node is not None and link_node.text else ""
                snippet = self._clean_snippet(desc_node.text) if desc_node is not None and desc_node.text else ""

                pub_date = None
                if pub_node is not None and pub_node.text:
                    try:
                        pub_date = date_parser.parse(pub_node.text)
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                # Strict date cutoff filtering
                if pub_date and pub_date < cutoff:
                    continue

                articles.append(
                    RawArticle(
                        title=full_title,
                        link=link,
                        source=source_name,
                        published_at=pub_date,
                        snippet=snippet,
                        company=company,
                        source_type="news",
                        is_sample_data=False
                    )
                )
        except Exception:
            pass

        return articles

    def search_hacker_news(self, company: str, days: int = 14) -> List[RawArticle]:
        """
        Retrieves real-time developer releases and community signals via Hacker News Algolia API.
        """
        articles: List[RawArticle] = []
        cutoff_epoch = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        encoded = urllib.parse.quote(company)
        url = (
            f"https://hn.algolia.com/api/v1/search?"
            f"query={encoded}&tags=story&numericFilters=created_at_i>{cutoff_epoch}"
            f"&hitsPerPage=20"
        )

        content = self._fetch_bytes(url)
        if not content:
            return articles

        try:
            data = json.loads(content.decode("utf-8"))
            for hit in data.get("hits", []):
                title = hit.get("title")
                if not title:
                    continue

                item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                created_at_str = hit.get("created_at")
                pub_date = None
                if created_at_str:
                    try:
                        pub_date = date_parser.parse(created_at_str)
                    except Exception:
                        pass

                points = hit.get("points") or 0
                comments = hit.get("num_comments") or 0
                snippet = f"Hacker News community discussion ({points} upvotes, {comments} comments)."

                articles.append(
                    RawArticle(
                        title=title.strip(),
                        link=item_url,
                        source="Hacker News",
                        published_at=pub_date,
                        snippet=snippet,
                        company=company,
                        source_type="hacker_news",
                        is_sample_data=False
                    )
                )
        except Exception:
            pass

        return articles

    def get_explicit_sample_data(self, company: str, days: int = 14) -> List[RawArticle]:
        """
        Returns explicitly labeled benchmark data for offline evaluation when external networks are unavailable.
        Never presented as live intelligence.
        """
        now = datetime.now(timezone.utc)
        sample_database: Dict[str, List[Dict]] = {
            "OpenAI": [
                {
                    "title": "[DEMO SAMPLE] OpenAI Releases o3-mini Reasoning Model for Math and Coding Workflows",
                    "link": "https://openai.com/index/o3-mini",
                    "source": "OpenAI Blog (Demo Record)",
                    "days_ago": 2,
                    "snippet": "OpenAI announces the availability of o3-mini, providing specialized step-by-step reasoning."
                },
                {
                    "title": "[DEMO SAMPLE] OpenAI Expands Operator Autonomous Web Agent Preview to Plus Users",
                    "link": "https://openai.com/index/operator-preview",
                    "source": "TechCrunch (Demo Record)",
                    "days_ago": 5,
                    "snippet": "OpenAI launches preview of Operator, allowing automated browser navigation for complex tasks."
                }
            ],
            "Anthropic": [
                {
                    "title": "[DEMO SAMPLE] Anthropic Introduces Claude 3.7 Sonnet Hybrid Reasoning Architecture",
                    "link": "https://anthropic.com/news/claude-3-7-sonnet",
                    "source": "Anthropic Research (Demo Record)",
                    "days_ago": 3,
                    "snippet": "Anthropic releases Claude 3.7 Sonnet with toggleable thinking time and enhanced coding benchmarks."
                },
                {
                    "title": "[DEMO SAMPLE] Anthropic Cuts Batch Inference Pricing and Adds Prompt Caching Discounts",
                    "link": "https://anthropic.com/pricing",
                    "source": "VentureBeat (Demo Record)",
                    "days_ago": 6,
                    "snippet": "Anthropic reduces enterprise token costs by 50% for asynchronous batch jobs."
                }
            ],
            "Cursor": [
                {
                    "title": "[DEMO SAMPLE] Cursor Announces Background Agent Feature for Asynchronous Code Editing",
                    "link": "https://cursor.com/blog/background-agent",
                    "source": "Cursor Changelog (Demo Record)",
                    "days_ago": 1,
                    "snippet": "Cursor releases background agents capable of multi-file refactoring while developer continues typing."
                }
            ],
            "Perplexity AI": [
                {
                    "title": "[DEMO SAMPLE] Perplexity AI Launches Shopping Hub with One-Click Buy Integration",
                    "link": "https://perplexity.ai/hub/shopping",
                    "source": "The Verge (Demo Record)",
                    "days_ago": 4,
                    "snippet": "Perplexity partners with top retailers to allow seamless purchase recommendations directly in chat."
                }
            ],
            "Mistral AI": [
                {
                    "title": "[DEMO SAMPLE] Mistral AI Releases Mistral Large 3 with 128k Multilingual Context",
                    "link": "https://mistral.ai/news/mistral-large-3",
                    "source": "Mistral AI Blog (Demo Record)",
                    "days_ago": 7,
                    "snippet": "Mistral unveils its new frontier open-weights model optimized for multilingual enterprise tasks."
                }
            ]
        }

        records = sample_database.get(company, [
            {
                "title": f"[DEMO SAMPLE] {company} Announces Strategic Product Roadmap and Enterprise Expansion",
                "link": f"https://example.com/{company.lower()}-update",
                "source": "Industry Wire (Demo Record)",
                "days_ago": 3,
                "snippet": f"Representative benchmark record for evaluating {company} intelligence pipeline when offline."
            }
        ])

        results: List[RawArticle] = []
        for r in records:
            if r["days_ago"] <= days:
                pub = now - timedelta(days=r["days_ago"])
                results.append(
                    RawArticle(
                        title=r["title"],
                        link=r["link"],
                        source=r["source"],
                        published_at=pub,
                        snippet=r["snippet"],
                        company=company,
                        source_type="sample_fallback",
                        is_sample_data=True
                    )
                )
        return results

    def retrieve_competitor_updates(
        self,
        company: str,
        days: int = 14,
        force_sample_data: bool = False
    ) -> List[RawArticle]:
        """
        Retrieves all updates for a single competitor across all connected search feeds.
        """
        if force_sample_data:
            return self.get_explicit_sample_data(company, days=days)

        results: List[RawArticle] = []
        gnews = self.search_google_news(company, days=days)
        hn = self.search_hacker_news(company, days=days)
        results.extend(gnews)
        results.extend(hn)

        # If live retrieval yielded 0 results due to network failure/firewall,
        # note: do not fake data silently. Caller can opt into sample data explicitly.
        return results

    def retrieve_all(
        self,
        companies: List[str],
        days: int = 14,
        force_sample_data: bool = False
    ) -> Dict[str, List[RawArticle]]:
        """
        Retrieves updates for 5-10 competitors in parallel using thread pooling.
        """
        data: Dict[str, List[RawArticle]] = {c: [] for c in companies}
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(companies) * 2)) as pool:
            futures = {
                pool.submit(self.retrieve_competitor_updates, comp, days, force_sample_data): comp
                for comp in companies
            }
            for fut in as_completed(futures):
                comp = futures[fut]
                try:
                    data[comp] = fut.result()
                except Exception:
                    data[comp] = []
        return data
