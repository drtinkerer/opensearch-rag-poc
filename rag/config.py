"""
Configuration settings for OpenSearch RAG implementation.
"""
import os

# OpenSearch Configuration
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'localhost')
OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', 9200))
OPENSEARCH_USER = os.getenv('OPENSEARCH_USER', 'admin')
OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_PASSWORD', 'MyStrongPassword123!')
OPENSEARCH_USE_SSL = True
OPENSEARCH_VERIFY_CERTS = False

# Vector Index Configuration
VECTOR_INDEX_NAME = 'rag-documents'
VECTOR_DIMENSION = 384  # all-MiniLM-L6-v2 embedding dimension
VECTOR_ENGINE = 'lucene'  # or 'faiss', 'nmslib'
VECTOR_SPACE_TYPE = 'cosinesimil'  # or 'l2', 'innerproduct'

# HNSW Algorithm Parameters
HNSW_M = 16  # Number of bidirectional links (higher = more accurate, more memory)
HNSW_EF_CONSTRUCTION = 100  # Size of dynamic candidate list (higher = better quality, slower indexing)
HNSW_EF_SEARCH = 100  # Size of dynamic candidate list for search (higher = more accurate, slower)

# Embedding Model Configuration
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'  # Fast, 384-dim
# Alternative models:
# 'sentence-transformers/all-mpnet-base-v2'  # Better quality, 768-dim, slower
# 'BAAI/bge-small-en-v1.5'  # Good balance, 384-dim

# Text Chunking Configuration
CHUNK_SIZE = 512  # Characters per chunk
CHUNK_OVERLAP = 50  # Overlap between chunks

# Retrieval Configuration
TOP_K_RESULTS = 5  # Number of documents to retrieve
HYBRID_SEARCH_ALPHA = 0.5  # 0 = pure keyword, 1 = pure vector, 0.5 = balanced

# LLM Configuration (optional - for generation step)
LLM_MODEL = 'gpt-3.5-turbo'  # OpenAI model
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 500

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'documents')
