FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg wget python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip install -q yt-dlp

# Download Poppins font (clean, professional, widely used on social media)
RUN mkdir -p /app/fonts && \
    wget -q "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf" -O /app/fonts/Poppins-Bold.ttf && \
    wget -q "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf" -O /app/fonts/Poppins-SemiBold.ttf && \
    wget -q "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf" -O /app/fonts/Poppins-Regular.ttf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY islamic_automation_claude.py .

# Google credentials are written at runtime from the GOOGLE_CREDENTIALS_JSON env var
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# All secrets are injected at runtime via environment variables or --env-file
# Do NOT hardcode secrets here — pass them with: docker run --env-file .env ...
ENV YOUTUBE_API_KEY=""
ENV YOUTUBE_CHANNEL_ID=""
ENV CLAUDE_API_KEY=""
ENV INSTAGRAM_BUSINESS_ACCOUNT_ID=""
ENV INSTAGRAM_ACCESS_TOKEN=""
ENV GOOGLE_CREDENTIALS_JSON=""

ENTRYPOINT ["./entrypoint.sh"]
