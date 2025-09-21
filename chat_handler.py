import requests
import json
import re
import config
from utils import AnimatedLoader

# Global conversation memory
conversation_memory = {}

def _append_delta_text_from_chunk(obj, buf):
    """
    Safely extract streamed text from an OpenAI-compatible SSE JSON object.
    Handles shapes:
      - {"choices":[{"delta":{"content":"..."} }]}
      - {"choices":[{"delta":{"role":"assistant"}}]}  # no content
      - {"choices":[{"message":{"content":"..."} }]}  # non-stream JSON fallback
    Also tolerates when 'choices' is a list but not dict-like.
    """
    try:
        choices = obj.get("choices", [])
    except AttributeError:
        choices = obj if isinstance(obj, list) else []
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        delta = choice.get("delta") or {}
        if isinstance(delta, dict):
            piece = delta.get("content")
            if isinstance(piece, str):
                buf.append(piece)
        message = choice.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                buf.append(content)

def parse_streaming_response(response):
    """Robust SSE parser tolerant to proxies and concatenated or array chunks."""
    out_parts = []
    try:
        for raw in response.iter_lines(decode_unicode=True):
            if not raw or raw.startswith(":"):
                continue
            if raw.startswith("data:"):
                data = raw[5:].lstrip()
            else:
                continue
            if not data or data == "[DONE]":
                continue

            pieces = re.split(r'(?<=\})(?=\{)', data) if "}{" in data else [data]
            for p in pieces:
                p = p.strip()
                if not p:
                    continue
                try:
                    obj = json.loads(p)
                except json.JSONDecodeError:
                    if p.startswith("[") and p.endswith("]"):
                        try:
                            arr = json.loads(p)
                            _append_delta_text_from_chunk({"choices": arr}, out_parts)
                            continue
                        except Exception:
                            out_parts.append(p)
                            continue
                    out_parts.append(p)
                    continue
                _append_delta_text_from_chunk(obj, out_parts)
        return "".join(out_parts).strip()
    except Exception as e:
        print(f"[DEBUG] Streaming parse error: {e}")
        return None

def get_ai_response(user_message, user_name="User", chat_id=None, message_context=None):
    """Get AI response with streaming support and conversation memory"""
    result = ""
    current_message = f"{user_name}: {user_message}"

    try:
        messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        if chat_id in conversation_memory:
            messages.extend(conversation_memory[chat_id][-6:])
        if message_context:
            current_message = f"[Context: {message_context}] {current_message}"
        messages.append({"role": "user", "content": current_message})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.API_KEY}"
        }
        payload = {
            "model": config.CHAT_MODEL,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.8,
            "stream": True
        }

        print(f"[DEBUG] Sending request to: {config.CHAT_API_ENDPOINT}")
        response = requests.post(
            config.CHAT_API_ENDPOINT,
            json=payload,
            headers=headers,
            stream=True,
            timeout=60
        )

        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower().strip()

        if "text/event-stream" in content_type or content_type == "" or "event-stream" in content_type:
            ai_response = parse_streaming_response(response)
            result = ai_response if ai_response else "🔄 **Streaming Error:** Unable to parse response."
        elif "application/json" in content_type:
            data = response.json()
            try:
                if "choices" in data and data["choices"] and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    msg = choice.get("message", {})
                    result = (msg.get("content") or "").strip() or "🔍 **Response Error:** Empty content."
                else:
                    result = "🔍 **Response Error:** Invalid response structure."
            except Exception as e:
                result = f"🔍 **Response Error:** {e}"
        else:
            ai_response = parse_streaming_response(response)
            result = ai_response if ai_response else f"🚨 **API Error:** Unexpected content type: {content_type}"

    except requests.exceptions.HTTPError as http_err:
        result = f"🐞 **HTTP Error:** {http_err}"
    except requests.exceptions.ConnectionError:
        result = "🔌 **Connection Error:** Unable to reach API endpoint."
    except requests.exceptions.Timeout:
        result = "⏳ **Timeout Error:** API response took too long."
    except Exception as ex:
        result = f"💥 **Error:** {str(ex)[:100]}..."

    if chat_id and result:
        if chat_id not in conversation_memory:
            conversation_memory[chat_id] = []
        conversation_memory[chat_id].append({"role": "user", "content": current_message})
        conversation_memory[chat_id].append({"role": "assistant", "content": result})
        if len(conversation_memory[chat_id]) > 10:
            conversation_memory[chat_id] = conversation_memory[chat_id][-10:]
    return result

def handle_chat_message(bot, message, chat_mode_users, user_waiting_for_chat):
    """Handle chat messages in chat mode with memory"""
    from utils import log_user_interaction, get_user_mention

    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"

    log_user_interaction(message.from_user, "chat", "DM" if message.chat.type == "private" else "Group")

    if user_id in user_waiting_for_chat:
        user_waiting_for_chat.remove(user_id)

    context = None
    if message.reply_to_message:
        context = "Replying to previous message"
    elif message.chat.type in ['group', 'supergroup']:
        context = "Group conversation"

    ai_response = get_ai_response(message.text, user_name, message.chat.id, context)

    try:
        bot.send_message(message.chat.id, ai_response, parse_mode="Markdown")
    except Exception as e:
        print(f"[DEBUG] Failed to send chat response with Markdown: {e}")
        try:
            bot.send_message(message.chat.id, ai_response)
        except Exception as e2:
            print(f"[DEBUG] Failed to send chat response entirely: {e2}")
            bot.send_message(message.chat.id, "❌ **Sorry, I had trouble processing your message. Please try again.**")

def handle_prompt_command(bot, message):
    """Handle /prompt command for enhancing prompts with animation"""
    from utils import log_user_interaction, AnimatedLoader

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

    enhanced_prompt = f"""You are a Prompt Generator for Image Generation and TTS paragraph under 500 characters.

Rewrite the user's TTS idea in 500 characters and if specified number of characters do that only generate words for TTS not for image if asked.

If user tells you that make a prompt for this and mentioned characters design it like it will be specified for TTS saying only.

Rewrite the user's idea into a vivid, cinematic description.

**Focus on:**
- Maximum realism and intricate details
- Photorealistic textures  
- Lighting and shadows
- Mood and atmosphere
- Depth of field and focus
- Ambient, background details
- For TTS focus on good pronunciation and under 500 characters, if number of characters specified do that

Do not add style labels like cartoon/anime unless explicitly requested by the idea.
Always aim for masterpiece quality and 2K resolution.
If cartoonish or any anime is not mentioned please don't give it.
Always look for default quality and look realistic.

Now rewrite this prompt and ONLY output the final enhanced result:

**User idea:** {original_prompt}

Create an enhanced prompt with rich visual details:"""

    user_name = message.from_user.first_name or "User"

    loader = AnimatedLoader(bot, message.chat.id, "Enhancing prompt", "prompt")
    loader.start()

    try:
        enhanced = get_ai_response(enhanced_prompt, user_name, message.chat.id)
        loader.stop()

        response = f"✨ **Enhanced Prompt:**\n\n`{enhanced}`\n\n💡 *Copy the text above for better AI results!*"
        try:
            bot.reply_to(message, response, parse_mode="Markdown")
        except Exception as e:
            print(f"[DEBUG] Failed to send enhanced prompt with Markdown: {e}")
            bot.reply_to(message, f"✨ Enhanced Prompt:\n\n{enhanced}\n\n💡 Copy the text above for better AI results!")
    except Exception as e:
        loader.stop()
        bot.reply_to(message, f"❌ **Error enhancing prompt:** {str(e)[:100]}...", parse_mode="Markdown")
