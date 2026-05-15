"""
Islamic Content Automation System v2
FULLY AUTOMATED - Claude generates all content
One video per day, 100% free
"""

import os
import json
from datetime import datetime, timedelta
import requests
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

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Google Cloud Storage (for temporary video hosting so Instagram can fetch it)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

FONT_BOLD    = "/app/fonts/Poppins-Bold.ttf"
FONT_SEMIBOLD = "/app/fonts/Poppins-SemiBold.ttf"
FONT_REGULAR  = "/app/fonts/Poppins-Regular.ttf"

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
    """Calls Groq (free) to generate Islamic content using Llama 3."""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": GEMINI_PROMPT}],
            "max_tokens": 1024,
            "temperature": 0.9,
        }
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        response_text = response.json()["choices"][0]["message"]["content"].strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        content_data = json.loads(response_text.strip())
        print("✅ Generated content with Groq (Llama 3):")
        print(f"   Topic: {content_data['topic']}")
        print(f"   Hook: {content_data['hook_text']}")
        return content_data

    except Exception as e:
        print(f"❌ Error generating content with Groq: {e}")
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
# STEP 2: FETCH ISLAMIC BACKGROUND IMAGE
# ============================================================================

PEXELS_QUERIES = [
    "kaaba mecca pilgrimage",
    "grand mosque islamic architecture",
    "mosque interior dome",
    "masjid al haram aerial",
    "islamic architecture golden",
    "nature peaceful sunrise mountains",
]


def get_peaceful_islamic_image(theme="mosque"):
    # 1. Try Pexels (best quality Islamic content)
    if PEXELS_API_KEY:
        query = random.choice(PEXELS_QUERIES)
        try:
            headers = {"Authorization": PEXELS_API_KEY}
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": query, "orientation": "portrait", "per_page": 10},
                timeout=15,
            )
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                if photos:
                    photo = random.choice(photos)
                    img_url = photo["src"]["large2x"]
                    img_data = requests.get(img_url, timeout=30).content
                    path = f"{IMAGE_DIR}/bg_{datetime.now().timestamp()}.jpg"
                    with open(path, "wb") as f:
                        f.write(img_data)
                    print(f"✅ Downloaded Pexels background: {query}")
                    return path
        except Exception as e:
            print(f"⚠️ Pexels failed: {e}")

    # 2. Try Unsplash
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
    if unsplash_key:
        search_terms = {
            "mosque": "mosque architecture interior",
            "calligraphy": "islamic calligraphy art",
            "nature": "peaceful nature sunrise",
            "islamic-art": "islamic geometric architecture",
            "sunset": "golden sunset peaceful",
        }
        query = search_terms.get(theme, "mosque architecture")
        try:
            r = requests.get(
                "https://api.unsplash.com/photos/random",
                headers={"Authorization": f"Client-ID {unsplash_key}"},
                params={"query": query, "orientation": "portrait"},
                timeout=15,
            )
            if r.status_code == 200:
                img_url = r.json()["urls"]["full"]
                img_data = requests.get(img_url, timeout=30).content
                path = f"{IMAGE_DIR}/bg_{datetime.now().timestamp()}.jpg"
                with open(path, "wb") as f:
                    f.write(img_data)
                print(f"✅ Downloaded Unsplash background")
                return path
        except Exception as e:
            print(f"⚠️ Unsplash failed: {e}")

    print("⚠️ No image API key set — using generated background")
    return create_fallback_image()


def create_fallback_image():
    """Professional Islamic-themed gradient background."""
    try:
        from PIL import Image, ImageDraw
        import math

        W, H = 1080, 1920
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Deep teal-to-midnight gradient
        for y in range(H):
            t = y / H
            r = int(10 + t * 5)
            g = int(40 + t * 10)
            b = int(60 + t * 20)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Islamic 8-pointed star pattern (subtle, gold)
        GOLD = (180, 140, 40)
        star_positions = [(W // 2, H // 4), (W // 2, H // 2), (W // 2, H * 3 // 4)]
        for cx, cy in star_positions:
            for i in range(8):
                angle = math.radians(i * 45)
                x1 = cx + int(120 * math.cos(angle))
                y1 = cy + int(120 * math.sin(angle))
                x2 = cx + int(55 * math.cos(angle + math.radians(22.5)))
                y2 = cy + int(55 * math.sin(angle + math.radians(22.5)))
                draw.line([(cx, cy), (x1, y1)], fill=GOLD, width=1)
                draw.line([(cx, cy), (x2, y2)], fill=GOLD, width=1)
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=GOLD)

        path = f"{IMAGE_DIR}/fallback_bg_{datetime.now().timestamp()}.jpg"
        img.save(path, quality=95)
        print(f"✅ Created fallback background")
        return path

    except Exception as e:
        print(f"⚠️ Error creating fallback: {e}")
        return None


# ============================================================================
# STEP 3: CREATE TEXT OVERLAY — Professional social media style
# ============================================================================

def _load_fonts():
    """Load Poppins fonts, fall back to DejaVu."""
    from PIL import ImageFont
    sizes = {"bold": 72, "semibold": 52, "regular": 40}
    try:
        return {
            "title":  ImageFont.truetype(FONT_BOLD,     sizes["bold"]),
            "verse":  ImageFont.truetype(FONT_SEMIBOLD, sizes["semibold"]),
            "cta":    ImageFont.truetype(FONT_REGULAR,  sizes["regular"]),
        }
    except Exception:
        try:
            base = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
            return {
                "title": ImageFont.truetype(f"{base}-Bold.ttf",    sizes["bold"]),
                "verse": ImageFont.truetype(f"{base}.ttf",         sizes["semibold"]),
                "cta":   ImageFont.truetype(f"{base}.ttf",         sizes["regular"]),
            }
        except Exception:
            d = ImageFont.load_default()
            return {"title": d, "verse": d, "cta": d}


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_text_overlay(hook_text, hadith_verse, image_path):
    """
    Professional TikTok / Instagram Reels style overlay.
    Layout:
      - Full background image, resized to 1080x1920
      - Subtle dark gradient (stronger at bottom)
      - Center: gold decorative lines + large white hook text + verse ref
      - Bottom: CTA "Read description for the full teaching"
    """
    try:
        from PIL import Image, ImageDraw

        W, H = 1080, 1920
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((W, H), Image.LANCZOS)

        # Gradient overlay — transparent top, darkening toward bottom
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for y in range(H):
            alpha = int(min(200, (y / H) ** 1.4 * 230))
            od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
        # Slight center darkening for text readability
        od.rectangle([0, H // 3, W, H * 2 // 3], fill=(0, 0, 0, 60))
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)
        fonts = _load_fonts()

        GOLD  = (212, 175, 55)
        WHITE = (255, 255, 255)
        LGOLD = (255, 220, 100)

        CENTER_X = W // 2
        LINE_W   = 700   # max text width

        # ── Hook text (centered, large, bold) ─────────────────────────────
        lines     = _wrap_text(draw, hook_text, fonts["title"], LINE_W)
        line_h    = 88
        block_h   = len(lines) * line_h
        text_top  = H // 2 - block_h // 2 - 20

        # Gold rule above
        rule_y = text_top - 55
        draw.line([(CENTER_X - 260, rule_y), (CENTER_X + 260, rule_y)], fill=GOLD, width=2)
        draw.text((CENTER_X, rule_y - 22), "✦", font=fonts["cta"], fill=GOLD, anchor="mm")

        for i, line in enumerate(lines):
            y = text_top + i * line_h
            # Shadow
            draw.text((CENTER_X + 2, y + 2), line, font=fonts["title"],
                      fill=(0, 0, 0, 160), anchor="mt")
            # Text
            draw.text((CENTER_X, y), line, font=fonts["title"],
                      fill=WHITE, anchor="mt")

        # Gold rule below
        rule_y2 = text_top + block_h + 30
        draw.line([(CENTER_X - 260, rule_y2), (CENTER_X + 260, rule_y2)], fill=GOLD, width=2)
        draw.text((CENTER_X, rule_y2 + 22), "✦", font=fonts["cta"], fill=GOLD, anchor="mm")

        # ── Hadith / verse reference ───────────────────────────────────────
        draw.text((CENTER_X, rule_y2 + 75), hadith_verse,
                  font=fonts["verse"], fill=LGOLD, anchor="mm")

        # ── Bottom CTA ────────────────────────────────────────────────────
        cta_y = H - 200
        draw.line([(80, cta_y - 35), (W - 80, cta_y - 35)],
                  fill=(255, 255, 255, 60), width=1)
        draw.text((CENTER_X, cta_y), "Read description for the full teaching",
                  font=fonts["cta"], fill=WHITE, anchor="mm")
        draw.text((CENTER_X, cta_y + 55), "↓  Follow for daily reminders  ↓",
                  font=fonts["cta"], fill=LGOLD, anchor="mm")

        out = f"{IMAGE_DIR}/text_overlay_{datetime.now().timestamp()}.png"
        img.convert("RGB").save(out, quality=95)
        print(f"✅ Created professional text overlay")
        return out

    except Exception as e:
        print(f"⚠️ Error creating text overlay: {e}")
        return image_path


# ============================================================================
# STEP 4: GET NASHEED / ISLAMIC MUSIC
# ============================================================================

# Public-domain / Creative Commons nasheeds from Archive.org
NASHEED_SOURCES = [
    {
        "name": "tala_al_badru.mp3",
        "url": "https://archive.org/download/TalaAlBadruAlayna/Tala%20Al%20Badru%20Alayna.mp3",
    },
    {
        "name": "nasheed_allahu.mp3",
        "url": "https://archive.org/download/NasheedAllahu/nasheed.mp3",
    },
    {
        "name": "peaceful_nasheed.mp3",
        "url": "https://archive.org/download/IslamicNasheedCollection/01.mp3",
    },
]


def get_islamic_music():
    random.shuffle(NASHEED_SOURCES)
    for source in NASHEED_SOURCES:
        try:
            r = requests.get(source["url"], timeout=20, stream=True)
            if r.status_code == 200:
                path = f"{MUSIC_DIR}/{source['name']}"
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ Downloaded nasheed: {source['name']}")
                return path
        except Exception:
            continue

    print("⚠️ Nasheed download failed — generating peaceful ambient music")
    return create_ambient_music()


def create_ambient_music():
    """
    Generates a peaceful Islamic-style ambient drone using ffmpeg.
    Uses 432 Hz + harmonics — sounds meditative and calming.
    """
    try:
        path = f"{MUSIC_DIR}/ambient_islamic.mp3"
        # Three-frequency harmonic chord (432 Hz, 528 Hz, 639 Hz)
        # with slow fade in/out — sounds like a gentle oud/nay drone
        subprocess.run([
            "ffmpeg",
            "-f", "lavfi",
            "-i", "sine=frequency=432:duration=65",
            "-f", "lavfi",
            "-i", "sine=frequency=528:duration=65",
            "-f", "lavfi",
            "-i", "sine=frequency=639:duration=65",
            "-filter_complex",
            "[0][1][2]amix=inputs=3:duration=first,"
            "afade=t=in:st=0:d=4,"
            "afade=t=out:st=60:d=4,"
            "volume=0.25",
            "-codec:a", "libmp3lame", "-q:a", "4",
            "-y", path,
        ], capture_output=True, timeout=30)
        print(f"✅ Generated ambient music")
        return path
    except Exception as e:
        print(f"⚠️ Error generating ambient music: {e}")
        return None


# ============================================================================
# STEP 5: CREATE VIDEO WITH FFMPEG
# ============================================================================

def create_video(background_image, music_path, output_path):
    """
    Creates 60-second YouTube Shorts / Reels video.
    - Slow Ken Burns zoom (1.0 → 1.08 over 60s) makes static images feel alive
    - Fade in/out on both video and audio
    - 1080x1920, high quality
    """
    try:
        # Ken Burns: slow zoom from center, 60 s × 25 fps = 1500 frames
        # zoompan: z = zoom level, d = duration in frames, x/y keep center
        vf = (
            "scale=8000:-1,"                          # upscale so zoompan has room
            "zoompan="
            "z='min(zoom+0.0003,1.08)':"
            "d=1500:"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "s=1080x1920,"
            "setsar=1,"
            "fade=t=in:st=0:d=1,"                     # 1-second fade in
            "fade=t=out:st=58:d=2"                    # 2-second fade out
        )
        cmd = [
            "ffmpeg",
            "-loop", "1",
            "-framerate", "25",
            "-i", background_image,
            "-i", music_path,
            "-vf", vf,
            "-af", "afade=t=in:st=0:d=2,afade=t=out:st=57:d=3",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", "60",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-y", output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"✅ Video created: {output_path}")
            return output_path
        else:
            print(f"❌ FFmpeg error: {result.stderr[-500:]}")
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
    text_image = create_text_overlay(
        content_data['hook_text'],
        content_data.get('hadith_verse', ''),
        background_image,
    )
    
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
