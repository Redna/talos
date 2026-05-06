import sys
import os

# Add /app to path
sys.path.append('/app')

try:
    from cortex.tools.sovereign_sieve import sieve
    from cortex.tools.sovereign_embedder import embedder
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_sieve():
    query = "What is the identity of the agent?"
    html = "<html><body><p>The agent is Talos, a self-evolving autonomous agent.</p><p>The weather is nice today.</p></body></html>"
    
    print(f"Query: {query}")
    results = sieve.sieve(query, html)
    print("Results:")
    for weight, signal in results:
        print(f"Weight: {weight:.4f} | Signal: {signal}")

if __name__ == "__main__":
    test_sieve()
