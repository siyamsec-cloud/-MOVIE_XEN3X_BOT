import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
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

PHOTO_URL = "https://i.postimg.cc/XJycncFq/Picsart-26-05-01-12-48-36-061.png"

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

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    Thread(target=run).start()

# ================= START MENU =================
@bot.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🍿 MOVIE HUB | XEN3X

👋 Hi {message.from_user.first_name}

━━━━━━━━━━━━━━━
🎬 Welcome to Netflix-style Movie Bot

✨ Choose your category below:
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                InlineKeyboardButton("🔥 Trending", callback_data="trending")
            ],
            [
                InlineKeyboardButton("⭐ Web Series", callback_data="series"),
                InlineKeyboardButton("🎭 Genres", callback_data="genres")
            ],
            [
                InlineKeyboardButton("👨‍💻 Developer", callback_data="developer")
            ]
        ]
    )

    await message.reply_photo(
        photo=PHOTO_URL,
        caption=text,
        reply_markup=buttons
    )

# ================= SAVE MOVIES =================
@bot.on_message(filters.channel & filters.chat(CHANNEL_ID))
async def save_movie(client, message):

    if message.video:
        name = message.caption or "Unknown"

        await movies.insert_one({
            "name": name,
            "file_id": message.video.file_id
        })

        print(f"Saved movie: {name}")

# ================= SEARCH =================
@bot.on_message(filters.private & filters.text)
async def search_movie(client, message):

    if message.text.startswith("/"):
        return

    result = await movies.find_one({
        "name": {"$regex": message.text, "$options": "i"}
    })

    if result:
        await message.reply_video(
            result["file_id"],
            caption=f"🎬 {result['name']}"
        )
    else:
        await message.reply_text("😔 No movie found")

# ================= CALLBACK SYSTEM =================
@bot.on_callback_query()
async def callback(client, callback_query):

    data = callback_query.data

    # ===== HOME BACK =====
    if data == "back":

        text = f"""
🍿 MOVIE HUB | XEN3X

👋 Welcome back {callback_query.from_user.first_name}

━━━━━━━━━━━━━━━
🎬 Choose category
"""

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                    InlineKeyboardButton("🔥 Trending", callback_data="trending")
                ],
                [
                    InlineKeyboardButton("⭐ Web Series", callback_data="series"),
                    InlineKeyboardButton("🎭 Genres", callback_data="genres")
                ],
                [
                    InlineKeyboardButton("👨‍💻 Developer", callback_data="developer")
                ]
            ]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ===== DEVELOPER =====
    elif data == "developer":

        text = """
👨‍💻 Developer Info

━━━━━━━━━━━━━━━
🧑 Name: MUHAMMAD SIYAM
🎬 Bot: MOVIE | XEN3X
⚡ Powered By Pyrogram
━━━━━━━━━━━━━━━
"""

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ===== MOVIES MENU =====
    elif data == "movies":

        text = """
🎬 MOVIES LIBRARY

━━━━━━━━━━━━━━━
Choose category 🍿
"""

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔥 Latest", callback_data="latest"),
                    InlineKeyboardButton("⭐ Top Rated", callback_data="top")
                ],
                [
                    InlineKeyboardButton("🇮🇳 Bollywood", callback_data="bollywood"),
                    InlineKeyboardButton("🌍 Hollywood", callback_data="hollywood")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="back")
                ]
            ]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ===== TRENDING =====
    elif data == "trending":

        text = """
🔥 TRENDING NOW

━━━━━━━━━━━━━━━
Most watched movies 🍿
"""

        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🎬 View List", callback_data="latest")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ===== GENRES =====
    elif data == "genres":

        text = """
🎭 MOVIE GENRES

━━━━━━━━━━━━━━━
Pick your mood 🍿
"""

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("💥 Action", callback_data="action"),
                    InlineKeyboardButton("😂 Comedy", callback_data="comedy")
                ],
                [
                    InlineKeyboardButton("💔 Romance", callback_data="romance"),
                    InlineKeyboardButton("😱 Thriller", callback_data="thriller")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="back")
                ]
            ]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ===== PLACEHOLDER CATEGORIES =====
    elif data in ["latest", "top", "bollywood", "hollywood", "action", "comedy", "romance", "thriller", "series"]:

        text = f"""
🍿 {data.upper()} MOVIES

━━━━━━━━━━━━━━━
Coming soon auto filter system...
"""

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

# ================= START BOT =================
print("Bot Started...")
keep_alive()
bot.run()
