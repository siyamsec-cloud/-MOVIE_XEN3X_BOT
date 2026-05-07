from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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

@bot.on_message(filters.text)
async def search_movie(client, message):
    movie_name = message.text

    await message.reply_text(
        f"🎥 Searching for: {movie_name}\n\n❌ Database not connected yet."
    )

print("Bot Started...")
bot.run()
