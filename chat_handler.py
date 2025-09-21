import requests
import json
import re
import config
from utils import AnimatedLoader, log_user_interaction

# Global conversation memory
conversation_memory = {}

# ==============================================
# 🔹 AI RESPONSE HANDLER
# ==============================================
def get_ai_response(prompt, user_name, chat_id):
    """
    Sends prompt to AI API and returns response text
    """
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800,
        "temperature": 0.8,
    }

    response = requests.post(config.CHAT_API_ENDPOINT, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()

# ==============================================
# 🔹 /prompt COMMAND
# ==============================================
def handle_prompt_command(bot, message):
    """Handle /prompt command for enhancing prompts with animation"""

    log_user_interaction(message.from_user, "/prompt", "DM" if message.chat.type == "private" else "Group")

    prompt_text = message.text.strip()

    if len(prompt_text.split()) <= 1:
        bot.reply_to(message, """❓ **Prompt Enhancement Help**

**Usage:** `/prompt [your text]`

**Examples:**
• `/prompt a warrior` → Enhanced warrior description
• `/prompt sunset landscape` → Detailed scenic prompt
• `/prompt explain quantum physics` → Structured explanation

**💡 This command enhances ideas with rich details for chat or image generation!**""", parse_mode="Markdown")
        return

    original_prompt = prompt_text[7:].strip()

    enhanced_prompt = f"""You are a Prompt Generator specialized in turning short user ideas into rich, detailed prompts.
- Expand vague ideas into vivid, descriptive text
- Add sensory details (visuals, sounds, textures, atmosphere)
- Make it creative, structured, and AI-friendly
- Adapt style depending on the subject

**User idea:** {original_prompt}

Create an enhanced prompt with rich visual details:"""

    user_name = message.from_user.first_name or "User"

    loader = AnimatedLoader(bot, message.chat.id, "Enhancing prompt", "prompt")
    loader.start()

    try:
        enhanced = get_ai_response(enhanced_prompt, user_name, message.chat.id)
        loader.stop()

        response = f"✨ **Enhanced Prompt:**\n\n`{enhanced}`\n\n💡 *Copy the text above for better AI results!*"
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        loader.stop()
        bot.reply_to(message, f"❌ **Error enhancing prompt:** {str(e)[:100]}...", parse_mode="Markdown")

# ==============================================
# 🔹 /image COMMAND
# ==============================================
def handle_image_command(bot, message):
    """Handle /image command using Akashiverse API"""

    log_user_interaction(message.from_user, "/image", "DM" if message.chat.type == "private" else "Group")

    text = message.text.strip()
    if len(text.split()) <= 1:
        bot.reply_to(message, "❓ Usage: `/image cyberpunk samurai`", parse_mode="Markdown")
        return

    prompt = text[6:].strip()

    loader = AnimatedLoader(bot, message.chat.id, "Generating image", "image")
    loader.start()

    try:
        payload = {
            "model": config.IMAGE_MODEL,
            "prompt": prompt
        }

        response = requests.post(config.IMAGE_API_URL, json=payload, timeout=120)

        loader.stop()

        if response.status_code != 200:
            bot.reply_to(message, f"❌ Error: {response.status_code}", parse_mode="Markdown")
            return

        bot.send_photo(message.chat.id, response.content, caption=f"🖼 **Generated Image for:** `{prompt}`", parse_mode="Markdown")

    except Exception as e:
        loader.stop()
        bot.reply_to(message, f"❌ **Image generation failed:** {str(e)[:100]}...", parse_mode="Markdown")

# ==============================================
# 🔹 CHAT HANDLER
# ==============================================
def handle_chat_message(bot, message):
    """Handle general chat messages with AI"""

    chat_type = "DM" if message.chat.type == "private" else "Group"
    log_user_interaction(message.from_user, "message", chat_type)

    user_name = message.from_user.first_name or "User"
    text = message.text.strip()

    # In groups: only reply if mentioned or replied to
    if message.chat.type != "private":
        if not (message.reply_to_message or any(name in text for name in config.BOT_NAMES)):
            return

    loader = AnimatedLoader(bot, message.chat.id, "Thinking", "chat")
    loader.start()

    try:
        ai_response = get_ai_response(text, user_name, message.chat.id)
        loader.stop()

        bot.reply_to(message, ai_response, parse_mode="Markdown")
    except Exception as e:
        loader.stop()
        bot.reply_to(message, f"❌ **Error:** {str(e)[:100]}...", parse_mode="Markdown")
