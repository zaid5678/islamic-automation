"""
Islamic Content Automation System v2
FULLY AUTOMATED - Claude generates all content
One video per day, 100% free
"""

import os
import json
from datetime import datetime, timedelta
import requests
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as SACredentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import storage
import subprocess
import random
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# YouTube API
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "YOUR_YOUTUBE_CHANNEL_ID")

# Instagram API (optional)
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

GCP_PROJECT = "seraphic-ripple-496317-v1"
VERTEX_AI_URL = (
    f"https://us-central1-aiplatform.googleapis.com/v1/projects/{GCP_PROJECT}"
    f"/locations/us-central1/publishers/google/models/gemini-1.5-flash:generateContent"
)

# Google Cloud Storage (for temporary video hosting so Instagram can fetch it)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")

# Output directories
OUTPUT_DIR = "/tmp/islamic_videos"
MUSIC_DIR = f"{OUTPUT_DIR}/music"
IMAGE_DIR = f"{OUTPUT_DIR}/images"
VIDEO_DIR = f"{OUTPUT_DIR}/videos"

# Ensure directories exist
for directory in [MUSIC_DIR, IMAGE_DIR, VIDEO_DIR]:
    os.makedirs(directory, exist_ok=True)

# ============================================================================
# STEP 1: GENERATE CONTENT WITH GEMINI (FREE)
# ============================================================================

GEMINI_PROMPT = """Generate ONE Islamic teaching for a YouTube Short/Instagram Reel.

Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{
    "topic": "Topic name",
    "hadith_verse": "Quran X:X or Hadith reference",
    "hook_text": "One sentence that appears on screen - makes user want to read description",
    "image_theme": "mosque OR calligraphy OR nature OR islamic-art OR sunset",
    "full_teaching": "2-3 sentences explaining the Islamic concept deeply",
    "daily_lesson": "One actionable tip the user can do today",
    "youtube_description": "Full YouTube description with emoji, call to action, hashtags",
    "instagram_caption": "Instagram caption with emoji and hashtags"
}

Important:
- Make hook_text SHORT (one sentence, max 10 words)
- Make hook_text compelling (makes them want to read more)
- Make descriptions detailed and meaningful
- Focus on universal Islamic teachings (patience, gratitude, kindness, etc)
- Include relevant Quranic verses or Hadith
- Make it authentic and respectful
- Include monetization elements (affiliate suggestions in description)"""


def generate_islamic_content():
    """Calls Gemini via Vertex AI using the service account — no separate API key needed."""
    try:
        sa_creds = SACredentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        sa_creds.refresh(google.auth.transport.requests.Request())

        headers = {
            "Authorization": f"Bearer {sa_creds.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [{"role": "user", "parts": [{"text": GEMINI_PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.9},
        }
        response = requests.post(VERTEX_AI_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        response_text = (
            response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        )

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        content_data = json.loads(response_text.strip())
        print("✅ Generated content with Gemini (Vertex AI):")
        print(f"   Topic: {content_data['topic']}")
        print(f"   Hook: {content_data['hook_text']}")
        return content_data

    except Exception as e:
        print(f"❌ Error generating content with Gemini: {e}")
        return get_fallback_content()


def get_fallback_content():
    """
    Fallback content if Claude API fails
    Static Islamic teaching
    """
    return {
        "topic": "Trust in Allah",
        "hadith_verse": "Quran 65:3",
        "hook_text": "Allah provides for those who trust Him",
        "image_theme": "sky",
        "full_teaching": "Tawakkul means placing complete trust in Allah while doing your part. It doesn't mean sitting idle - it means working hard and then surrendering results to Allah. Many carry unnecessary stress trying to control outcomes. True peace comes from releasing that burden and trusting the Divine plan.",
        "daily_lesson": "Identify one worry. Do what you can to address it, then surrender the rest to Allah.",
        "youtube_description": """✨ TAWAKKUL (TRUST IN ALLAH) ✨

📖 Quran 65:3 - "Whoever trusts in Allah, then He will suffice him"

📚 FULL TEACHING:
Tawakkul is the art of trusting Allah completely while doing your part. The Prophet Muhammad (peace be upon him) said: "Trust in Allah, but tie your camel" - meaning work hard, then leave results to Allah.

💡 LESSON FOR TODAY:
Identify one worry you're carrying. Do what you can to address it, then surrender the rest to Allah. Feel the peace that comes with letting go.

---

🤲 SHARE THIS WITH SOMEONE WHO NEEDS IT

🔗 RESOURCES:
• Islamic Education Course: [AFFILIATE]
• Quran App: [AFFILIATE]
• Meditation for Muslims: [AFFILIATE]

📮 SUBSCRIBE FOR DAILY ISLAMIC TEACHINGS
🔔 TURN ON NOTIFICATIONS

#IslamicTeachings #Quran #Tawakkul #TrustInAllah #DailyReminder #IslamicWisdom""",
        "instagram_caption": """✨ Trust in Allah's plan ✨

📖 Quran 65:3

Full teaching in our bio 🔗

Save this 💾
Share with someone 🤲

#IslamicContent #DailyReminder #Quran #TrustInAllah"""
    }


# ============================================================================
# STEP 2: FETCH PEACEFUL ISLAMIC BACKGROUND IMAGE
# ============================================================================

def get_peaceful_islamic_image(theme="mosque"):
    """
    Fetches peaceful Islamic image from Unsplash
    """
    search_terms = {
        'mosque': 'peaceful mosque interior architecture',
        'calligraphy': 'Islamic calligraphy Quranic verses',
        'nature': 'serene nature landscape peaceful',
        'islamic-art': 'Islamic geometric patterns art',
        'sunset': 'golden sunset peaceful landscape'
    }
    
    query = search_terms.get(theme, search_terms['mosque'])
    
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
    if unsplash_key:
        try:
            url = f"https://api.unsplash.com/photos/random?query={query}&orientation=portrait&w=1080&h=1920"
            headers = {"Authorization": f"Client-ID {unsplash_key}"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                image_url = response.json()["urls"]["full"]
                image_response = requests.get(image_url, timeout=30)
                image_path = f"{IMAGE_DIR}/background_{datetime.now().timestamp()}.jpg"
                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                print(f"✅ Downloaded Islamic background: {image_path}")
                return image_path
        except Exception as e:
            print(f"⚠️ Could not fetch from Unsplash: {e}")
    else:
        print("⚠️ UNSPLASH_ACCESS_KEY not set — using generated background")
    
    # Fallback: Create simple background
    return create_fallback_image()


def create_fallback_image():
    """
    Creates simple Islamic-themed background using PIL
    """
    try:
        from PIL import Image, ImageDraw
        
        # Create 1080x1920 vertical image
        img = Image.new('RGB', (1080, 1920), color=(15, 32, 71))  # Deep Islamic blue
        draw = ImageDraw.Draw(img)
        
        # Add simple geometric pattern
        for i in range(0, 1920, 300):
            for j in range(0, 1080, 300):
                draw.ellipse(
                    [j-50, i-50, j+50, i+50],
                    outline=(184, 134, 11),
                    width=2
                )
        
        image_path = f"{IMAGE_DIR}/fallback_bg_{datetime.now().timestamp()}.jpg"
        img.save(image_path)
        
        print(f"✅ Created fallback background: {image_path}")
        return image_path
    
    except Exception as e:
        print(f"⚠️ Error creating fallback: {e}")
        return None


# ============================================================================
# STEP 3: CREATE TEXT OVERLAY
# ============================================================================

def create_text_overlay(hook_text, image_path):
    """
    Creates text overlay on background image
    Text: Hook text to make user read description
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Open background image
        img = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Load font
        try:
            font_size = 60
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add dark semi-transparent box at bottom for text
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        overlay_draw.rectangle(
            [0, 1400, 1080, 1920],
            fill=(0, 0, 0, 180)
        )
        
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Word wrap hook text
        text_lines = []
        words = hook_text.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > 1000:
                if current_line:
                    text_lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line = test_line
        
        if current_line:
            text_lines.append(current_line.strip())
        
        # Draw hook text
        y_offset = 1450
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            
            draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
            y_offset += 80
        
        # Add "Read below" prompt
        prompt_text = "📖 Read description below"
        bbox = draw.textbbox((0, 0), prompt_text, font=small_font)
        prompt_width = bbox[2] - bbox[0]
        prompt_x = (1080 - prompt_width) // 2
        
        draw.text((prompt_x, y_offset + 40), prompt_text, fill=(184, 134, 11), font=small_font)
        
        # Save
        text_overlay_path = f"{IMAGE_DIR}/text_overlay_{datetime.now().timestamp()}.png"
        img.save(text_overlay_path)
        
        print(f"✅ Created text overlay: {text_overlay_path}")
        return text_overlay_path
    
    except Exception as e:
        print(f"⚠️ Error creating text overlay: {e}")
        return image_path


# ============================================================================
# STEP 4: GET ROYALTY-FREE ISLAMIC MUSIC
# ============================================================================

def get_islamic_music():
    """
    Gets free Islamic peaceful music
    Uses YouTube Audio Library or free sources
    """
    
    # List of royalty-free Islamic music URLs
    music_sources = [
        {
            'name': 'islamic_peace_1.mp3',
            'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
        },
        {
            'name': 'islamic_peace_2.mp3',
            'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
        }
    ]
    
    selected = random.choice(music_sources)
    
    try:
        response = requests.get(selected['url'], timeout=15)
        
        if response.status_code == 200:
            music_path = f"{MUSIC_DIR}/{selected['name']}"
            
            with open(music_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded music: {music_path}")
            return music_path
    
    except Exception as e:
        print(f"⚠️ Could not download music: {e}")
    
    # Fallback: Create silence (you'll add music later)
    return create_silence_fallback()


def create_silence_fallback():
    """
    Creates silent audio fallback
    """
    try:
        silence_path = f"{MUSIC_DIR}/silence_60s.mp3"
        
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono',
            '-t', '60', '-q:a', '9', '-acodec', 'libmp3lame', silence_path,
            '-y'
        ], capture_output=True, timeout=10)
        
        print(f"✅ Created silence fallback: {silence_path}")
        return silence_path
    
    except Exception as e:
        print(f"⚠️ Error creating silence: {e}")
        return None


# ============================================================================
# STEP 5: CREATE VIDEO WITH FFMPEG
# ============================================================================

def create_video(background_image, music_path, output_path):
    """
    Creates 60-second video:
    - Background image with text
    - Islamic music
    - Fade effects
    - Optimized for YouTube Shorts (1080x1920)
    """
    try:
        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', background_image,
            '-i', music_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-t', '60',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
            '-b:v', '5000k',
            '-b:a', '128k',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Video created: {output_path}")
            return output_path
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return None
    
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        return None


# ============================================================================
# STEP 6: UPLOAD TO YOUTUBE
# ============================================================================

def _get_youtube_client():
    # Uses OAuth2 refresh token so uploads go to YOUR channel, not a service account.
    # Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN as secrets.
    # Run get_youtube_token.py once locally to generate the refresh token.
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def upload_to_youtube(video_path, title, description, tags):
    """
    Uploads video to YouTube Shorts using service account OAuth credentials.
    The service account must have the channel granted via domain-wide delegation
    or the channel must be a YouTube Brand Account linked to the GCP project.
    """
    try:
        youtube = _get_youtube_client()
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '26'  # Howto & Style
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        
        insert_request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = insert_request.execute()
        video_id = response['id']
        
        print(f"✅ Uploaded to YouTube!")
        print(f"   Video ID: {video_id}")
        print(f"   URL: https://www.youtube.com/shorts/{video_id}")
        
        return video_id
    
    except Exception as e:
        print(f"❌ Error uploading to YouTube: {e}")
        return None


# ============================================================================
# STEP 7: UPLOAD TO INSTAGRAM (OPTIONAL)
# ============================================================================

def upload_to_instagram(video_public_url, caption):
    """
    Uploads to Instagram Reels via the Graph API.
    video_public_url must be a publicly accessible HTTPS URL — Instagram
    cannot reach local file paths.  Host the video (e.g. S3, GCS, CDN)
    and pass the URL here, or set INSTAGRAM_VIDEO_HOST_URL to skip local upload.
    """
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        print("⚠️ Instagram upload skipped (not configured)")
        return None

    if not video_public_url or not video_public_url.startswith("https://"):
        print("⚠️ Instagram upload skipped (no public HTTPS video URL available)")
        return None

    try:
        # Step 1 — create media container
        container_url = f"https://graph.instagram.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        payload = {
            "video_url": video_public_url,
            "media_type": "REELS",
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        }
        response = requests.post(container_url, data=payload, timeout=30)

        if response.status_code != 200:
            print(f"⚠️ Instagram container creation failed: {response.text}")
            return None

        creation_id = response.json().get("id")

        # Step 2 — publish
        publish_url = f"https://graph.instagram.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
        publish_payload = {"creation_id": creation_id, "access_token": INSTAGRAM_ACCESS_TOKEN}
        pub_response = requests.post(publish_url, data=publish_payload, timeout=30)

        if pub_response.status_code == 200:
            print("✅ Posted to Instagram Reels!")
            return pub_response.json().get("id")
        else:
            print(f"⚠️ Instagram publish failed: {pub_response.text}")
            return None

    except Exception as e:
        print(f"⚠️ Instagram upload skipped: {e}")
        return None


# ============================================================================
# STEP 7.5: GCS TEMPORARY HOSTING (bridges Docker → Instagram)
# ============================================================================

GOOGLE_CREDENTIALS_PATH = "/app/google_credentials.json"


def _gcs_client():
    creds = SACredentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return storage.Client(credentials=creds, project=creds.project_id)


def upload_video_to_gcs(video_path):
    """
    Uploads the video to GCS and returns a signed URL valid for 1 hour.
    Instagram will fetch the video from this URL.
    Returns (signed_url, blob_name) or (None, None) if GCS is not configured.
    """
    if not GCS_BUCKET_NAME:
        print("⚠️ GCS_BUCKET_NAME not set — Instagram upload will be skipped")
        return None, None

    try:
        client = _gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob_name = f"islamic-videos/{os.path.basename(video_path)}"
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(video_path, content_type="video/mp4")
        print(f"✅ Uploaded video to GCS: gs://{GCS_BUCKET_NAME}/{blob_name}")

        sa_creds = SACredentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET",
            credentials=sa_creds,
        )
        return signed_url, blob_name

    except Exception as e:
        print(f"❌ GCS upload failed: {e}")
        return None, None


def delete_from_gcs(blob_name):
    """Removes the temporary video from GCS after Instagram has fetched it."""
    if not GCS_BUCKET_NAME or not blob_name:
        return
    try:
        client = _gcs_client()
        client.bucket(GCS_BUCKET_NAME).blob(blob_name).delete()
        print(f"✅ Deleted temporary GCS file: {blob_name}")
    except Exception as e:
        print(f"⚠️ Could not delete GCS file: {e}")


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def main():
    """
    Main function - daily fully automated run
    """
    
    print("\n" + "="*60)
    print("🕌 ISLAMIC CONTENT AUTOMATION - DAILY RUN")
    print("="*60 + "\n")
    
    # STEP 1: Generate content with Claude
    print("📝 Step 1: Generating Islamic content with Claude AI...")
    content_data = generate_islamic_content()
    
    if not content_data:
        print("❌ Failed to generate content. Exiting.")
        return False
    
    # STEP 2: Get background image
    print(f"\n🖼️  Step 2: Fetching Islamic background image...")
    background_image = get_peaceful_islamic_image(content_data.get('image_theme', 'mosque'))
    
    if not background_image:
        print("❌ Failed to get background. Exiting.")
        return False
    
    # STEP 3: Create text overlay
    print("\n📝 Step 3: Creating text overlay...")
    text_image = create_text_overlay(content_data['hook_text'], background_image)
    
    # STEP 4: Get music
    print("\n🎵 Step 4: Getting Islamic music...")
    music_path = get_islamic_music()
    
    if not music_path:
        print("❌ Failed to get music. Exiting.")
        return False
    
    # STEP 5: Create video
    print("\n🎬 Step 5: Creating video...")
    video_timestamp = datetime.now().timestamp()
    video_path = f"{VIDEO_DIR}/islamic_teaching_{video_timestamp}.mp4"
    
    video = create_video(text_image, music_path, video_path)
    
    if not video:
        print("❌ Failed to create video. Exiting.")
        return False
    
    # STEP 6: Upload to YouTube
    print("\n▶️  Step 6: Uploading to YouTube...")
    youtube_title = f"{content_data['topic']} - Islamic Teaching"
    youtube_tags = ['Islamic', 'Hadith', 'Quran', 'DailyReminder', 'IslamicTeachings']
    
    youtube_id = upload_to_youtube(
        video_path,
        youtube_title,
        content_data['youtube_description'],
        youtube_tags
    )
    
    # STEP 7: Upload to GCS → Instagram → clean up GCS
    print("\n📸 Step 7: Uploading to Instagram Reels via GCS...")
    gcs_url, gcs_blob = upload_video_to_gcs(video_path)
    instagram_id = upload_to_instagram(gcs_url, content_data['instagram_caption'])
    delete_from_gcs(gcs_blob)

    # Cleanup local files
    print("\n🧹 Cleaning up temporary files...")
    try:
        os.remove(video_path)
        os.remove(text_image)
        print("✅ Cleanup complete")
    except:
        pass
    
    print("\n" + "="*60)
    print("✅ DAILY AUTOMATION COMPLETE!")
    print(f"   Topic: {content_data['topic']}")
    print(f"   YouTube: https://www.youtube.com/shorts/{youtube_id}")
    if instagram_id:
        print(f"   Instagram: Posted")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
