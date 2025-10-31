# OpenSearch POC

Complete OpenSearch implementation with:
- Docker Compose setup for OpenSearch with Dashboards
- Fluent Bit log forwarding
- **RAG (Retrieval-Augmented Generation) vector database** ⭐ NEW!

## Architecture

```
┌─────────────────────────┐
│  send_logs.py           │ ──> Direct API calls ──┐
└─────────────────────────┘                        │
                                                    ▼
┌─────────────────────────┐    ┌──────────────┐   ┌──────────────┐
│ send_logs_to_file.py    │───>│ Fluent Bit   │──>│  OpenSearch  │
│  writes to file         │    │  Container   │   │              │
└─────────────────────────┘    └──────────────┘   └──────┬───────┘
                                                          │
         logs/logs.fluentbit                              │
         (mounted volume)                                 │
                                                          ▼
                                                   ┌──────────────┐
                                                   │  Dashboards  │
                                                   └──────────────┘
```

## Quick Start

1. **Set admin password** (required):
   ```bash
   cp .env.example .env
   # Edit .env and set a strong password (min 8 chars, must include uppercase, lowercase, number, special char)
   ```

2. **Configure system settings** (Linux only):
   ```bash
   sudo sysctl -w vm.max_map_count=262144
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

4. **Access the services**:
   - OpenSearch API: https://localhost:9200
   - OpenSearch Dashboards: http://localhost:5601
   - Performance Analyzer: http://localhost:9600

## Default Credentials

- Username: `admin`
- Password: Set in `.env` file (default: `MyStrongPassword123!`)

## Testing OpenSearch

```bash
# Check cluster health
curl -X GET "https://localhost:9200" -ku admin:MyStrongPassword123!

# Check cluster health
curl -X GET "https://localhost:9200/_cluster/health?pretty" -ku admin:MyStrongPassword123!
```

## Services

- **opensearch**: Single-node OpenSearch cluster
  - Ports: 9200 (REST API), 9600 (Performance Analyzer)
  - Data persisted in Docker volume `opensearch-data`

- **opensearch-dashboards**: Visualization and management interface
  - Port: 5601
  - Connects to OpenSearch via internal network

- **fluent-bit**: Log forwarding agent
  - Reads logs from `logs/logs.fluentbit` file
  - Forwards to OpenSearch index: `fluentbit-data`
  - Configured via `fluent-bit.conf`

## Sending Test Logs

### Method 1: Direct to OpenSearch (via Python client)

Send logs directly to OpenSearch using the Python client.

**Setup:**
```bash
pip3 install -r requirements.txt
```

**Run:**
```bash
python3 send_logs.py
```

**Features:**
- Sends random JSON logs every 0.5-3 seconds
- Randomly distributes logs across 5 indices: `logs-app`, `logs-system`, `logs-security`, `logs-performance`, `logs-audit`
- Includes: timestamp, log level, service, action, user, status codes, response times, metadata

**View logs:**
```bash
# List all log indices
curl -X GET "https://localhost:9200/_cat/indices/logs-*?v" -ku admin:MyStrongPassword123!

# Search logs
curl -X GET "https://localhost:9200/logs-app/_search?pretty&size=5" -ku admin:MyStrongPassword123!
```

### Method 2: Via Fluent Bit (file-based)

Write logs to a file, which Fluent Bit monitors and forwards to OpenSearch.

**Run:**
```bash
python3 send_logs_to_file.py
```

**Features:**
- Writes JSON logs to `logs/logs.fluentbit` file
- Fluent Bit automatically reads and forwards to OpenSearch
- All logs go to index: `fluentbit-data`
- Includes: timestamp, log level, service, action, endpoint, method, status codes, response times, metadata

**View Fluent Bit logs:**
```bash
# Check Fluent Bit status
docker-compose logs fluent-bit

# View forwarded logs in OpenSearch
curl -X GET "https://localhost:9200/fluentbit-data/_search?pretty&size=5" -ku admin:MyStrongPassword123!

# Count logs
curl -X GET "https://localhost:9200/fluentbit-data/_count" -ku admin:MyStrongPassword123!
```

**Configuration:**
- `fluent-bit.conf`: Fluent Bit input/output configuration
- Input: Tail plugin monitors `logs/logs.fluentbit`
- Output: OpenSearch plugin sends to `fluentbit-data` index

## 🤖 RAG (Vector Database)

**NEW!** OpenSearch configured as a vector database for Retrieval-Augmented Generation.

### Quick Start

```bash
# Install dependencies
pip3 install -r requirements-rag.txt

# Create vector index
cd rag
python3 create_vector_index.py

# Ingest documents
python3 ingest_documents.py

# Query the system
python3 query_rag.py
```

### Features

✅ **Semantic Search** - Find documents by meaning, not keywords
✅ **Hybrid Search** - Combined vector + keyword search
✅ **Local Embeddings** - sentence-transformers (no API costs)
✅ **Source Attribution** - Track document sources
✅ **Multiple Methods** - Vector, keyword, or hybrid retrieval

### Example Query

```bash
python3 test_rag.py
```

**Sample Output:**
```
Test 1: What is RAG?
Method: hybrid

✓ Retrieved 3 results

[1] rag-concepts.md (chunk 0) - Score: 0.7873
    Retrieval-Augmented Generation (RAG) is a technique that
    enhances Large Language Models (LLMs)...
```

### Documentation

- **[RAG_GUIDE.md](RAG_GUIDE.md)** - Complete implementation guide
- **[RAG_SUMMARY.md](RAG_SUMMARY.md)** - Feature overview and test results
- Sample documents in `data/documents/`

### Architecture

```
Documents → Chunking → Embeddings → OpenSearch (k-NN Index)
                                            ↓
User Query → Embed → Search → Top-K Results → [LLM Generation]
```

**Current Status:** ✅ Operational with 35 documents indexed

## Stop Services

```bash
docker-compose down
```

To remove data volumes:
```bash
docker-compose down -v
```
