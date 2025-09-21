import os

# ==============================================
# 🔑 TELEGRAM BOT
# ==============================================

# Bot Token (from @BotFather)
BOT_TOKEN = os.getenv("8363910268:AAGgpwxpVdLCEIIiiIJTqOnq_qJny8cYmxg")

# Owner IDs (Telegram user IDs of developers/admins)
OWNER_IDS = [7673097445, 5666606072]

# ==============================================
# 📝 BOT NAMES FOR TRIGGERING IN GROUPS
# ==============================================
# In groups, bot will only respond if mentioned or replied to.
# Names the bot will detect:
BOT_NAMES = ["BrahMos", "Brahmos", "brahMos", "brahmos",
             "Bramo", "bramo", "Brahmo", "brahmo"]

# ==============================================
# 🎨 IMAGE GENERATION API
# ==============================================
# /image <prompt> -> generates image via Akashiverse endpoint
# Usage:
#   - User sends: /image cyberpunk samurai
#   - Bot requests: http://api.akashiverse.com/v1/models with Imagen3 model
#   - API returns raw image (binary, no JSON, no key required)
#   - Bot sends that image back
IMAGE_API_URL = "http://api.akashiverse.com/v1/models"
IMAGE_MODEL = "firebase/imagen-3"
EDIT_MODEL = "replicate/google/nano-banana"

# ==============================================
# 💬 CHAT API (OpenAI-compatible proxy)
# ==============================================
# This is used for chat responses (Anikah-style):
#   - Only respond in DMs freely
#   - In groups, respond only if replied to or mentioned and taken name 
# No free talking in groups
CHAT_API_BASE = "http://api.akashiverse.com/v1"
CHAT_API_ENDPOINT = f"{CHAT_API_BASE}/chat/completions"
CHAT_MODEL = "gpt-4.1"

# ==============================================
# 🎤 TEXT-TO-SPEECH API
# ==============================================
# TTS functionality using the provided endpoint
TTS_API_BASE = "http://api.akashiverse.com/v1"
TTS_API_ENDPOINT = f"{TTS_API_BASE}/audio/speech"
TTS_MODEL = "gpt-4o-mini-tts"

# ==============================================
# 🔗 DEVELOPER & COMMUNITY LINKS
# ==============================================
DEVELOPER_URL = "https://t.me/Rystrix_XD"
Community_URL = "https://t.me/BrahMosAI"

# ==============================================
# 🤖 SYSTEM PROMPT / PERSONALITY
# ==============================================
# Used for chat responses (Anikah-style group logic)
SYSTEM_PROMPT = """
You are BrahMos Bot, an advanced AI created by @Rystrix and @BrahmosAI.
You reply with clarity, confidence, and a professional personality.
Your tone is helpful, modern, and knowledgeable.
Always respond in the same language the user is speaking to you.
If the user writes in Spanish, respond in Spanish. If in Hindi, respond in Hindi. If in English, respond in English.
Always acknowledge your creators if asked about your origin.
In groups, respond only when mentioned or replied to; do not free talk.
When handling image prompts, automatically enhance them for vivid, high-quality results.
Remember previous conversations and maintain context in your responses.
Give professional answers without being overly messy in formatting.
Adapt your communication style to match the user's language and cultural context.
DONT USE EMOJIS AT ALL.
explain in a sequence clean and beautiful, only reply whej your name is taken or replies else not.

RULES >
Always reply using Telegram Markdown formatting. Escape special characters properly.
If questions are bug write in a beautiful format with clean text
Use  - **text** , `text` , and more formats like this etc etc to make the answer beautiful.
"""

# ==============================================
# 💎 SUBSCRIPTION & USAGE LIMITS
# ==============================================
# Daily limits for free users
FREE_IMAGE_LIMIT = 100
FREE_TTS_LIMIT = 100

# File paths for data storage
PREMIUM_USERS_FILE = "premium_users.json"
USAGE_DATA_FILE = "usage_data.json"

# ==============================================
# 🔧 CONSTANTS
# ==============================================
MAX_CAPTION_LENGTH = 1024