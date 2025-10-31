#!/usr/bin/env python3
"""
Query the RAG system: retrieve relevant documents and optionally generate answers.
Supports vector search, hybrid search, and integration with LLMs.
"""
import urllib3
from typing import List, Dict, Optional
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
from config import (
    OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USER, OPENSEARCH_PASSWORD,
    OPENSEARCH_USE_SSL, OPENSEARCH_VERIFY_CERTS,
    VECTOR_INDEX_NAME, EMBEDDING_MODEL_NAME, TOP_K_RESULTS, HNSW_EF_SEARCH
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RAGRetriever:
    """Handle RAG retrieval operations."""

    def __init__(self):
        """Initialize retriever with OpenSearch client and embedding model."""
        self.client = self._get_opensearch_client()
        print("Loading embedding model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print(f"✓ Model loaded: {EMBEDDING_MODEL_NAME}")

    def _get_opensearch_client(self):
        """Create OpenSearch client."""
        return OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
            use_ssl=OPENSEARCH_USE_SSL,
            verify_certs=OPENSEARCH_VERIFY_CERTS,
            ssl_show_warn=False
        )

    def vector_search(
        self,
        query: str,
        index_name: str = VECTOR_INDEX_NAME,
        k: int = TOP_K_RESULTS
    ) -> List[Dict]:
        """
        Perform vector similarity search.

        Args:
            query: Search query
            index_name: Index to search
            k: Number of results to return

        Returns:
            List of search results with text and metadata
        """
        # Generate query embedding
        query_vector = self.model.encode(query).tolist()

        # k-NN search query
        search_body = {
            "size": k,
            "query": {
                "knn": {
                    "text_vector": {
                        "vector": query_vector,
                        "k": k,
                        "method_parameters": {
                            "ef_search": HNSW_EF_SEARCH
                        }
                    }
                }
            },
            "_source": ["text", "metadata"]
        }

        try:
            response = self.client.search(index=index_name, body=search_body)
            results = []

            for hit in response['hits']['hits']:
                results.append({
                    'text': hit['_source']['text'],
                    'metadata': hit['_source']['metadata'],
                    'score': hit['_score']
                })

            return results

        except Exception as e:
            print(f"Error during vector search: {e}")
            return []

    def keyword_search(
        self,
        query: str,
        index_name: str = VECTOR_INDEX_NAME,
        k: int = TOP_K_RESULTS
    ) -> List[Dict]:
        """
        Perform traditional keyword search (BM25).

        Args:
            query: Search query
            index_name: Index to search
            k: Number of results to return

        Returns:
            List of search results
        """
        search_body = {
            "size": k,
            "query": {
                "match": {
                    "text": {
                        "query": query,
                        "fuzziness": "AUTO"
                    }
                }
            },
            "_source": ["text", "metadata"]
        }

        try:
            response = self.client.search(index=index_name, body=search_body)
            results = []

            for hit in response['hits']['hits']:
                results.append({
                    'text': hit['_source']['text'],
                    'metadata': hit['_source']['metadata'],
                    'score': hit['_score']
                })

            return results

        except Exception as e:
            print(f"Error during keyword search: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        index_name: str = VECTOR_INDEX_NAME,
        k: int = TOP_K_RESULTS,
        alpha: float = 0.5
    ) -> List[Dict]:
        """
        Perform hybrid search combining vector and keyword search.

        Args:
            query: Search query
            index_name: Index to search
            k: Number of results to return
            alpha: Weight for vector search (0-1). 0=pure keyword, 1=pure vector

        Returns:
            List of search results
        """
        # Get results from both methods
        vector_results = self.vector_search(query, index_name, k * 2)
        keyword_results = self.keyword_search(query, index_name, k * 2)

        # Combine and rerank using Reciprocal Rank Fusion (RRF)
        combined_scores = {}

        # Add vector scores
        for rank, result in enumerate(vector_results):
            doc_id = result['metadata'].get('source', '') + str(result['metadata'].get('chunk_id', 0))
            combined_scores[doc_id] = {
                'result': result,
                'score': alpha * (1 / (rank + 60))  # RRF formula
            }

        # Add keyword scores
        for rank, result in enumerate(keyword_results):
            doc_id = result['metadata'].get('source', '') + str(result['metadata'].get('chunk_id', 0))
            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += (1 - alpha) * (1 / (rank + 60))
            else:
                combined_scores[doc_id] = {
                    'result': result,
                    'score': (1 - alpha) * (1 / (rank + 60))
                }

        # Sort by combined score
        ranked_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        return [item['result'] for item in ranked_results[:k]]

    def retrieve(
        self,
        query: str,
        method: str = 'hybrid',
        k: int = TOP_K_RESULTS
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query
            method: Search method ('vector', 'keyword', or 'hybrid')
            k: Number of results to return

        Returns:
            List of search results
        """
        if method == 'vector':
            return self.vector_search(query, k=k)
        elif method == 'keyword':
            return self.keyword_search(query, k=k)
        elif method == 'hybrid':
            return self.hybrid_search(query, k=k)
        else:
            raise ValueError(f"Unknown method: {method}")

    def format_results(self, results: List[Dict]) -> str:
        """Format search results for display or LLM context."""
        if not results:
            return "No results found."

        formatted = []
        for i, result in enumerate(results, 1):
            source = result['metadata'].get('source', 'Unknown')
            chunk_id = result['metadata'].get('chunk_id', 0)
            text = result['text'][:300] + "..." if len(result['text']) > 300 else result['text']

            formatted.append(
                f"[{i}] Source: {source} (chunk {chunk_id})\n"
                f"    Score: {result.get('score', 0):.4f}\n"
                f"    Text: {text}\n"
            )

        return "\n".join(formatted)

    def generate_answer(self, query: str, results: List[Dict], llm_client=None) -> str:
        """
        Generate an answer using retrieved context and an LLM.

        Args:
            query: User query
            results: Retrieved documents
            llm_client: Optional LLM client (e.g., OpenAI)

        Returns:
            Generated answer or context-only response
        """
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1} ({r['metadata'].get('source', 'Unknown')}):\n{r['text']}"
            for i, r in enumerate(results)
        ])

        if not llm_client:
            # Return context without generation
            return (
                f"QUERY: {query}\n\n"
                f"RETRIEVED CONTEXT:\n{context}\n\n"
                f"(No LLM configured - showing context only)\n"
                f"To get AI-generated answers, integrate with OpenAI or another LLM."
            )

        # If LLM is available, generate answer
        # This is a placeholder for LLM integration
        # You would call llm_client.chat.completions.create() here
        prompt = (
            f"Answer the following question based only on the provided context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        return prompt  # In practice, send to LLM and return response


def interactive_query():
    """Interactive query loop."""
    print("🔍 OpenSearch RAG Interactive Query")
    print("=" * 60)
    print("Search methods: vector, keyword, hybrid")
    print("Type 'quit' to exit\n")

    retriever = RAGRetriever()

    while True:
        # Get query
        query = input("\n💬 Enter your question: ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not query:
            continue

        # Get search method
        method = input("   Search method (vector/keyword/hybrid) [hybrid]: ").strip() or 'hybrid'
        k = input(f"   Number of results [{TOP_K_RESULTS}]: ").strip() or TOP_K_RESULTS
        k = int(k)

        print(f"\n🔎 Searching with {method} method...")

        # Retrieve
        results = retriever.retrieve(query, method=method, k=k)

        # Display results
        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        print(retriever.format_results(results))

        # Optionally generate answer
        show_answer = input("\nGenerate answer context? (y/n) [y]: ").strip().lower() or 'y'
        if show_answer == 'y':
            answer = retriever.generate_answer(query, results)
            print("\n" + "=" * 60)
            print("ANSWER CONTEXT:")
            print("=" * 60)
            print(answer)


def main():
    """Main function."""
    interactive_query()


if __name__ == "__main__":
    main()
