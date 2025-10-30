import discord
import requests
import json
import os

# === Configuration (from Environment Variables) ===
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
SAMBANOVA_API_KEY = os.environ["SAMBANOVA_API_KEY"]
SAMBANOVA_API_URL = "https://api.sambanova.ai/v1/chat/completions"

# === Ensure chat_history.json is in the same folder as this script ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")

# === Load chat history from file ===
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# === Save chat history to file ===
def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=2)

# === Memory: chat history per channel ===
chat_history = load_history()

# === Helper: call SambaNova API ===
def get_ai_answer(channel_id, user_message):
    channel_key = str(channel_id)
    if channel_key not in chat_history:
        chat_history[channel_key] = []

    # Add user message to memory
    chat_history[channel_key].append({"role": "user", "content": user_message})

    # Use last 10 messages for context
    messages = chat_history[channel_key][-10:]

    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "Meta-Llama-3.3-70B-Instruct",
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(SAMBANOVA_API_URL, headers=headers, json=payload)
        data = resp.json()
        print("🔍 SambaNova raw response:", json.dumps(data, indent=2))

        if "choices" in data and len(data["choices"]) > 0:
            ai_message = data["choices"][0]["message"].get("content", "No answer found.")
        elif "output" in data:
            ai_message = data["output"]
        else:
            ai_message = "I couldn't generate a valid answer."

        # Save bot response to memory
        chat_history[channel_key].append({"role": "assistant", "content": ai_message})
        save_history()  # persist memory

        return ai_message

    except Exception as e:
        return f"Error communicating with SambaNova: {e}"

# === Discord bot setup ===
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    print(f"💾 Chat history file located at: {HISTORY_FILE}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_message = message.content.strip()
    if user_message:
        await message.channel.typing()
        answer = get_ai_answer(message.channel.id, user_message)
        await message.channel.send(answer)

# === Run bot ===
client.run(DISCORD_BOT_TOKEN)
