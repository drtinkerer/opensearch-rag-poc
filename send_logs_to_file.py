#!/usr/bin/env python3
"""
Continuously writes random JSON logs to logs.fluentbit file for Fluent Bit to process.
"""
import random
import time
import json
from datetime import datetime

# Log data generators
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
SERVICES = ['payment-service', 'user-service', 'order-service', 'inventory-service', 'shipping-service', 'analytics-service']
ACTIONS = ['process_payment', 'create_order', 'update_inventory', 'ship_package', 'user_registration', 'data_analysis']
USERS = ['customer_001', 'customer_002', 'customer_003', 'admin_001', 'service_account', 'bot_user']
STATUS_CODES = [200, 201, 400, 401, 403, 404, 500, 502, 503]
ENDPOINTS = ['/api/v1/payments', '/api/v1/orders', '/api/v1/users', '/api/v1/inventory', '/api/v1/shipments']

LOG_FILE = 'logs/logs.fluentbit'

def generate_random_log():
    """Generate a random log entry."""
    log = {
        '@timestamp': datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        'level': random.choice(LOG_LEVELS),
        'service': random.choice(SERVICES),
        'action': random.choice(ACTIONS),
        'user': random.choice(USERS),
        'endpoint': random.choice(ENDPOINTS),
        'method': random.choice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
        'status_code': random.choice(STATUS_CODES),
        'response_time_ms': random.randint(5, 3000),
        'message': f"Processing {random.choice(ACTIONS)} request via Fluent Bit",
        'request_id': f"fb_req_{random.randint(100000, 999999)}",
        'source_ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        'bytes_sent': random.randint(100, 50000),
        'metadata': {
            'app_version': f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,20)}",
            'environment': random.choice(['production', 'staging', 'development']),
            'datacenter': random.choice(['dc-us-east', 'dc-us-west', 'dc-eu-central', 'dc-asia-pacific']),
            'instance_id': f"i-{random.randint(1000, 9999)}"
        }
    }
    return log

def write_log_to_file(log_data):
    """Write a single log entry to the log file as JSON."""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_data) + '\n')
            f.flush()
        return True
    except Exception as e:
        print(f"Error writing log: {e}")
        return False

def main():
    """Main function to continuously write logs to file."""
    print(f"Writing logs to {LOG_FILE} (Press Ctrl+C to stop)...\n")

    count = 0
    try:
        while True:
            # Generate random log
            log = generate_random_log()

            # Write to file
            if write_log_to_file(log):
                count += 1
                print(f"[{count}] Wrote log - Level: {log['level']}, Service: {log['service']}, Action: {log['action']}, Status: {log['status_code']}")

            # Random delay between 0.5 and 2 seconds
            time.sleep(random.uniform(0.5, 2.0))

    except KeyboardInterrupt:
        print(f"\n\nStopped. Total logs written: {count}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
