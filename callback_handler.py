from telebot import types
import config
from utils import safe_edit_message, is_premium_user

def handle_help_callback(bot, call, usage_tracker):
    """Handle help callback with safe text"""
    user_id = call.from_user.id
    is_premium = is_premium_user(user_id)
    help_text = f"""🚀 **BrahMos AI - Features**

**💬 Chat:** `/chat` - Smart AI conversations
**🎨 Create:** `/image` - Generate stunning images  
**✏️ Edit:** `/edit` - Edit photos with AI
**🎤 Speech:** `/say` - Text-to-speech conversion
**⚡ Enhance:** `/prompt` - Improve your prompts
**📡 Status:** `/ping` - Check bot health

📊 **Status:** {"💎 Premium User" if is_premium else "🆓 Free User"}

🚀 **Powered by GPT-4 & Advanced AI Models**"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("💬 Chat", callback_data="quick_chat"),
        types.InlineKeyboardButton("🎨 Create", callback_data="quick_image")
    )
    keyboard.row(
        types.InlineKeyboardButton("✏️ Edit", callback_data="quick_edit"),
        types.InlineKeyboardButton("🎤 Speech", callback_data="quick_tts")
    )
    if not is_premium:
        keyboard.row(
            types.InlineKeyboardButton("💎 Upgrade Premium", callback_data="upgrade_premium")
        )
    keyboard.row(
        types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_start")
    )

    safe_edit_message(bot, call.message.chat.id, call.message.message_id, help_text, keyboard, parse_mode="Markdown")

def handle_my_info_callback(bot, call, usage_tracker):
    """Handle my info callback with safe text"""
    user_id = call.from_user.id
    user = call.from_user
    is_premium = is_premium_user(user_id)
    remaining_images = usage_tracker.get_remaining_images(user_id)
    remaining_tts = usage_tracker.get_remaining_tts(user_id)

    info_text = f"""ℹ️ **Your Account Information**

**👤 Profile:**
• Name: {user.first_name or 'Unknown'}
• Username: @{user.username or 'None'}
• User ID: `{user_id}`

**💎 Subscription:** {"Premium" if is_premium else "Free"}

**📊 Daily Usage:**
• Images: {"∞" if is_premium else f"{remaining_images}/100"} remaining
• TTS: {"∞" if is_premium else f"{remaining_tts}/100"} remaining

**⚡ Status:** {"Unlimited Access" if is_premium else "Limited Access"}

💡 **Need more?** {'You have unlimited access!' if is_premium else 'Consider upgrading to Premium!'}"""

    keyboard = types.InlineKeyboardMarkup()
    if not is_premium:
        keyboard.row(types.InlineKeyboardButton("💎 Upgrade to Premium", callback_data="upgrade_premium"))
    keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_start"))

    safe_edit_message(bot, call.message.chat.id, call.message.message_id, info_text, keyboard, parse_mode="Markdown")

def handle_back_to_start_callback(bot, call):
    """Handle back to start callback with safe text"""
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "User"
    is_premium = is_premium_user(user_id)

    welcome_text = f"""🚀 **Welcome to BrahMos AI!**

Hey {first_name}! I'm your advanced AI assistant powered by cutting-edge technology.

🤖 **What I can do:**
• 💬 Smart Conversations - Chat with advanced AI
• 🎨 Image Generation - Create stunning artwork
• 🎤 Text-to-Speech - Convert text to natural speech
• ⚡ Group Chat Support - Mention me anywhere!

📊 **Your Status:** {"💎 Premium User - Unlimited Access!" if is_premium else "🆓 Free User - 100 daily generations"}

🚀 Ready to explore cutting-edge AI technology together!

Powered by the latest in AI innovation."""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("❓ Help & Features", callback_data="help"),
        types.InlineKeyboardButton("ℹ️ My Info", callback_data="my_info")
    )
    keyboard.row(
        types.InlineKeyboardButton("👨‍💻 Developer", url=config.DEVELOPER_URL),
        types.InlineKeyboardButton("🌐 Community", url=config.Community_URL)
    )
    if not is_premium:
        keyboard.row(
            types.InlineKeyboardButton("💎 Upgrade to Premium", callback_data="upgrade_premium")
        )

    safe_edit_message(bot, call.message.chat.id, call.message.message_id, welcome_text, keyboard, parse_mode="Markdown")

def handle_upgrade_premium_callback(bot, call):
    """Handle upgrade premium callback with safe text"""
    upgrade_text = """💎 **Upgrade to Premium**

🌟 **Premium Benefits:**
• ∞ Unlimited image generations
• ∞ Unlimited TTS conversions
• 🚀 Priority processing
• 🎯 Higher quality outputs
• 📞 Direct support

💰 **Contact Developer:**
Ready to upgrade? Contact @Rystrix for premium access!

Premium users get the full BrahMos AI experience without any limits."""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("📞 Contact Developer", url="https://t.me/Rystrix_XD"))
    keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_start"))

    safe_edit_message(bot, call.message.chat.id, call.message.message_id, upgrade_text, keyboard, parse_mode="Markdown")

def handle_quick_chat_callback(bot, call, chat_mode, user_waiting_for_chat):
    """Handle quick chat callback"""
    user_id = call.from_user.id

    if call.message.chat.type != 'private':
        bot.answer_callback_query(call.id, "Chat mode is only available in direct messages!", show_alert=True)
        return

    chat_mode.add(user_id)
    user_waiting_for_chat.add(user_id)

    bot.answer_callback_query(call.id, "Chat mode activated! Send me a message.")
    bot.send_message(call.message.chat.id, """💬 **Chat Mode Activated!**

I'm now ready for a conversation! Just type your message and I'll respond with intelligent answers.

✨ **Features:**
• Contextual conversations
• Memory of our chat
• Smart responses
• No command needed

**What would you like to talk about?**""", parse_mode="Markdown")

def handle_quick_image_callback(bot, call, user_waiting_for_image):
    """Handle quick image callback"""
    user_id = call.from_user.id
    user_waiting_for_image.add(user_id)
    bot.answer_callback_query(call.id, "Image mode activated! Send me your prompt.")
    bot.send_message(call.message.chat.id, """🎨 **Image Generation Mode Activated!**

Send me a description of what you want to create and I'll generate an image for you.

**Examples:**
• "cyberpunk samurai warrior"
• "sunset over mountains"
• "cute cat in space suit"

💡 **Tip:** Be descriptive for better results!""", parse_mode="Markdown")

def handle_quick_tts_callback(bot, call, user_waiting_for_tts):
    """Handle quick TTS callback"""
    user_id = call.from_user.id
    user_waiting_for_tts.add(user_id)
    bot.answer_callback_query(call.id, "TTS mode activated! Send me text to convert.")
    bot.send_message(call.message.chat.id, """🎤 **Text-to-Speech Mode Activated!**

Send me any text and I'll convert it to speech for you.

**Examples:**
• "Hello, how are you today?"
• "Welcome to BrahMos AI!"
• "This is a test of speech synthesis"

💡 **Tip:** Keep text under 500 characters for best results!""", parse_mode="Markdown")

def handle_quick_edit_callback(bot, call, user_waiting_for_edit):
    """Handle quick edit callback"""
    user_id = call.from_user.id
    bot.answer_callback_query(call.id, "Edit mode ready! Use /edit [description] first.")
    bot.send_message(call.message.chat.id, """✏️ **Photo Editing Mode!**

**Step 1:** Use `/edit [description]` command
**Step 2:** Upload the photo you want to edit

**Examples:**
• `/edit make it darker and more dramatic`
• `/edit add sunglasses and a hat`  
• `/edit change background to beach`

💡 **Tip:** Be specific about what changes you want!""", parse_mode="Markdown")