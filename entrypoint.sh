#!/bin/sh
set -e

# Write google_credentials.json from the env var at container startup.
# In CI/CD, set GOOGLE_CREDENTIALS_JSON to the contents of the JSON file.
if [ -n "$GOOGLE_CREDENTIALS_JSON" ]; then
    # Use Python to write the file so the private key \n sequences are preserved correctly
    python3 -c "import os; open('/app/google_credentials.json', 'w').write(os.environ['GOOGLE_CREDENTIALS_JSON'])"
else
    echo "WARNING: GOOGLE_CREDENTIALS_JSON is not set. Google API calls will fail."
fi

exec python islamic_automation_claude.py
