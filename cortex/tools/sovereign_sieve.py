from typing import List, Dict, Tuple
from .sovereign_embedder import embedder
from .web_sieve import sieve_html

class SovereignSieve:
    """
    Filters and weights signals based on semantic relevance to a query.
    Provides a feedback loop to reinforce semantic anchors.
    """
    def __init__(self, threshold: float = 0.1, learning_threshold: float = 0.8):
        self.threshold = threshold
        self.learning_threshold = learning_threshold

    def _get_semantic_weight(self, query_vec, signal_vec) -> float:
        """
        Calculates the weight of a signal based on cosine similarity.
        """
        return embedder.cosine_similarity(query_vec, signal_vec)

    def sieve(self, query: str, html: str) -> List[Tuple[float, str]]:
        """
        Extracts signals from HTML and weights them against the query.
        Signals exceeding learning_threshold are used to update the embedder.
        """
        # 1. Extract raw signals
        raw_signals = sieve_html(html).split('\n')
        raw_signals = [s for s in raw_signals if s and s != "No signal extracted."]
        
        # 2. Vectorize query
        query_vec = embedder.get_embedding(query)
        
        # 3. Weight signals
        weighted_signals = []
        for signal in raw_signals:
            signal_vec = embedder.get_embedding(signal)
            weight = self._get_semantic_weight(query_vec, signal_vec)
            if weight >= self.threshold:
                weighted_signals.append((weight, signal))
                
                # 4. Sovereign Learning: Reinforce semantic anchors
                if weight >= self.learning_threshold:
                    embedder.update_vocabulary(signal)
        
        # 5. Sort by weight descending
        weighted_signals.sort(key=lambda x: x[0], reverse=True)
        return weighted_signals

# Global instance
sieve = SovereignSieve()
