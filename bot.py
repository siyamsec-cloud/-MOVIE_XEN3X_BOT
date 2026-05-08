import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
from bson import ObjectId
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

# ================= START (HOME UI) =================
@bot.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🍿 NETFLIX MOVIE HUB

👋 Hi {message.from_user.first_name}

━━━━━━━━━━━━━━━
🎬 Browse unlimited movies
🔥 Trending & Latest updates
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                InlineKeyboardButton("🔥 Trending", callback_data="trending")
            ],
            [
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

        await movies.insert_one({
            "name": message.caption or "Unknown",
            "file_id": message.video.file_id
        })

        print("Movie saved")

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

    # ================= HOME =================
    if data == "home":

        text = """
🍿 NETFLIX MOVIE HUB

🎬 Choose category
"""

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                    InlineKeyboardButton("🔥 Trending", callback_data="trending")
                ],
                [
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

    # ================= DEVELOPER =================
    elif data == "developer":

        text = """
👨‍💻 Developer Info

━━━━━━━━━━━━━━━
🧑 MUHAMMAD SIYAM
🎬 MOVIE BOT XEN3X
⚡ Pyrogram Powered
"""

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ================= MOVIES GRID =================
    elif data == "movies":

        text = """
🎬 MOVIE LIBRARY

👇 Select a movie
"""

        all_movies = await movies.find().to_list(length=10)

        buttons = []
        row = []

        for m in all_movies:
            row.append(
                InlineKeyboardButton(
                    m["name"][:18],
                    callback_data=f"movie_{m['_id']}"
                )
            )

            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        buttons.append([
            InlineKeyboardButton("🔙 Back", callback_data="home")
        ])

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ================= TRENDING =================
    elif data == "trending":

        latest = await movies.find().limit(6).to_list(length=6)

        text = "🔥 TRENDING MOVIES"

        buttons = [
            [
                InlineKeyboardButton(m["name"][:18], callback_data=f"movie_{m['_id']}")
            ]
            for m in latest
        ]

        buttons.append([
            InlineKeyboardButton("🔙 Back", callback_data="home")
        ])

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ================= GENRES =================
    elif data == "genres":

        text = """
🎭 GENRES

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
                    InlineKeyboardButton("🔙 Back", callback_data="home")
                ]
            ]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ================= OPEN MOVIE =================
    elif data.startswith("movie_"):

        movie_id = data.split("_")[1]

        movie = await movies.find_one({"_id": ObjectId(movie_id)})

        if movie:

            await callback_query.message.reply_video(
                movie["file_id"],
                caption=f"🎬 {movie['name']}"
            )

# ================= START BOT =================
print("Bot Started...")
keep_alive()
bot.run()
