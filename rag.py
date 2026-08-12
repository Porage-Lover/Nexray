"""
Offline Clinical RAG (Retrieval-Augmented Generation) for Hack4Health.

Uses BM25 text retrieval to search local clinical guideline documents and inject
relevant evidence-based context into the HealthGPT-Pro prompt before inference.
Zero external dependencies — pure Python implementation.
"""
import os
import re
import math
from typing import List, Tuple
from collections import Counter


GUIDELINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinical_guidelines")


class BM25Retriever:
    """
    Lightweight BM25 retrieval engine for offline clinical guideline search.
    Pure Python implementation — no FAISS, no ChromaDB, no ML models needed.
    Optimized for small-to-medium document collections (<1000 passages).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[str] = []
        self.doc_sources: List[str] = []
        self.doc_freqs: List[Counter] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.idf: dict = {}
        self.indexed: bool = False

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        text = text.lower()
        text = re.sub(r"[^\w\s\-]", " ", text)
        tokens = text.split()
        # Remove very short tokens
        return [t for t in tokens if len(t) > 1]

    def index(self, documents: List[str], sources: List[str] = None) -> None:
        """
        Indexes a collection of document passages for BM25 retrieval.

        Args:
            documents: List of text passages to index.
            sources: Optional list of source filenames (parallel to documents).
        """
        self.documents = documents
        self.doc_sources = sources or ["" for _ in documents]
        self.doc_freqs = []
        self.doc_lengths = []

        # Compute term frequencies per document
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_freqs.append(Counter(tokens))
            self.doc_lengths.append(len(tokens))

        self.avg_doc_length = (
            sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1.0
        )

        # Compute IDF for all terms
        n_docs = len(documents)
        all_terms = set()
        for freq in self.doc_freqs:
            all_terms.update(freq.keys())

        self.idf = {}
        for term in all_terms:
            doc_count = sum(1 for freq in self.doc_freqs if term in freq)
            self.idf[term] = math.log((n_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)

        self.indexed = True

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float, str]]:
        """
        Searches the indexed documents for the most relevant passages.

        Args:
            query: The search query string.
            top_k: Number of top results to return.

        Returns:
            List of (document_text, score, source_filename) tuples, sorted by score descending.
        """
        if not self.indexed:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_freq in enumerate(self.doc_freqs):
            score = 0.0
            doc_len = self.doc_lengths[i]

            for token in query_tokens:
                if token not in self.idf:
                    continue

                tf = doc_freq.get(token, 0)
                idf = self.idf[token]

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_len / self.avg_doc_length)
                )
                score += idf * (numerator / denominator)

            scores.append((score, i))

        # Sort by score descending, return top_k
        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx in scores[:top_k]:
            if score > 0:
                results.append((self.documents[idx], score, self.doc_sources[idx]))

        return results


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Splits text into overlapping chunks for indexing.

    Args:
        text: The full document text.
        chunk_size: Approximate number of words per chunk.
        overlap: Number of overlapping words between chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def load_guidelines(guidelines_dir: str = GUIDELINES_DIR) -> BM25Retriever:
    """
    Loads all clinical guideline text files from the guidelines directory
    and builds a BM25 index for retrieval.

    Args:
        guidelines_dir: Path to the directory containing .txt guideline files.

    Returns:
        An indexed BM25Retriever instance.
    """
    retriever = BM25Retriever()

    if not os.path.exists(guidelines_dir):
        print(f"[RAG] No guidelines directory found at {guidelines_dir}")
        return retriever

    documents = []
    sources = []

    for filename in sorted(os.listdir(guidelines_dir)):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(guidelines_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Chunk the document for granular retrieval
            chunks = _chunk_text(content, chunk_size=300, overlap=30)
            documents.extend(chunks)
            sources.extend([filename] * len(chunks))
        except Exception as e:
            print(f"[RAG] Error loading {filename}: {e}")

    if documents:
        retriever.index(documents, sources)
        print(f"[RAG] Indexed {len(documents)} passages from {len(set(sources))} guideline files")
    else:
        print("[RAG] No guideline documents found to index")

    return retriever


def retrieve_context(
    retriever: BM25Retriever,
    modality: str,
    clinical_context: str = "",
    top_k: int = 3,
    min_score: float = 1.0,
) -> str:
    """
    Retrieves relevant clinical guideline passages for a given case.

    Builds a search query from the modality and clinical context, then
    retrieves the top-k most relevant guideline passages.

    Args:
        retriever: An indexed BM25Retriever instance.
        modality: The imaging modality (e.g., "X-ray").
        clinical_context: The clinical context from the user.
        top_k: Number of passages to retrieve.
        min_score: Minimum BM25 score threshold for inclusion.

    Returns:
        A formatted string of retrieved guideline passages, or empty string if none found.
    """
    if not retriever.indexed:
        return ""

    # Build search query from case details
    query = f"{modality} {clinical_context}"

    results = retriever.search(query, top_k=top_k)

    if not results:
        return ""

    # Filter by minimum score
    filtered = [(text, score, source) for text, score, source in results if score >= min_score]

    if not filtered:
        return ""

    # Format retrieved passages
    passages = []
    for i, (text, score, source) in enumerate(filtered, 1):
        source_label = source.replace(".txt", "").replace("_", " ").title()
        passages.append(
            f"[Guideline {i} — {source_label} (relevance: {score:.1f})]:\n{text}"
        )

    return "\n\n".join(passages)
