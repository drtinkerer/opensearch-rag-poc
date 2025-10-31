#!/usr/bin/env python3
"""
Quick test script for RAG functionality.
"""
from query_rag import RAGRetriever

def test_rag():
    """Test RAG with sample queries."""
    print("🧪 Testing RAG System")
    print("=" * 60)

    retriever = RAGRetriever()

    # Test queries
    queries = [
        ("What is RAG?", "hybrid"),
        ("How does vector search work?", "vector"),
        ("OpenSearch architecture", "keyword"),
    ]

    for i, (query, method) in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print(f"Method: {method}")
        print("=" * 60)

        results = retriever.retrieve(query, method=method, k=3)

        if results:
            print(f"\n✓ Retrieved {len(results)} results")
            for j, result in enumerate(results, 1):
                source = result['metadata'].get('source', 'Unknown')
                chunk_id = result['metadata'].get('chunk_id', 0)
                score = result.get('score', 0)
                text_preview = result['text'][:150] + "..."

                print(f"\n[{j}] {source} (chunk {chunk_id}) - Score: {score:.4f}")
                print(f"    {text_preview}")
        else:
            print("✗ No results found")

    print("\n" + "=" * 60)
    print("✅ RAG testing complete!")
    print("\nTo test interactively, run: python3 query_rag.py")


if __name__ == "__main__":
    test_rag()
