#!/bin/bash
# Start OpenSearch and begin sending logs

echo "Starting OpenSearch and Dashboards..."
docker-compose up -d

echo "Waiting for OpenSearch to be ready..."
until curl -s -k -u admin:MyStrongPassword123! https://localhost:9200 > /dev/null 2>&1; do
    echo "Waiting..."
    sleep 2
done

echo "OpenSearch is ready!"
echo ""
echo "Services:"
echo "  - OpenSearch: https://localhost:9200"
echo "  - Dashboards: http://localhost:5601"
echo ""
echo "Starting log generator..."
python3 send_logs.py
