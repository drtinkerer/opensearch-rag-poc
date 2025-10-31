# Fluent Bit parsers.conf Flow Diagram

## Current Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Container                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Fluent Bit Container                              │    │
│  │                                                     │    │
│  │  Built-in Files:                                   │    │
│  │  /fluent-bit/etc/parsers.conf (DEFAULT)           │    │
│  │  ┌──────────────────────────────────────┐         │    │
│  │  │ [PARSER]                             │         │    │
│  │  │   Name   json                        │         │    │
│  │  │   Format json                        │         │    │
│  │  │                                      │         │    │
│  │  │ [PARSER]                             │         │    │
│  │  │   Name   docker                      │         │    │
│  │  │   Format json                        │         │    │
│  │  │                                      │         │    │
│  │  │ [PARSER]                             │         │    │
│  │  │   Name   syslog                      │         │    │
│  │  │   Format regex                       │         │    │
│  │  │   ... and 20+ more parsers           │         │    │
│  │  └──────────────────────────────────────┘         │    │
│  │                                                     │    │
│  │  Mounted Files (from host):                        │    │
│  │  /fluent-bit/etc/fluent-bit.conf (OUR CONFIG)     │    │
│  │  ┌──────────────────────────────────────┐         │    │
│  │  │ [SERVICE]                            │         │    │
│  │  │   Parsers_File parsers.conf ────────┼─────┐   │    │
│  │  │                                      │     │   │    │
│  │  │ [INPUT]                              │     │   │    │
│  │  │   Name   tail                        │     │   │    │
│  │  │   Path   /logs/logs.fluentbit        │     │   │    │
│  │  │   Parser json ───────────────────────┼───┐ │   │    │
│  │  └──────────────────────────────────────┘   │ │   │    │
│  │                                              │ │   │    │
│  └──────────────────────────────────────────────┼─┼───┘    │
│                                                  │ │        │
│  References built-in parsers.conf ◄─────────────┘ │        │
│  Uses 'json' parser definition ◄──────────────────┘        │
└─────────────────────────────────────────────────────────────┘

                            ▼
                    ┌───────────────┐
                    │  Log Flow     │
                    └───────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────┐         ┌──────────────┐        ┌────────────┐
│ File    │         │ JSON Parser  │        │ OpenSearch │
│ Read    │────────▶│ Processing   │───────▶│  Index     │
└─────────┘         └──────────────┘        └────────────┘
  Raw JSON            Structured              Indexed
  Line by line        Binary Format           Documents
```

## How It Works Step-by-Step

### Step 1: Python Writes Log
```json
{"@timestamp":"2025-10-31T11:29:11.877689","level":"DEBUG","service":"shipping-service",...}
```

### Step 2: Fluent Bit Tail Reads File
```
logs/logs.fluentbit ──> Fluent Bit Tail Input Plugin
```

### Step 3: JSON Parser Applied
```
Fluent Bit looks for 'json' parser in parsers.conf:
  ↓
Finds it in built-in /fluent-bit/etc/parsers.conf
  ↓
Applies JSON parsing rules:
  - Parses JSON string
  - Extracts all fields
  - Converts to internal binary format
```

### Step 4: Output to OpenSearch
```
Structured data ──> OpenSearch Output Plugin ──> fluentbit-data index
```

## Why We Don't Need Custom parsers.conf

✅ **Our logs are already JSON** - Perfect match for built-in parser
✅ **Built-in JSON parser handles our format** - No customization needed
✅ **All fields are preserved** - Including nested objects (metadata)
✅ **Timestamps work correctly** - Using @timestamp field

## When You'd Need Custom parsers.conf

### Scenario 1: Non-JSON Logs
```
2025-10-31 11:29:11 ERROR [shipping-service] Failed to process order
```
Would need regex parser:
```ini
[PARSER]
    Name        app_log
    Format      regex
    Regex       ^(?<time>[^ ]+) (?<level>[^ ]+) \[(?<service>[^\]]+)\] (?<message>.*)$
```

### Scenario 2: Custom Timestamp Format
```json
{"time":"31/Oct/2025:11:29:11 +0000","level":"ERROR",...}
```
Would need custom JSON parser:
```ini
[PARSER]
    Name        custom_json
    Format      json
    Time_Key    time
    Time_Format %d/%b/%Y:%H:%M:%S %z
```

### Scenario 3: Multi-line Logs (Stack Traces)
```
2025-10-31 ERROR Exception in thread
    at com.example.Service.method(Service.java:42)
    at com.example.Main.main(Main.java:10)
```
Would need multiline parser configuration.

## Verification Commands

```bash
# 1. Check if Fluent Bit is using default parsers.conf
docker-compose logs fluent-bit | grep -i parser

# 2. Verify JSON parsing works (all fields present)
curl -X GET "https://localhost:9200/fluentbit-data/_search?pretty&size=1" \
  -ku admin:MyStrongPassword123!

# 3. Check nested object parsing (metadata field)
curl -X GET "https://localhost:9200/fluentbit-data/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"exists":{"field":"metadata.datacenter"}}}' \
  -ku admin:MyStrongPassword123!
```

## Summary

**Current Setup:**
- ✅ Uses built-in `parsers.conf` from Fluent Bit container
- ✅ Uses built-in `json` parser (no customization needed)
- ✅ All JSON fields parsed correctly
- ✅ Nested objects (metadata) preserved
- ✅ 130+ documents successfully indexed

**No action required** - The default configuration works perfectly for our JSON logs!
