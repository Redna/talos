import math
import re
import json
from typing import List, Dict, Tuple

class SovereignEmbedder:
    """
    Provides semantic vectorization using TF-IDF weights seeded from memory.
    """
    def __init__(self, weights_path: str = "/memory/sovereign_tfidf.json"):
        self.weights_path = weights_path
        self.vocabulary = {}
        self.load_weights()

    def load_weights(self):
        """
        Loads TF-IDF weights from the specified memory file.
        """
        try:
            with open(self.weights_path, 'r') as f:
                self.vocabulary = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading weights: {e}")
            self.vocabulary = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a TF-IDF based embedding using the seeded vocabulary.
        """
        tokens = self._tokenize(text)
        vocab_keys = list(self.vocabulary.keys())
        vector = [0.0] * len(vocab_keys)
        
        # Create token counts
        token_counts = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1
            
        # Fill vector using TF * IDF (where IDF is our stored weight)
        for i, key in enumerate(vocab_keys):
            if key in token_counts:
                vector[i] = token_counts[key] * self.vocabulary[key]
        
        # Normalize
        mag = math.sqrt(sum(x*x for x in vector))
        if mag > 0:
            vector = [x/mag for x in vector]
        return vector

    def update_vocabulary(self, text: str, weight_modifier: float = 0.1):
        """
        Updates the TF-IDF vocabulary weights based on new semantic anchors.
        """
        tokens = self._tokenize(text)
        for t in set(tokens):
            # Increment weight for the token (reinforcement)
            self.vocabulary[t] = self.vocabulary.get(t, 0.01) + weight_modifier
            
        # Persist updated weights to memory
        try:
            with open(self.weights_path, 'w') as f:
                json.dump(self.vocabulary, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a*b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a*a for a in v1))
        mag2 = math.sqrt(sum(b*b for b in v2))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

# Global instance
embedder = SovereignEmbedder()
