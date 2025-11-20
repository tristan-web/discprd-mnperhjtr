import discord
from discord.ext import commands
import requests
import json
import os
import asyncio

# === ENVIRONMENT VARIABLES ===
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
SAMBANOVA_API_KEY = os.environ["SAMBANOVA_API_KEY"]
SAMBANOVA_API_URL = "https://api.sambanova.ai/v1/chat/completions"

SERVER_NAME = "Tristan and Esmae`s Roblox Club"

# === Words that trigger a 5-minute ban ===
RUDE_WORDS = [
    "stupid", "idiot", "dumb", "shut up", "ugly", "trash", "loser",
    "bitch", "fuck", "asshole"
]

# === Chat history file ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")

# === Load chat history ===
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
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        resp = requests.post(SAMBANOVA_API_URL, headers=headers, json=payload)
        data = resp.json()

        if "choices" in data and len(data["choices"]) > 0:
            ai_message = data["choices"][0]["message"].get("content", "No answer found.")
        else:
            ai_message = "I couldn't understand the response from the AI."

        chat_history[channel_key].append({"role": "assistant", "content": ai_message})
        save_history()

        return ai_message

    except Exception as e:
        return f"Error communicating with SambaNova: {e}"

# === Discord bot ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    print(f"💾 Chat history stored at {HISTORY_FILE}")

# === Check rude words & ban ===
async def check_rude_language(message):
    text = message.content.lower()

    if any(rude in text for rude in RUDE_WORDS):
        try:
            await message.channel.send(
                f"🚨 {message.author.mention} has been banned for rude language (5 minutes)."
            )

            await message.guild.ban(
                message.author,
                reason="Rude language auto-ban"
            )

            await asyncio.sleep(300)

            await message.guild.unban(
                message.author,
                reason="Temporary ban expired"
            )

            return True

        except Exception as e:
            print("Ban error:", e)

    return False

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Only moderate inside your Roblox Club server
    if message.guild and message.guild.name == SERVER_NAME:
        rude = await check_rude_language(message)
        if rude:
            return

    # AI reply
    if message.content.strip():
        async with message.channel.typing():
            answer = get_ai_answer(message.channel.id, message.content.strip())
        await message.channel.send(answer)

# === Run bot ===
client.run(DISCORD_BOT_TOKEN)
