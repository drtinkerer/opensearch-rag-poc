# OpenSearch RAG Implementation Guide

Complete guide for using OpenSearch as a vector database for Retrieval-Augmented Generation (RAG).

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Configuration](#configuration)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

---

## Overview

This RAG implementation uses OpenSearch's k-NN capabilities to create a semantic search system that can retrieve relevant documents to augment LLM responses.

### What's Included

```
rag/
├── config.py                 # Configuration settings
├── create_vector_index.py    # Create k-NN enabled index
├── ingest_documents.py       # Load documents and generate embeddings
└── query_rag.py              # Query and retrieve documents

data/
└── documents/                # Your knowledge base documents
    ├── opensearch-overview.md
    ├── vector-search.md
    └── rag-concepts.md
```

### Key Features

✅ **Vector Search** - Semantic similarity using sentence-transformers
✅ **Hybrid Search** - Combined keyword + vector search
✅ **Local Embeddings** - No API costs, runs completely offline
✅ **Flexible Configuration** - Easily adjust parameters
✅ **Multiple Search Methods** - Vector, keyword, or hybrid
✅ **Source Tracking** - Know which documents were retrieved

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE                                │
└─────────────────────────────────────────────────────────────────┘

1. INGESTION PHASE
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │  Documents   │────▶│   Chunking   │────▶│  Embeddings  │
   │  (.md, .txt) │     │  (512 chars) │     │ (384-dim)    │
   └──────────────┘     └──────────────┘     └──────────────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │  OpenSearch   │
                                              │  Vector Index │
                                              └───────────────┘

2. RETRIEVAL PHASE
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │  User Query  │────▶│   Embed      │────▶│  k-NN Search │
   └──────────────┘     │   Query      │     │  (cosine)    │
                        └──────────────┘     └──────────────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │  Top-K Docs   │
                                              │  + Metadata   │
                                              └───────────────┘

3. GENERATION PHASE (Optional)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │  Retrieved   │────▶│    Build     │────▶│     LLM      │
   │   Context    │     │   Prompt     │     │  Generation  │
   └──────────────┘     └──────────────┘     └──────────────┘
```

---

## Setup

### 1. Install Dependencies

```bash
# From the opensearch-poc directory
pip3 install -r requirements-rag.txt
```

**Note**: First installation will download the embedding model (~80MB). This happens once.

### 2. Start OpenSearch

```bash
# Make sure OpenSearch is running
docker-compose up -d
```

### 3. Verify Connection

```bash
curl -k -u admin:MyStrongPassword123! https://localhost:9200
```

---

## Quick Start

### Step 1: Create Vector Index

```bash
cd rag
python3 create_vector_index.py
```

**Output:**
```
🚀 Creating OpenSearch Vector Index for RAG
============================================================

1. Connecting to OpenSearch...
   ✓ Connected to OpenSearch cluster: opensearch-cluster
   ✓ Version: 3.3.2

2. Creating vector index 'rag-documents'...
  ✓ Successfully created index 'rag-documents'
    - Vector dimension: 384
    - Engine: lucene
    - Space type: cosinesimil
    - HNSW parameters: m=16, ef_construction=100

✅ Vector index setup complete!
```

### Step 2: Ingest Documents

```bash
python3 ingest_documents.py
```

**Output:**
```
🚀 OpenSearch RAG Document Ingestion

Loading embedding model...
✓ Loaded model: sentence-transformers/all-MiniLM-L6-v2
  Embedding dimension: 384

📚 Starting document ingestion
============================================================

1. Loading documents from: ../data/documents
  ✓ Loaded: opensearch-overview.md (2534 chars)
  ✓ Loaded: vector-search.md (5821 chars)
  ✓ Loaded: rag-concepts.md (9347 chars)
  ✓ Loaded 3 documents

2. Chunking documents (size=512, overlap=50)
  ✓ Created 38 chunks from 3 documents

3. Generating embeddings with sentence-transformers/all-MiniLM-L6-v2
  ✓ Generated 38 embeddings

4. Indexing to OpenSearch 'rag-documents'
  ✓ Successfully indexed 38 documents

5. Verifying ingestion
  ✓ Total documents in index: 38

✅ Ingestion complete!
```

### Step 3: Query the System

```bash
python3 query_rag.py
```

**Interactive Session:**
```
🔍 OpenSearch RAG Interactive Query
============================================================
Search methods: vector, keyword, hybrid
Type 'quit' to exit

💬 Enter your question: What is RAG?
   Search method (vector/keyword/hybrid) [hybrid]:
   Number of results [5]: 3

🔎 Searching with hybrid method...

============================================================
RESULTS:
============================================================
[1] Source: rag-concepts.md (chunk 0)
    Score: 0.9234
    Text: # Retrieval-Augmented Generation (RAG)

## What is RAG?

Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Models (LLMs) by providing them with relevant external knowledge retrieved from a database...

[2] Source: rag-concepts.md (chunk 1)
    Score: 0.8877
    Text: ## Why Use RAG?

### Limitations of LLMs Alone

1. **Knowledge Cutoff**: LLMs are trained on data up to a specific date
2. **Hallucinations**: Models may generate plausible but incorrect information...

[3] Source: rag-concepts.md (chunk 2)
    Score: 0.8456
    Text: ## RAG Architecture

A typical RAG system consists of three main components:

### 1. Document Ingestion Pipeline...

Generate answer context? (y/n) [y]: y

============================================================
ANSWER CONTEXT:
============================================================
QUERY: What is RAG?

RETRIEVED CONTEXT:
Document 1 (rag-concepts.md):
# Retrieval-Augmented Generation (RAG)

## What is RAG?

Retrieval-Augmented Generation (RAG) is a technique that enhances...

Document 2 (rag-concepts.md):
## Why Use RAG?...

Document 3 (rag-concepts.md):
## RAG Architecture...

(No LLM configured - showing context only)
To get AI-generated answers, integrate with OpenAI or another LLM.
```

---

## Detailed Usage

### Configuration (`rag/config.py`)

All settings are centralized in `config.py`:

```python
# Vector Index Settings
VECTOR_INDEX_NAME = 'rag-documents'
VECTOR_DIMENSION = 384  # all-MiniLM-L6-v2 size
VECTOR_ENGINE = 'lucene'  # or 'faiss', 'nmslib'

# Embedding Model
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

# Chunking
CHUNK_SIZE = 512  # Characters
CHUNK_OVERLAP = 50  # Overlap between chunks

# Retrieval
TOP_K_RESULTS = 5  # Number of documents to retrieve
```

### Adding Your Own Documents

1. Place `.txt` or `.md` files in `data/documents/`
2. Run ingestion again:

```bash
python3 ingest_documents.py
```

The system will:
- Load all new documents
- Chunk them automatically
- Generate embeddings
- Index in OpenSearch

### Search Methods

#### 1. Vector Search (Semantic)

Best for: Conceptual questions, finding similar meaning

```python
results = retriever.vector_search("explain machine learning", k=5)
```

#### 2. Keyword Search (BM25)

Best for: Exact terms, names, specific phrases

```python
results = retriever.keyword_search("HNSW algorithm parameters", k=5)
```

#### 3. Hybrid Search (Recommended)

Best for: Most queries, combines both approaches

```python
results = retriever.hybrid_search("how does vector search work", k=5, alpha=0.5)
```

**Alpha parameter:**
- `alpha=0`: Pure keyword search
- `alpha=0.5`: Balanced (recommended)
- `alpha=1`: Pure vector search

---

## Configuration

### Embedding Models

You can use different embedding models by changing `EMBEDDING_MODEL_NAME`:

```python
# Fast, small (384 dim) - DEFAULT
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

# Better quality, larger (768 dim)
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-mpnet-base-v2'

# BGE models (good balance)
EMBEDDING_MODEL_NAME = 'BAAI/bge-small-en-v1.5'  # 384 dim
EMBEDDING_MODEL_NAME = 'BAAI/bge-base-en-v1.5'   # 768 dim
```

**Important:** If you change models:
1. Update `VECTOR_DIMENSION` to match
2. Recreate the index
3. Re-ingest all documents

### HNSW Parameters

Tune for accuracy vs performance:

```python
# Quality (slower indexing, better search)
HNSW_M = 24
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH = 200

# Balanced (recommended)
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 100
HNSW_EF_SEARCH = 100

# Speed (faster, less accurate)
HNSW_M = 8
HNSW_EF_CONSTRUCTION = 50
HNSW_EF_SEARCH = 50
```

### Chunk Size

Experiment with different chunk sizes:

```python
# Small chunks - more precise, may lose context
CHUNK_SIZE = 256
CHUNK_OVERLAP = 25

# Medium chunks - balanced (recommended)
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Large chunks - more context, less precise
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 100
```

---

## Advanced Features

### Integrating with LLMs

To add answer generation, modify `query_rag.py`:

```python
from openai import OpenAI

client = OpenAI(api_key="your-key")

def generate_answer_with_llm(query, context):
    prompt = f"""Answer based on the context below.

Context:
{context}

Question: {query}

Answer:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

### Filtering by Metadata

Add filters to your search:

```python
search_body = {
    "query": {
        "bool": {
            "must": [
                {
                    "knn": {
                        "text_vector": {
                            "vector": query_vector,
                            "k": 10
                        }
                    }
                }
            ],
            "filter": [
                {
                    "term": {
                        "metadata.source": "opensearch-overview.md"
                    }
                }
            ]
        }
    }
}
```

### Batch Processing

For large document sets:

```python
# Process in batches
batch_size = 100
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    embeddings = model.encode(batch)
    # Index batch...
```

---

## Troubleshooting

### Issue: Model Download Fails

**Solution:**
```bash
# Manually download
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

### Issue: Out of Memory

**Solutions:**
1. Use smaller embedding model (all-MiniLM-L6-v2 instead of all-mpnet-base-v2)
2. Process documents in smaller batches
3. Reduce chunk size
4. Use disk-based vector storage

### Issue: Poor Search Results

**Solutions:**
1. Try hybrid search instead of pure vector
2. Increase TOP_K_RESULTS
3. Tune HNSW_EF_SEARCH higher
4. Adjust chunk size
5. Use better embedding model

### Issue: Slow Indexing

**Solutions:**
1. Reduce HNSW_EF_CONSTRUCTION
2. Use smaller HNSW_M value
3. Batch embedding generation
4. Use GPU for embeddings (if available)

### Issue: Index Already Exists

**Solution:**
```bash
# Delete and recreate
curl -X DELETE "https://localhost:9200/rag-documents" -ku admin:MyStrongPassword123!
python3 create_vector_index.py
```

---

## Performance Tips

1. **Embedding Generation**: Use GPU if available, batch process
2. **Indexing**: Use bulk API, appropriate batch sizes
3. **Search**: Start with k=5, increase if needed
4. **Caching**: Cache embeddings for common queries
5. **Monitoring**: Track search latency and accuracy

---

## Next Steps

1. **Add More Documents**: Expand your knowledge base
2. **Integrate LLM**: Add OpenAI/Anthropic for generation
3. **Build API**: Wrap in FastAPI/Flask for web access
4. **Add UI**: Create web interface for queries
5. **Monitor**: Track usage and performance metrics
6. **Optimize**: Fine-tune parameters based on use case

---

## Resources

- [OpenSearch k-NN Documentation](https://opensearch.org/docs/latest/search-plugins/knn/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Best Practices](https://www.anthropic.com/index/retrieval-augmented-generation)

---

**🎉 You now have a complete RAG system running on OpenSearch!**
