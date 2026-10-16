"""
Noise Filtering and Deduplication Engine for Competitor Updates.
Clusters related coverage across multiple publications into single high-signal events.
"""

import re
import difflib
import hashlib
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from src.models import RawArticle, ProcessedUpdate
from src.config import NOISE_INDICATORS

# Common English stopwords to ignore in title similarity calculations
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "shall", "should", "may", "might", "must", "can",
    "could", "its", "it", "this", "that", "these", "those", "how", "what", "why",
    "who", "which", "when", "where", "new", "says"
}


class UpdateDeduplicator:
    def __init__(self, similarity_threshold: float = 0.50):
        self.similarity_threshold = similarity_threshold

    def is_noise(self, article: RawArticle) -> bool:
        """
        Determines whether an article is noise, spam, or low-signal clickbait.
        """
        title_lower = article.title.lower()
        snippet_lower = article.snippet.lower()
        combined = f"{title_lower} {snippet_lower}"

        # 1. Filter out known stock/financial noise patterns
        for indicator in NOISE_INDICATORS:
            if indicator in combined:
                return True

        # 2. Company relevance check:
        # Check if the company name (or main tokens) appears in the title or snippet
        company_clean = re.sub(r'[^a-zA-Z0-9\s]', '', article.company.lower())
        company_tokens = [tok for tok in company_clean.split() if len(tok) > 2]
        
        has_company_mention = any(
            tok in title_lower or tok in snippet_lower for tok in company_tokens
        )
        if not has_company_mention:
            return True

        # 3. Minimum length / garbage check
        if len(article.title.strip()) < 12:
            return True

        return False

    def clean_url(self, raw_url: str) -> str:
        """
        Removes UTM tracking tags and marketing parameters from URLs.
        """
        try:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            # Remove tracking keys
            clean_params = {
                k: v for k, v in query_params.items()
                if not (k.startswith("utm_") or k in {"ref", "fbclid", "gclid", "source"})
            }
            new_query = urlencode(clean_params, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
        except Exception:
            return raw_url

    def _tokenize(self, text: str) -> Set[str]:
        """
        Extracts alphanumeric tokens excluding stopwords.
        """
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        tokens = {
            word for word in clean_text.split()
            if word not in STOPWORDS and len(word) > 2
        }
        return tokens

    def compute_similarity(self, title_a: str, title_b: str) -> float:
        """
        Calculates a hybrid similarity score between two titles using Jaccard & SequenceMatcher.
        """
        tokens_a = self._tokenize(title_a)
        tokens_b = self._tokenize(title_b)

        if not tokens_a or not tokens_b:
            return 0.0

        # Jaccard index on keyword tokens
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        jaccard = intersection / union if union > 0 else 0.0

        # Sequence matcher ratio on normalized titles
        norm_a = " ".join(sorted(tokens_a))
        norm_b = " ".join(sorted(tokens_b))
        seq_ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()

        # Hybrid weighted similarity
        return 0.6 * jaccard + 0.4 * seq_ratio

    def deduplicate_and_cluster(self, articles: List[RawArticle]) -> List[Tuple[RawArticle, List[RawArticle]]]:
        """
        Filters noise and groups duplicate/syndicated articles into clusters.
        Returns a list of tuples: (canonical_article, all_clustered_articles).
        """
        # Step 1: Filter out noise
        valid_articles = [art for art in articles if not self.is_noise(art)]

        clusters: List[List[RawArticle]] = []

        # Step 2: Cluster similar articles
        for article in valid_articles:
            matched_cluster = None
            for cluster in clusters:
                # Compare against the representative (first) article in cluster
                sim = self.compute_similarity(article.title, cluster[0].title)
                if sim >= self.similarity_threshold:
                    matched_cluster = cluster
                    break
            
            if matched_cluster is not None:
                matched_cluster.append(article)
            else:
                clusters.append([article])

        # Step 3: Elect canonical representative for each cluster
        result: List[Tuple[RawArticle, List[RawArticle]]] = []
        for cluster in clusters:
            # Pick canonical article: preferred by title length and snippet richness
            canonical = max(
                cluster,
                key=lambda a: (len(a.title) + len(a.snippet), -len(a.title.split(" - ")))
            )
            result.append((canonical, cluster))

        return result
