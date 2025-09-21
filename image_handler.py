import io
import re
import json
import requests
import config
from utils import AnimatedLoader

# ---------- MarkdownV2 escaping ----------
# Per Telegram MarkdownV2 rules, escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
MDV2_CHARS = r'_\*\[\]\(\)~`>#+\-=|{}\.!'

def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    # First escape backslashes, then the rest
    text = text.replace("\\", "\\\\")
    return re.sub(f"([{MDV2_CHARS}])", r"\\\1", text)

def truncate(text: str, limit: int = 1024) -> str:
    if text is None:
        return ""
    return text if len(text) <= limit else text[: limit - 3] + "..."

# ---------- API call ----------
def generate_image(full_prompt: str, bot=None, chat_id=None):
    """
    Always send the FULL prompt to the API using Imagen3 model.
    Returns image bytes or None.
    """
    loader = None
    try:
        if bot and chat_id:
            loader = AnimatedLoader(bot, chat_id, "Creating your masterpiece", "image")
            loader.start()

        # New API format for Imagen3 model
        payload = {
            "model": config.IMAGE_MODEL,
            "prompt": full_prompt,
            "response_format": "url",
            "size": "1024x1024"
        }

        headers = {"Content-Type": "application/json"}

        # Use POST with JSON payload for new API
        resp = requests.post(
            config.IMAGE_API_URL,
            json=payload,
            headers=headers,
            timeout=120,
        )
        
        print(f"[DEBUG] Image API response status: {resp.status_code}")
        
        if resp.status_code == 200:
            # Try to parse JSON response first
            try:
                response_data = resp.json()
                if "data" in response_data and len(response_data["data"]) > 0:
                    image_url = response_data["data"][0].get("url")
                    if image_url:
                        # Download the image from the URL
                        img_resp = requests.get(image_url, timeout=60)
                        if img_resp.status_code == 200:
                            return img_resp.content
                        else:
                            print(f"[DEBUG] Failed to download image from URL: {img_resp.status_code}")
            except json.JSONDecodeError:
                pass
            
            # Fallback: check if response contains image data directly
            if _looks_like_image(resp):
                return resp.content

        return None
    except requests.exceptions.Timeout:
        print("[DEBUG] Image generation timeout")
        return None
    except requests.exceptions.ConnectionError:
        print("[DEBUG] Image generation connection error")
        return None
    except Exception as e:
        print(f"[DEBUG] Image generation error: {e}")
        return None
    finally:
        if loader:
            loader.stop()

def _looks_like_image(resp: requests.Response) -> bool:
    if not resp or resp.status_code != 200:
        return False
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if ctype.startswith("image/"):
        return True
    # Accept large binary that is not JSON
    return len(resp.content or b"") > 1000 and not ctype.startswith("application/json")

# ---------- Telegram send helpers ----------
def safe_send_photo(bot, chat_id, image_bytes: bytes, caption: str, reply_to=None):
    try:
        bot.send_photo(
            chat_id,
            io.BytesIO(image_bytes),
            caption=caption,
            parse_mode="MarkdownV2",
            reply_to_message_id=reply_to,
        )
    except Exception as e:
        print(f"[DEBUG] Failed to send photo: {e}")
        # Fallback: send without parse_mode
        try:
            bot.send_photo(
                chat_id,
                io.BytesIO(image_bytes),
                caption=caption.replace("\\", ""),  # loosen escaping on fallback
                reply_to_message_id=reply_to,
            )
        except Exception as e2:
            print(f"[DEBUG] Fallback photo send failed: {e2}")
            bot.send_message(chat_id, f"❌ Failed to send image\nError: {e2}")

# ---------- Handlers ----------
def handle_image_command(bot, message, user_waiting_for_image, usage_tracker):
    from utils import log_user_interaction, is_premium_user

    user_id = message.from_user.id
    log_user_interaction(message.from_user, "/image", "DM" if message.chat.type == "private" else "Group")

    text = (message.text or "").strip()
    if len(text.split()) <= 1:
        bot.reply_to(
            message,
            "🎨 Image Generation Help\n\nUsage: `/image [description]`\n\nExamples:\n• `/image cyberpunk samurai warrior`\n• `/image sunset over mountains`\n• `/image cute cat in space suit`\n\nTip: Be descriptive for better results!",
            parse_mode="Markdown",
        )
        return

    full_prompt = text[6:].strip()  # FULL prompt goes to API

    # Usage gates
    if not is_premium_user(user_id):
        if not usage_tracker.can_use_image(user_id):
            bot.reply_to(
                message,
                "🚫 Daily Image Limit Reached\n\nUpgrade to Premium for unlimited generations.\nContact @Rystrix to upgrade!",
                parse_mode="Markdown",
            )
            return
        remaining = usage_tracker.get_remaining_images(user_id)
        if remaining <= 10:
            bot.reply_to(message, f"⚠️ Only {remaining} image generations left today!", parse_mode="Markdown")

    img = generate_image(full_prompt, bot, message.chat.id)
    if not img:
        bot.reply_to(message, "❌ Image Generation Failed\nPlease try a different prompt.", parse_mode="Markdown")
        return

    shown = truncate(full_prompt, 900)  # leave headroom for the rest of caption after escaping
    safe_shown = escape_markdown_v2(shown)

    if not is_premium_user(user_id):
        usage_tracker.use_image(user_id)
        remaining = usage_tracker.get_remaining_images(user_id)
        tail = f"\n\n📊 Remaining today: {remaining}/100"
    else:
        tail = "\n\n💎 Premium User - Unlimited Access!"

    cap = f"🎨 *Generated Image*\n\n📝 *Prompt:* `{safe_shown}`\n\n✨ *Created by BrahMos AI*{escape_markdown_v2(tail)}"
    safe_send_photo(bot, message.chat.id, img, cap, reply_to=message.message_id)

def edit_image(image_data: bytes, edit_prompt: str, bot=None, chat_id=None):
    """
    Edit an image using nano banana model.
    Returns edited image bytes or None.
    """
    loader = None
    try:
        if bot and chat_id:
            loader = AnimatedLoader(bot, chat_id, "Editing your image", "image")
            loader.start()

        # Convert image to base64 for API
        import base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Edit API format for nano banana model
        payload = {
            "model": config.EDIT_MODEL,
            "prompt": edit_prompt,
            "image": f"data:image/jpeg;base64,{image_b64}",
            "response_format": "url",
            "size": "1024x1024"
        }

        headers = {"Content-Type": "application/json"}

        # Use POST with JSON payload for edit API
        resp = requests.post(
            config.IMAGE_API_URL,
            json=payload,
            headers=headers,
            timeout=120,
        )
        
        print(f"[DEBUG] Edit API response status: {resp.status_code}")
        
        if resp.status_code == 200:
            # Try to parse JSON response first
            try:
                response_data = resp.json()
                if "data" in response_data and len(response_data["data"]) > 0:
                    image_url = response_data["data"][0].get("url")
                    if image_url:
                        # Download the edited image from the URL
                        img_resp = requests.get(image_url, timeout=60)
                        if img_resp.status_code == 200:
                            return img_resp.content
                        else:
                            print(f"[DEBUG] Failed to download edited image from URL: {img_resp.status_code}")
            except json.JSONDecodeError:
                pass
            
            # Fallback: check if response contains image data directly
            if _looks_like_image(resp):
                return resp.content

        return None
    except Exception as e:
        print(f"[DEBUG] Image editing error: {e}")
        return None
    finally:
        if loader:
            loader.stop()

def handle_edit_command(bot, message, user_waiting_for_edit, usage_tracker):
    from utils import log_user_interaction, is_premium_user

    user_id = message.from_user.id
    log_user_interaction(message.from_user, "/edit", "DM" if message.chat.type == "private" else "Group")

    text = (message.text or "").strip()
    if len(text.split()) <= 1:
        bot.reply_to(
            message,
            "🎨 **Image Editing Help**\n\n**Usage:** `/edit [description]`\n\n**Examples:**\n• `/edit make it darker and more dramatic`\n• `/edit add sunglasses and a hat`\n• `/edit change background to beach`\n\n**💡 Tip:** First send the command, then upload your photo!",
            parse_mode="Markdown",
        )
        return

    edit_prompt = text[5:].strip()  # Remove "/edit "
    
    # Store edit prompt and put user in waiting mode
    user_waiting_for_edit[user_id] = edit_prompt
    
    bot.reply_to(message, f"📷 **Ready to edit!**\n\n**Edit instruction:** `{edit_prompt}`\n\n**Now send me the photo** you want to edit.", parse_mode="Markdown")

def handle_edit_photo(bot, message, user_waiting_for_edit, usage_tracker):
    from utils import is_premium_user
    import io

    user_id = message.from_user.id
    if user_id not in user_waiting_for_edit:
        return

    edit_prompt = user_waiting_for_edit.pop(user_id)

    # Check usage limits for free users
    if not is_premium_user(user_id):
        if not usage_tracker.can_use_image(user_id):
            bot.reply_to(
                message,
                "🚫 **Daily Image Limit Reached**\n\nUpgrade to Premium for unlimited edits.\nContact @Rystrix to upgrade!",
                parse_mode="Markdown",
            )
            return

    try:
        # Get the largest photo size
        if message.photo:
            photo = message.photo[-1]  # Get highest resolution
            file_info = bot.get_file(photo.file_id)
            photo_data = bot.download_file(file_info.file_path)
            
            # Edit the image
            edited_img = edit_image(photo_data, edit_prompt, bot, message.chat.id)
            
            if edited_img:
                # Track usage for free users
                if not is_premium_user(user_id):
                    usage_tracker.use_image(user_id)
                    remaining = usage_tracker.get_remaining_images(user_id)
                    tail = f"\n\n📊 **Remaining today:** {remaining}/100"
                else:
                    tail = "\n\n💎 **Premium User - Unlimited Access!**"

                safe_edit_prompt = escape_markdown_v2(truncate(edit_prompt, 900))
                cap = f"🎨 *Edited Image*\n\n📝 *Edit:* `{safe_edit_prompt}`\n\n✨ *Edited by BrahMos AI*{escape_markdown_v2(tail)}"
                
                safe_send_photo(bot, message.chat.id, edited_img, cap, reply_to=message.message_id)
            else:
                bot.reply_to(message, "❌ **Image Editing Failed**\n\nPlease try a different edit instruction.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ **No Photo Found**\n\nPlease send a photo to edit.", parse_mode="Markdown")
            
    except Exception as e:
        print(f"[DEBUG] Edit photo error: {e}")
        bot.reply_to(message, "💥 **Error:** Something went wrong while editing your photo. Please try again!")

def handle_image_input(bot, message, user_waiting_for_image, usage_tracker):
    from utils import is_premium_user

    uid = message.from_user.id
    if uid not in user_waiting_for_image:
        return
    user_waiting_for_image.discard(uid)

    full_prompt = (message.text or "").strip()
    img = generate_image(full_prompt, bot, message.chat.id)
    if not img:
        bot.send_message(message.chat.id, "❌ Image Generation Failed\nPlease try a different prompt.", parse_mode="Markdown")
        return

    shown = truncate(full_prompt, 900)
    safe_shown = escape_markdown_v2(shown)

    if not is_premium_user(uid):
        usage_tracker.use_image(uid)
        remaining = usage_tracker.get_remaining_images(uid)
        tail = f"\n\n📊 Remaining today: {remaining}/100"
    else:
        tail = "\n\n💎 Premium User - Unlimited Access!"

    cap = f"🎨 *Generated Image*\n\n📝 *Prompt:* `{safe_shown}`\n\n✨ *Created by BrahMos AI*{escape_markdown_v2(tail)}"
    safe_send_photo(bot, message.chat.id, img, cap, reply_to=message.message_id)