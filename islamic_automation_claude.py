"""
Islamic Automation — main entry point.
Replace this file with your actual automation logic.

Expected environment variables (all required):
  YOUTUBE_API_KEY
  YOUTUBE_CHANNEL_ID
  CLAUDE_API_KEY
  INSTAGRAM_BUSINESS_ACCOUNT_ID
  INSTAGRAM_ACCESS_TOKEN
  GOOGLE_CREDENTIALS_JSON   (full JSON content of service account key)
"""

import os
import sys

REQUIRED_ENV_VARS = [
    "YOUTUBE_API_KEY",
    "YOUTUBE_CHANNEL_ID",
    "CLAUDE_API_KEY",
    "INSTAGRAM_BUSINESS_ACCOUNT_ID",
    "INSTAGRAM_ACCESS_TOKEN",
    "GOOGLE_CREDENTIALS_JSON",
]


def check_env():
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        print(f"ERROR: missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def main():
    check_env()
    print("All environment variables present. Add your automation logic here.")


if __name__ == "__main__":
    main()
