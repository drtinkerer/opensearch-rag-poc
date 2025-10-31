#!/usr/bin/env python3
"""
Ingest documents into OpenSearch with vector embeddings for RAG.
Processes text files, generates embeddings, and stores them in the vector index.
"""
import os
import urllib3
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from opensearchpy import OpenSearch, helpers
from sentence_transformers import SentenceTransformer
from config import (
    OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USER, OPENSEARCH_PASSWORD,
    OPENSEARCH_USE_SSL, OPENSEARCH_VERIFY_CERTS,
    VECTOR_INDEX_NAME, EMBEDDING_MODEL_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DocumentIngester:
    """Handle document ingestion with embeddings."""

    def __init__(self):
        """Initialize the ingester with OpenSearch client and embedding model."""
        self.client = self._get_opensearch_client()
        print("Loading embedding model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print(f"✓ Loaded model: {EMBEDDING_MODEL_NAME}")
        print(f"  Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

    def _get_opensearch_client(self):
        """Create OpenSearch client."""
        return OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
            use_ssl=OPENSEARCH_USE_SSL,
            verify_certs=OPENSEARCH_VERIFY_CERTS,
            ssl_show_warn=False
        )

    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Number of overlapping characters between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def load_documents(self, directory: str = DATA_DIR) -> List[Dict]:
        """
        Load all text/markdown files from directory.

        Args:
            directory: Path to directory containing documents

        Returns:
            List of document dictionaries with text and metadata
        """
        documents = []
        directory_path = Path(directory)

        if not directory_path.exists():
            print(f"Directory not found: {directory}")
            return documents

        # Supported file extensions
        extensions = ['.txt', '.md', '.markdown']

        for file_path in directory_path.rglob('*'):
            if file_path.suffix.lower() in extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Get file metadata
                    relative_path = file_path.relative_to(directory_path)

                    documents.append({
                        'text': content,
                        'metadata': {
                            'source': str(relative_path),
                            'title': file_path.stem,
                            'created_at': datetime.utcnow().isoformat()
                        }
                    })
                    print(f"  ✓ Loaded: {relative_path} ({len(content)} chars)")

                except Exception as e:
                    print(f"  ✗ Error loading {file_path}: {e}")

        return documents

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        return embeddings.tolist()

    def ingest(self, directory: str = DATA_DIR, index_name: str = VECTOR_INDEX_NAME):
        """
        Main ingestion pipeline: load docs, chunk, embed, and index.

        Args:
            directory: Directory containing documents
            index_name: OpenSearch index to write to
        """
        print(f"\n📚 Starting document ingestion")
        print("=" * 60)

        # Load documents
        print(f"\n1. Loading documents from: {directory}")
        documents = self.load_documents(directory)

        if not documents:
            print("  ⚠ No documents found!")
            return

        print(f"  ✓ Loaded {len(documents)} documents")

        # Chunk documents
        print(f"\n2. Chunking documents (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
        chunks = []
        for doc in documents:
            doc_chunks = self.chunk_text(doc['text'])
            for i, chunk in enumerate(doc_chunks):
                chunks.append({
                    'text': chunk,
                    'metadata': {
                        **doc['metadata'],
                        'chunk_id': i,
                        'total_chunks': len(doc_chunks)
                    }
                })

        print(f"  ✓ Created {len(chunks)} chunks from {len(documents)} documents")

        # Generate embeddings
        print(f"\n3. Generating embeddings with {EMBEDDING_MODEL_NAME}")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        print(f"  ✓ Generated {len(embeddings)} embeddings")

        # Prepare documents for bulk indexing
        print(f"\n4. Indexing to OpenSearch '{index_name}'")
        actions = []
        for chunk, embedding in zip(chunks, embeddings):
            action = {
                '_index': index_name,
                '_source': {
                    'text': chunk['text'],
                    'text_vector': embedding,
                    'metadata': chunk['metadata']
                }
            }
            actions.append(action)

        # Bulk index
        try:
            success, errors = helpers.bulk(self.client, actions, raise_on_error=False)
            print(f"  ✓ Successfully indexed {success} documents")

            if errors:
                print(f"  ⚠ {len(errors)} errors occurred during indexing")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"    - {error}")

        except Exception as e:
            print(f"  ✗ Error during bulk indexing: {e}")
            raise

        # Verify
        print(f"\n5. Verifying ingestion")
        count = self.client.count(index=index_name)
        print(f"  ✓ Total documents in index: {count['count']}")

        print("\n✅ Ingestion complete!")


def main():
    """Main function to run document ingestion."""
    print("🚀 OpenSearch RAG Document Ingestion")

    ingester = DocumentIngester()
    ingester.ingest()

    print("\nNext step:")
    print("  Run 'query_rag.py' to test retrieval and generation")


if __name__ == "__main__":
    main()
