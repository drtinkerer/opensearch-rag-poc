#!/usr/bin/env python3
"""
Create a vector index in OpenSearch for RAG.
This sets up a k-NN enabled index with hybrid search capabilities.
"""
import urllib3
from opensearchpy import OpenSearch
from config import (
    OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USER, OPENSEARCH_PASSWORD,
    OPENSEARCH_USE_SSL, OPENSEARCH_VERIFY_CERTS,
    VECTOR_INDEX_NAME, VECTOR_DIMENSION, VECTOR_ENGINE, VECTOR_SPACE_TYPE,
    HNSW_M, HNSW_EF_CONSTRUCTION
)

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_opensearch_client():
    """Create and return OpenSearch client."""
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
        use_ssl=OPENSEARCH_USE_SSL,
        verify_certs=OPENSEARCH_VERIFY_CERTS,
        ssl_show_warn=False
    )
    return client


def create_vector_index(client, index_name=VECTOR_INDEX_NAME):
    """
    Create a k-NN enabled index for vector search.

    Index structure:
    - text: The original text content
    - text_vector: Dense vector embedding of the text
    - metadata: Additional fields (source, page, etc.)
    """

    # Check if index already exists
    if client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists.")
        response = input("Do you want to delete and recreate it? (yes/no): ")
        if response.lower() == 'yes':
            client.indices.delete(index=index_name)
            print(f"Deleted existing index '{index_name}'")
        else:
            print("Keeping existing index. Exiting.")
            return

    # Index settings and mappings
    index_body = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "knn": True,  # Enable k-NN for this index
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "text": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "text_vector": {
                    "type": "knn_vector",
                    "dimension": VECTOR_DIMENSION,
                    "method": {
                        "name": "hnsw",
                        "space_type": VECTOR_SPACE_TYPE,
                        "engine": VECTOR_ENGINE,
                        "parameters": {
                            "ef_construction": HNSW_EF_CONSTRUCTION,
                            "m": HNSW_M
                        }
                    }
                },
                "metadata": {
                    "properties": {
                        "source": {"type": "keyword"},
                        "page": {"type": "integer"},
                        "chunk_id": {"type": "integer"},
                        "title": {"type": "text"},
                        "created_at": {"type": "date"}
                    }
                }
            }
        }
    }

    try:
        # Create the index
        response = client.indices.create(index=index_name, body=index_body)
        print(f"✓ Successfully created index '{index_name}'")
        print(f"  - Vector dimension: {VECTOR_DIMENSION}")
        print(f"  - Engine: {VECTOR_ENGINE}")
        print(f"  - Space type: {VECTOR_SPACE_TYPE}")
        print(f"  - HNSW parameters: m={HNSW_M}, ef_construction={HNSW_EF_CONSTRUCTION}")
        return response
    except Exception as e:
        print(f"✗ Error creating index: {e}")
        raise


def get_index_info(client, index_name=VECTOR_INDEX_NAME):
    """Get and display information about the index."""
    try:
        # Get index mappings
        mappings = client.indices.get_mapping(index=index_name)
        print(f"\n📊 Index Information for '{index_name}':")
        print(f"Mappings: {mappings}")

        # Get index settings
        settings = client.indices.get_settings(index=index_name)
        print(f"\nSettings: {settings}")

        # Get document count
        count = client.count(index=index_name)
        print(f"\n📈 Document count: {count['count']}")

    except Exception as e:
        print(f"Error getting index info: {e}")


def main():
    """Main function to create vector index."""
    print("🚀 Creating OpenSearch Vector Index for RAG")
    print("=" * 60)

    # Connect to OpenSearch
    print("\n1. Connecting to OpenSearch...")
    client = get_opensearch_client()

    try:
        info = client.info()
        print(f"   ✓ Connected to OpenSearch cluster: {info['cluster_name']}")
        print(f"   ✓ Version: {info['version']['number']}")
    except Exception as e:
        print(f"   ✗ Failed to connect: {e}")
        return

    # Create index
    print(f"\n2. Creating vector index '{VECTOR_INDEX_NAME}'...")
    create_vector_index(client)

    # Display index info
    print("\n3. Verifying index creation...")
    get_index_info(client)

    print("\n✅ Vector index setup complete!")
    print("\nNext steps:")
    print("  1. Run 'ingest_documents.py' to add documents")
    print("  2. Run 'query_rag.py' to test retrieval")


if __name__ == "__main__":
    main()
