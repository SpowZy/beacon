"""Retrieval layer for community safety guidance.

This is a small lexical retriever over a curated knowledge base. It is the RAG
step: given a category we retrieve the most relevant guidance and ground the
outgoing message in it. The interface matches what you would use for a vector
store, so swapping in embeddings later is a local change.
"""
from __future__ import annotations

from .models import Category

KNOWLEDGE_BASE: dict[Category, list[str]] = {
    Category.FIRE: [
        "If you see fire or smoke nearby, leave early and do not wait for a second warning.",
        "Keep doors closed and follow the evacuation route shared by local services.",
    ],
    Category.FLOOD: [
        "Move to higher ground and never walk or drive through floodwater.",
        "Disconnect power at the mains only if it is safe to reach.",
    ],
    Category.CRIME: [
        "Stay indoors, lock entry points, and report what you saw to local authorities.",
    ],
    Category.MEDICAL: [
        "Keep the area clear for responders and follow instructions from emergency services.",
    ],
    Category.ROADWORKS: [
        "Expect delays and use the suggested detour where possible.",
    ],
    Category.UTILITY: [
        "Report outages to your provider and keep a charged phone for updates.",
    ],
    Category.WEATHER: [
        "Secure loose items, stay indoors, and check on neighbours who may need help.",
    ],
    Category.COMMUNITY: [
        "Check the community board for details and reach out if you can help.",
    ],
}


def retrieve(category: Category, query: str, k: int = 1) -> list[str]:
    docs = KNOWLEDGE_BASE.get(category, [])
    if not docs:
        return []
    terms = {t.lower().strip(".,") for t in query.split() if len(t) > 3}
    scored: list[tuple[int, str]] = []
    for doc in docs:
        doc_terms = {t.lower().strip(".,") for t in doc.split()}
        scored.append((len(terms & doc_terms), doc))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [doc for _, doc in scored[:k]]
