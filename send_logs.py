#!/usr/bin/env python3
"""
Continuously sends random JSON logs to OpenSearch with random indices.
"""
import random
import time
import json
from datetime import datetime
from opensearchpy import OpenSearch
import urllib3

# Disable SSL warnings for demo/self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OpenSearch connection configuration
OPENSEARCH_HOST = 'localhost'
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = 'admin'
OPENSEARCH_PASSWORD = 'MyStrongPassword123!'

# Log data generators
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
SERVICES = ['auth-service', 'api-gateway', 'database', 'cache-service', 'worker', 'scheduler', 'notification-service']
ACTIONS = ['user_login', 'api_request', 'database_query', 'cache_hit', 'cache_miss', 'task_completed', 'email_sent', 'error_occurred']
USERS = ['user_001', 'user_002', 'user_003', 'user_004', 'admin_user', 'system_user']
STATUS_CODES = [200, 201, 400, 401, 403, 404, 500, 502, 503]
INDICES = ['logs-app', 'logs-system', 'logs-security', 'logs-performance', 'logs-audit']

def generate_random_log():
    """Generate a random log entry."""
    log = {
        '@timestamp': datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        'level': random.choice(LOG_LEVELS),
        'service': random.choice(SERVICES),
        'action': random.choice(ACTIONS),
        'user': random.choice(USERS),
        'status_code': random.choice(STATUS_CODES),
        'response_time_ms': random.randint(10, 5000),
        'message': f"Processing {random.choice(ACTIONS)} request",
        'request_id': f"req_{random.randint(100000, 999999)}",
        'ip_address': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        'metadata': {
            'version': f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,20)}",
            'environment': random.choice(['production', 'staging', 'development']),
            'region': random.choice(['us-east-1', 'us-west-2', 'eu-west-1', 'ap-south-1'])
        }
    }
    return log

def connect_opensearch():
    """Create OpenSearch client connection."""
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False
    )
    return client

def send_log(client, index_name, log_data):
    """Send a single log entry to OpenSearch."""
    try:
        response = client.index(
            index=index_name,
            body=log_data,
            refresh=False
        )
        return response
    except Exception as e:
        print(f"Error sending log: {e}")
        return None

def main():
    """Main function to continuously send logs."""
    print("Connecting to OpenSearch...")
    client = connect_opensearch()

    # Test connection
    try:
        info = client.info()
        print(f"Connected to OpenSearch cluster: {info['cluster_name']}")
        print(f"Version: {info['version']['number']}")
    except Exception as e:
        print(f"Failed to connect to OpenSearch: {e}")
        return

    print("\nStarting to send random logs (Press Ctrl+C to stop)...\n")

    count = 0
    try:
        while True:
            # Generate random log
            log = generate_random_log()

            # Select random index
            index = random.choice(INDICES)

            # Send to OpenSearch
            response = send_log(client, index, log)

            if response:
                count += 1
                print(f"[{count}] Sent log to index '{index}' - Level: {log['level']}, Service: {log['service']}, Action: {log['action']}")

            # Random delay between 0.5 and 3 seconds
            time.sleep(random.uniform(0.5, 3.0))

    except KeyboardInterrupt:
        print(f"\n\nStopped. Total logs sent: {count}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
