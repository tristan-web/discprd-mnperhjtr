import discord
from discord.ext import commands
import requests
import json
import os
import asyncio

# === Configuration ===
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
SAMBANOVA_API_KEY = os.environ["SAMBANOVA_API_KEY"]
SAMBANOVA_API_URL = "https://api.sambanova.ai/v1/chat/completions"

SERVER_NAME = "Tristan and Esmae`s Roblox Club"

# === Words that cause a 5-minute ban ===
RUDE_WORDS = [
    "stupid", "idiot", "dumb", "shut up", "ugly", "trash", "loser",
    "bitch", "fuck", "asshole"
]

# === Chat history file ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=2)

chat_history = load_history()

# === SambaNova API call ===
def get_ai_answer(channel_id, user_message):
    channel_key = str(channel_id)
    if channel_key not in chat_history:
        chat_history[channel_key] = []

    chat_history[channel_key].append({"role": "user", "content": user_message})
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

        if "choices" in data and len(data["choices"]) > 0:
            ai_message = data["choices"][0]["message"].get("content", "No answer found.")
        else:
            ai_message = "I couldn't generate a valid answer."

        chat_history[channel_key].append({"role": "assistant", "content": ai_message})
        save_history()

        return ai_message

    except Exception as e:
        return f"Error communicating with SambaNova: {e}"

# === Discord bot setup ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for banning/unbanning

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    print("Bot is running with admin abilities (if role has Admin enabled).")

@client.event
async def on_message(message):
    # Ignore the bot itself
    if message.author == client.user:
        return

    # Only moderate inside your specific server
    if message.guild and message.guild.name == SERVER_NAME:

        # Check for rude words
        msg_lower = message.content.lower()
        if any(word in msg_lower for word in RUDE_WORDS):
            try:
                await message.channel.send(
                    f"⚠️ {message.author.mention}, that was rude. "
                    "You are banned for **5 minutes**."
                )

                # Ban user
                await message.guild.ban(
                    message.author,
                    reason="Automatic rude-message ban"
                )

                # Wait 5 minutes
                await asyncio.sleep(300)

                # Unban user
                await message.guild.unban(
                    message.author,
                    reason="Auto-unban after timeout"
                )

                return

            except Exception as e:
                await message.channel.send(f"❌ Error banning user: {e}")
                return

    # === Normal AI function ===
    user_message = message.content.strip()
    if user_message:
        async with message.channel.typing():
            answer = get_ai_answer(message.channel.id, user_message)
        await message.channel.send(answer)

# === Run bot ===
client.run(DISCORD_BOT_TOKEN)
