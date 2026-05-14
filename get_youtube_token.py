"""
Run this script ONCE locally to get your YouTube OAuth refresh token.
The refresh token never expires (unless you revoke it), so you only need to do this once.

Steps:
  1. Go to https://console.cloud.google.com
  2. Select your project → APIs & Services → Credentials
  3. Click "Create Credentials" → "OAuth client ID"
  4. Application type: Desktop app → give it any name → Create
  5. Download the JSON → copy client_id and client_secret into the prompts below
  6. Run:  python get_youtube_token.py
  7. A browser window opens — log in as the YouTube channel owner
  8. Copy the printed YOUTUBE_REFRESH_TOKEN into GitHub Secrets
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID     = input("Paste your OAuth client_id:     ").strip()
CLIENT_SECRET = input("Paste your OAuth client_secret: ").strip()

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(
    client_config,
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)

creds = flow.run_local_server(port=0)

print("\n" + "=" * 60)
print("Add these three values to GitHub Secrets:")
print("=" * 60)
print(f"YOUTUBE_CLIENT_ID     = {CLIENT_ID}")
print(f"YOUTUBE_CLIENT_SECRET = {CLIENT_SECRET}")
print(f"YOUTUBE_REFRESH_TOKEN = {creds.refresh_token}")
print("=" * 60)
