# Vector Search in OpenSearch

## Introduction to Vector Search

Vector search, also known as semantic search or similarity search, enables finding similar items based on their meaning rather than exact keyword matches. This is accomplished by representing data as high-dimensional vectors (embeddings) and measuring the distance between these vectors.

## k-Nearest Neighbors (k-NN)

OpenSearch's k-NN plugin provides vector search capabilities using approximate nearest neighbor algorithms. The k-NN algorithm finds the k data points in a dataset that are closest to a given query point.

### Supported Algorithms

OpenSearch supports three k-NN engines:

1. **NMSLIB** (Non-Metric Space Library): Efficient for high-dimensional spaces
2. **Faiss** (Facebook AI Similarity Search): Optimized for GPU acceleration
3. **Lucene**: Native Apache Lucene k-NN implementation

The most commonly used algorithm is HNSW (Hierarchical Navigable Small World), which provides excellent performance and accuracy.

## Creating Vector Indices

To use vector search, you must create an index with a k-NN vector field:

```json
{
  "settings": {
    "index.knn": true
  },
  "mappings": {
    "properties": {
      "my_vector": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "lucene"
        }
      }
    }
  }
}
```

### Vector Dimensions

The dimension parameter specifies the length of vectors. Common dimensions include:
- 384: sentence-transformers/all-MiniLM-L6-v2
- 768: BERT-base models
- 1536: OpenAI text-embedding-ada-002
- Up to 16,000 dimensions are supported

## Distance Metrics

OpenSearch supports several distance metrics:

- **Cosine Similarity**: Measures the cosine of the angle between vectors. Range: -1 to 1
- **Euclidean (L2)**: Straight-line distance between points
- **Inner Product**: Dot product of vectors
- **Hamming**: Distance between binary vectors

Cosine similarity is most commonly used for text embeddings.

## Generating Embeddings

Embeddings can be generated using:

1. **Pre-trained models**: sentence-transformers, OpenAI, Cohere
2. **Custom models**: Fine-tuned for specific domains
3. **OpenSearch ML Commons**: Built-in model hosting

Example using sentence-transformers:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("This is a sample text")
```

## Querying Vectors

Perform k-NN search using the knn query clause:

```json
{
  "query": {
    "knn": {
      "my_vector": {
        "vector": [0.1, 0.2, ...],
        "k": 10
      }
    }
  }
}
```

## Hybrid Search

Combine vector search with traditional keyword search for better results:

```json
{
  "query": {
    "bool": {
      "should": [
        {
          "knn": {
            "my_vector": {
              "vector": [0.1, 0.2, ...],
              "k": 10
            }
          }
        },
        {
          "match": {
            "text": "search query"
          }
        }
      ]
    }
  }
}
```

## Performance Optimization

### Index Parameters

- **ef_construction**: Controls index quality (higher = better, slower)
- **m**: Number of bidirectional links per node
- **ef_search**: Search time parameter (higher = more accurate)

### Memory Considerations

Vector indices can consume significant memory. Options for optimization:

1. **Quantization**: Reduce vector precision
2. **Disk-based storage**: Store vectors on disk
3. **Filtering**: Apply filters before k-NN search

## Use Cases

Vector search is ideal for:

- **Semantic search**: Find documents by meaning, not keywords
- **Recommendation systems**: Find similar products, content
- **Image search**: Visual similarity matching
- **Anomaly detection**: Identify unusual patterns
- **Question answering**: Retrieve relevant knowledge base articles
- **Duplicate detection**: Find near-duplicate content

## Best Practices

1. Choose appropriate vector dimensions for your use case
2. Use cosine similarity for normalized embeddings
3. Tune HNSW parameters based on accuracy vs performance needs
4. Consider hybrid search for best results
5. Monitor index size and query performance
6. Use batch processing for embedding generation

Vector search transforms OpenSearch into a powerful semantic search engine capable of understanding meaning and context beyond simple keyword matching.
