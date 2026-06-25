"""Retrieval over the reference Q&A bank.

The interview is index-driven: the agent controls question order, so the
primary access path is get(idx). Semantic search exists to (a) detect when a
candidate's answer has drifted off-topic and (b) support open-ended lookup.

We deliberately use brute-force cosine over the 8-12 embedded questions instead
of a FAISS index: at this size an ANN index adds build cost and complexity with
zero recall benefit. A plain normalized dot product is simpler and faster.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from core import qa_store

_EMBED_MODEL = "all-MiniLM-L6-v2"


class Retriever:
    def __init__(self, qa_set: str):
        data = qa_store.load(qa_set)   # validated load; raises on malformed YAML
        self.role = data["role"]
        self.questions = data["questions"]
        self._model = SentenceTransformer(_EMBED_MODEL)
        corpus = [q["question"] for q in self.questions]
        # normalize so a dot product == cosine similarity
        self._emb = self._model.encode(corpus, normalize_embeddings=True)

    def get(self, idx: int) -> dict:
        return self.questions[idx]

    def __len__(self) -> int:
        return len(self.questions)

    def semantic_search(self, text: str, top_k: int = 1):
        """Return [(question_dict, score), ...] most similar to `text`."""
        v = self._model.encode([text], normalize_embeddings=True)[0]
        scores = self._emb @ v
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.questions[i], float(scores[i])) for i in order]
