# Quick Reference

## Start Everything
```bash
docker-compose up -d
```

## Log Generation Methods

### Method 1: Direct API (send_logs.py)
```bash
python3 send_logs.py
```
- Creates indices: `logs-app`, `logs-system`, `logs-security`, `logs-performance`, `logs-audit`
- Direct OpenSearch API calls

### Method 2: File + Fluent Bit (send_logs_to_file.py)
```bash
python3 send_logs_to_file.py
```
- Writes to: `logs/logs.fluentbit`
- Fluent Bit forwards to: `fluentbit-data` index

## Check Status

### Containers
```bash
docker-compose ps
```

### Fluent Bit Logs
```bash
docker-compose logs fluent-bit
docker-compose logs -f fluent-bit  # Follow
```

### OpenSearch Health
```bash
curl -X GET "https://localhost:9200/_cluster/health?pretty" -ku admin:MyStrongPassword123!
```

### List All Indices
```bash
curl -X GET "https://localhost:9200/_cat/indices?v" -ku admin:MyStrongPassword123!
```

### Count Documents
```bash
# Fluent Bit data
curl -X GET "https://localhost:9200/fluentbit-data/_count" -ku admin:MyStrongPassword123!

# App logs
curl -X GET "https://localhost:9200/logs-app/_count" -ku admin:MyStrongPassword123!
```

### Search Logs
```bash
# Fluent Bit logs
curl -X GET "https://localhost:9200/fluentbit-data/_search?pretty&size=2" -ku admin:MyStrongPassword123!

# App logs
curl -X GET "https://localhost:9200/logs-app/_search?pretty&size=2" -ku admin:MyStrongPassword123!

# Search by field
curl -X GET "https://localhost:9200/fluentbit-data/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match": {"level": "ERROR"}}}' \
  -ku admin:MyStrongPassword123!
```

## Access Points

- **OpenSearch API**: https://localhost:9200
- **OpenSearch Dashboards**: http://localhost:5601
- **Performance Analyzer**: http://localhost:9600

## Credentials

- Username: `admin`
- Password: `MyStrongPassword123!` (or from `.env`)

## Stop & Clean

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes (delete all data)
```bash
docker-compose down -v
```

### Clean log files
```bash
rm -f logs/logs.fluentbit
```

## Troubleshooting

### Fluent Bit not forwarding logs
```bash
# Check if log file exists and has content
ls -lh logs/logs.fluentbit
tail -f logs/logs.fluentbit

# Check Fluent Bit container logs
docker-compose logs fluent-bit

# Restart Fluent Bit
docker-compose restart fluent-bit
```

### OpenSearch connection issues
```bash
# Check if container is running
docker-compose ps

# Check OpenSearch logs
docker-compose logs opensearch

# Test connection
curl -k -u admin:MyStrongPassword123! https://localhost:9200
```

## File Locations

- Docker Compose: `docker-compose.yml`
- Fluent Bit config: `fluent-bit.conf`
- Log file directory: `logs/`
- Log file: `logs/logs.fluentbit`
- Python scripts:
  - `send_logs.py` - Direct API
  - `send_logs_to_file.py` - File-based
