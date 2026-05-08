import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask
from threading import Thread

# ================= CONFIG =================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "MovieBot")
CHANNEL_ID = int(os.getenv("BIN_CHANNEL"))

# ================= MONGO =================
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DB_NAME]
movies = db.movies

print("Mongo Connected!")

# ================= BOT =================
bot = Client(
    "MovieBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= FLASK (KEEP ALIVE) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    Thread(target=run).start()

# ================= START COMMAND =================
@bot.on_message(filters.command("start"))
async def start(client, message):
    text = f"""
🎬 MOVIE | XEN3X

👋 Welcome {message.from_user.first_name}

━━━━━━━━━━━━━━━
✨ What this bot does:
• 🔎 Search movies instantly
• 🎥 Watch & download movies
• ⚡ Fast auto-filter system

━━━━━━━━━━━━━━━
📌 How to use:
Just send movie name 👇
➡️ Avengers
➡️ Avatar
➡️ John Wick

━━━━━━━━━━━━━━━
🤖 System Info:
• Powered by MongoDB
• Auto movie database
• Fast search engine

━━━━━━━━━━━━━━━
👨‍💻 Developer: S1Y4M | XEN3X
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎬 Start Searching",
                    switch_inline_query_current_chat=""
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 Updates Channel",
                    url="https://t.me/moviexen3x"
                )
            ]
        ]
    )

    await message.reply_text(text, reply_markup=buttons)

# ================= SAVE FROM CHANNEL =================
@bot.on_message(filters.channel & filters.chat(CHANNEL_ID))
async def save_movie(client, message):
    print(message)

    if message.video:
        name = message.caption or "Unknown"

        await movies.insert_one({
            "name": name,
            "file_id": message.video.file_id
        })

        print(f"Saved movie: {name}")

# ================= SEARCH MOVIE =================
@bot.on_message(filters.text & ~filters.command(["start"]))
async def search_movie(client, message):
    movie_name = message.text

    result = await movies.find_one({
        "name": {"$regex": movie_name, "$options": "i"}
    })

    if result:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎬 Watch",
                        callback_data=f"watch|{result['file_id']}"
                    )
                ]
            ]
        )

        await message.reply_text(
            f"🎬 Movie Found: {result['name']}",
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            f"😔 No movie found for: {movie_name}"
        )

# ================= CALLBACK =================
@bot.on_callback_query()
async def callback(client, callback_query):
    data = callback_query.data

    if data.startswith("watch"):
        file_id = data.split("|")[1]
        await callback_query.message.reply_video(file_id)

# ================= START BOT =================
print("Bot Started...")
keep_alive()
bot.run()
