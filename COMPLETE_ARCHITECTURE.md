# Complete OpenSearch POC Architecture

## Full System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OPENSEARCH POC ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           1. LOGGING PIPELINE                                │
└──────────────────────────────────────────────────────────────────────────────┘

   ┌────────────────────┐              ┌─────────────────────┐
   │  send_logs.py      │─────────────▶│   OpenSearch        │
   │  (Direct API)      │   REST API   │   Indices:          │
   └────────────────────┘              │   - logs-app        │
                                       │   - logs-system     │
                                       │   - logs-security   │
   ┌────────────────────┐              │   - logs-performance│
   │ send_logs_to_file  │─────────┐    │   - logs-audit      │
   │  .py (File)        │         │    └─────────────────────┘
   └────────────────────┘         │
         │                        │
         ▼                        │
   ┌────────────────────┐         │
   │ logs/logs.fluentbit│         │
   │  (File on disk)    │         │
   └────────────────────┘         │
         │                        │
         ▼                        │
   ┌────────────────────┐         │    ┌─────────────────────┐
   │  Fluent Bit        │─────────┴───▶│   OpenSearch        │
   │  Container         │   k-NN API   │   Index:            │
   │  (fluent-bit.conf) │              │   - fluentbit-data  │
   └────────────────────┘              └─────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                      2. RAG / VECTOR DATABASE                                │
└──────────────────────────────────────────────────────────────────────────────┘

   INGESTION PHASE:

   ┌────────────────────┐
   │  data/documents/   │
   │  *.md, *.txt       │
   └────────────┬───────┘
                │
                ▼
   ┌────────────────────────────────────────┐
   │  ingest_documents.py                   │
   │  1. Load files                         │
   │  2. Chunk text (512 chars, 50 overlap) │
   │  3. Generate embeddings (384-dim)      │
   │  4. Bulk index to OpenSearch           │
   └────────────┬───────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────┐
   │  OpenSearch k-NN Index                 │
   │  Index: rag-documents                  │
   │  - text: Original content (text)       │
   │  - text_vector: Embeddings (knn_vector)│
   │  - metadata: Source, chunk info        │
   │  Engine: Lucene HNSW                   │
   │  Dimension: 384                        │
   │  Space: cosinesimil                    │
   └────────────────────────────────────────┘

   RETRIEVAL PHASE:

   ┌────────────────────┐
   │  User Query        │
   │  "What is RAG?"    │
   └────────────┬───────┘
                │
                ▼
   ┌────────────────────────────────────────┐
   │  query_rag.py                          │
   │  1. Embed query (sentence-transformers)│
   │  2. Choose search method:              │
   │     - Vector (semantic)                │
   │     - Keyword (BM25)                   │
   │     - Hybrid (RRF combination)         │
   │  3. Execute k-NN search                │
   └────────────┬───────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────┐
   │  Top-K Results                         │
   │  - Document chunks                     │
   │  - Relevance scores                    │
   │  - Source metadata                     │
   └────────────┬───────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────┐
   │  Optional: LLM Generation              │
   │  Context + Query → GPT/Claude → Answer │
   └────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                        3. INFRASTRUCTURE                                     │
└──────────────────────────────────────────────────────────────────────────────┘

   ┌────────────────────────────────────────────────────────────┐
   │                    Docker Compose Network                  │
   │                    (opensearch-net)                        │
   │                                                            │
   │  ┌──────────────────┐  ┌──────────────────┐              │
   │  │   OpenSearch     │  │  Dashboards      │              │
   │  │   Container      │◀─│  Container       │              │
   │  │                  │  │                  │              │
   │  │  Ports:          │  │  Port: 5601      │              │
   │  │  - 9200 (API)    │  │                  │              │
   │  │  - 9600 (Perf)   │  │                  │              │
   │  │                  │  │                  │              │
   │  │  Volume:         │  │                  │              │
   │  │  opensearch-data │  │                  │              │
   │  └──────────────────┘  └──────────────────┘              │
   │           ▲                                               │
   │           │                                               │
   │  ┌────────┴─────────┐                                    │
   │  │  Fluent Bit      │                                    │
   │  │  Container       │                                    │
   │  │                  │                                    │
   │  │  Mounts:         │                                    │
   │  │  - fluent-bit.conf                                    │
   │  │  - logs/         │                                    │
   │  └──────────────────┘                                    │
   │                                                            │
   └────────────────────────────────────────────────────────────┘

   Host Machine:
   ┌────────────────────────────────────────────────────────────┐
   │  - Python scripts (send_logs.py, send_logs_to_file.py)    │
   │  - RAG scripts (rag/*.py)                                  │
   │  - Document storage (data/documents/)                      │
   │  - Log files (logs/logs.fluentbit)                         │
   └────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                         4. DATA FLOW SUMMARY                                 │
└──────────────────────────────────────────────────────────────────────────────┘

   Logging:
   Python → Logs (JSON) → [File or API] → OpenSearch → Dashboards (Viz)

   RAG:
   Documents → Chunks → Embeddings → OpenSearch (k-NN) → Retrieval → [LLM]

   Monitoring:
   All data → OpenSearch Dashboards → Real-time visualization


┌──────────────────────────────────────────────────────────────────────────────┐
│                         5. INDICES OVERVIEW                                  │
└──────────────────────────────────────────────────────────────────────────────┘

   Standard Log Indices (BM25):
   ├── logs-app              (6 docs)
   ├── logs-system           (8 docs)
   ├── logs-security         (12 docs)
   ├── logs-performance      (4 docs)
   └── logs-audit            (6 docs)

   Fluent Bit Log Index (BM25):
   └── fluentbit-data        (53 docs)

   RAG Vector Index (k-NN + BM25):
   └── rag-documents         (35 docs, 384-dim vectors)
       - Supports semantic search
       - Hybrid search enabled
       - Source attribution


┌──────────────────────────────────────────────────────────────────────────────┐
│                      6. KEY FEATURES ENABLED                                 │
└──────────────────────────────────────────────────────────────────────────────┘

   ✅ Full-text search (BM25)
   ✅ Vector similarity search (k-NN)
   ✅ Hybrid search (combined)
   ✅ Real-time log ingestion
   ✅ File-based log forwarding (Fluent Bit)
   ✅ Direct API logging
   ✅ Semantic document retrieval
   ✅ RAG-ready infrastructure
   ✅ Scalable architecture
   ✅ Docker-based deployment
   ✅ Local embedding generation
   ✅ Source attribution


┌──────────────────────────────────────────────────────────────────────────────┐
│                         7. ACCESS POINTS                                     │
└──────────────────────────────────────────────────────────────────────────────┘

   OpenSearch API:          https://localhost:9200
   OpenSearch Dashboards:   http://localhost:5601
   Performance Analyzer:    http://localhost:9600

   Credentials:
   - Username: admin
   - Password: MyStrongPassword123! (or from .env)


┌──────────────────────────────────────────────────────────────────────────────┐
│                      8. TECHNOLOGY STACK                                     │
└──────────────────────────────────────────────────────────────────────────────┘

   Infrastructure:
   - OpenSearch 3.3.2 (search engine + vector database)
   - OpenSearch Dashboards (visualization)
   - Fluent Bit 4.0.13 (log forwarding)
   - Docker Compose (orchestration)

   RAG Stack:
   - sentence-transformers (embeddings)
   - PyTorch (ML framework)
   - Lucene HNSW (k-NN algorithm)
   - Python 3.12 (implementation)

   Search Capabilities:
   - BM25 (keyword search)
   - k-NN (vector search)
   - Hybrid (combined)
   - Reciprocal Rank Fusion (result merging)


┌──────────────────────────────────────────────────────────────────────────────┐
│                         9. USE CASES SUPPORTED                               │
└──────────────────────────────────────────────────────────────────────────────┘

   1. Log Analytics
      - Real-time log ingestion and analysis
      - Multi-source log aggregation
      - Performance monitoring

   2. Semantic Search
      - Find documents by meaning
      - Question answering
      - Knowledge base retrieval

   3. RAG Applications
      - LLM context augmentation
      - Grounded AI responses
      - Source-attributed answers

   4. Hybrid Search
      - Combined keyword + semantic
      - Best-of-both-worlds retrieval
      - Flexible ranking strategies


┌──────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM STATUS                                      │
└──────────────────────────────────────────────────────────────────────────────┘

   ✅ OpenSearch:        Running, healthy
   ✅ Dashboards:        Accessible
   ✅ Fluent Bit:        Forwarding logs
   ✅ RAG System:        Operational, 35 docs indexed
   ✅ Log Ingestion:     Active, multiple indices
   ✅ Vector Search:     Enabled, tested

   Total Documents:      153 (across all indices)
   Total Storage:        ~500 KB
   Services Running:     3 (OpenSearch, Dashboards, Fluent Bit)

```

---

## Quick Commands

```bash
# Start everything
docker-compose up -d

# Generate logs (Method 1: Direct)
python3 send_logs.py

# Generate logs (Method 2: Fluent Bit)
python3 send_logs_to_file.py

# Query RAG system
cd rag && python3 query_rag.py

# View all indices
curl -k -u admin:MyStrongPassword123! https://localhost:9200/_cat/indices?v

# Open Dashboards
open http://localhost:5601
```

---

**Complete system with logging, vector search, and RAG capabilities! 🚀**
