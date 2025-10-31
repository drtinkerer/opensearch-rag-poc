# Fluent Bit Configuration Explained

## How parsers.conf Works in the Container

### The Current Setup

In our `fluent-bit.conf`, we reference `parsers.conf`:

```ini
[SERVICE]
    Parsers_File parsers.conf  # References the default parsers.conf
```

And we use the JSON parser:
```ini
[INPUT]
    Parser json  # Uses the built-in 'json' parser
```

### Where is parsers.conf?

The Fluent Bit container image includes a **default parsers.conf** file at:
```
/fluent-bit/etc/parsers.conf
```

This file is **built into the container image** and contains many pre-configured parsers including:
- json
- docker
- syslog
- apache
- nginx
- and many more

### The JSON Parser

The built-in JSON parser definition looks like:
```ini
[PARSER]
    Name        json
    Format      json
    Time_Key    time
    Time_Format %d/%b/%Y:%H:%M:%S %z
```

**What it does:**
- Parses JSON-formatted log lines
- Extracts the `time` field as the timestamp
- Converts JSON to Fluent Bit's internal binary format

### Our Current Configuration Flow

```
1. Python writes JSON logs to: logs/logs.fluentbit
   Example: {"@timestamp": "2025-10-31T...", "level": "INFO", ...}

2. Fluent Bit tail input reads the file
   - Uses built-in 'json' parser from default parsers.conf
   - Automatically parses JSON structure

3. Fluent Bit sends to OpenSearch
   - All fields are preserved
   - Indexed in 'fluentbit-data'
```

### Why It Works Without Custom parsers.conf

The JSON parser is **built-in** and available by default. When we specify:
```ini
Parsers_File parsers.conf
```

Fluent Bit looks for this file in:
1. Current directory
2. Default location: `/fluent-bit/etc/parsers.conf`

Since we don't mount a custom `parsers.conf`, it uses the **default one from the container**, which already has the JSON parser defined.

## When You Need a Custom parsers.conf

You would create your own `parsers.conf` if you need to:

### 1. Custom Time Format
```ini
[PARSER]
    Name        my_json
    Format      json
    Time_Key    @timestamp
    Time_Format %Y-%m-%dT%H:%M:%S.%L
    Time_Keep   On
```

### 2. Custom Regex Parser
```ini
[PARSER]
    Name        custom_app_log
    Format      regex
    Regex       ^(?<time>[^ ]*) (?<level>[^ ]*) (?<message>.*)$
    Time_Key    time
    Time_Format %Y-%m-%dT%H:%M:%S
```

### 3. Multi-line Logs
```ini
[PARSER]
    Name        java_multiline
    Format      regex
    Regex       /^(?<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*$/
```

## How to Add Custom parsers.conf

If you want to customize parsers, update `docker-compose.yml`:

```yaml
fluent-bit:
  image: fluent/fluent-bit:latest
  volumes:
    - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
    - ./parsers.conf:/fluent-bit/etc/parsers.conf  # Mount custom parsers
    - ./logs:/logs
```

Then create `parsers.conf` with your custom parser definitions.

## Current Status: Everything Working ✓

Our setup works perfectly because:
1. ✓ We use the built-in `json` parser
2. ✓ Default `parsers.conf` is in the container
3. ✓ Our logs are already valid JSON
4. ✓ Fluent Bit successfully parses and forwards logs

**No custom parsers.conf needed for basic JSON parsing!**

## Verification

Check that JSON parser is working:
```bash
# View logs in OpenSearch - all fields should be parsed
curl -X GET "https://localhost:9200/fluentbit-data/_search?pretty&size=1" \
  -ku admin:MyStrongPassword123!

# Should see structured JSON with all fields:
# - @timestamp
# - level
# - service
# - action
# - metadata (nested object)
# etc.
```

## Default Parsers Available

The container includes parsers for:
- **json** - Our current parser
- docker
- syslog-rfc5424
- syslog-rfc3164
- apache2
- apache_error
- nginx
- mongodb
- And many more...

See full list: https://github.com/fluent/fluent-bit/blob/master/conf/parsers.conf
