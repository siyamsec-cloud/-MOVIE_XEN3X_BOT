import asyncio

asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client(
    "MovieBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.on_message(filters.command("start"))
async def start(client, message):
    text = """
🎬 Welcome to Movie Bot

Send any movie name to search.

Examples:
➡️ Avatar
➡️ John Wick
➡️ Avengers
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔥 Updates Channel",
                    url="https://t.me/MOVIE_XEN3X_BOT"
                )
            ]
        ]
    )

    await message.reply_text(
        text,
        reply_markup=buttons
    )

@bot.on_message(filters.text & ~filters.bot & ~filters.command(["start"]))
async def search_movie(client, message):
    movie_name = message.text

    await message.reply_text(
        f"🎥 Searching for: {movie_name}\n\n❌ Database not connected yet."
    )

print("Bot Started...")

keep_alive()

bot.run()
