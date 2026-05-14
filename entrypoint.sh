#!/bin/sh
set -e

# Write google_credentials.json from the env var at container startup.
# In CI/CD, set GOOGLE_CREDENTIALS_JSON to the contents of the JSON file.
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    echo "$GOOGLE_CREDENTIALS_JSON" > /app/google_credentials.json
else
    echo "WARNING: GOOGLE_CREDENTIALS_JSON is not set. Google API calls will fail."
fi

exec python islamic_automation_claude.py
