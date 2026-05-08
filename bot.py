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

# 👉 এখানে তোমার PHOTO CHANGE হবে
PHOTO_URL = "https://i.postimg.cc/XJycncFq/Picsart-26-05-01-12-48-36-061.png"

# ================= MONGO =================
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DB_NAME]
movies = db.movies
songs = db.songs

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

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🍿 NETFLIX HUB | XEN3X

👋 Hi {message.from_user.first_name}

━━━━━━━━━━━━━━━
🎬 Movies | 🎵 Songs | 🔥 Trending
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                InlineKeyboardButton("🎵 Songs", callback_data="songs")
            ],
            [
                InlineKeyboardButton("🔥 Trending", callback_data="trending")
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
async def save_content(client, message):

    # 🎬 MOVIE SAVE
    if message.video:

        await movies.insert_one({
            "name": message.caption or "Unknown Movie",
            "file_id": message.video.file_id
        })

    # 🎵 SONG SAVE
    if message.audio:

        title = message.caption or message.audio.title or "Unknown Song"

        await songs.insert_one({
            "name": title,
            "file_id": message.audio.file_id
        })

    print("Saved content")

# ================= SEARCH MOVIE =================
@bot.on_message(filters.private & filters.text)
async def search(client, message):

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

# ================= CALLBACK =================
@bot.on_callback_query()
async def callback(client, callback_query):

    data = callback_query.data

    # ================= HOME =================
    if data == "home":

        text = "🍿 NETFLIX HUB"

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                    InlineKeyboardButton("🎵 Songs", callback_data="songs")
                ],
                [
                    InlineKeyboardButton("🔥 Trending", callback_data="trending")
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
👨‍💻 Developer

🧑 MUHAMMAD SIYAM
🎬 XEN3X BOT
"""

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
        )

        await callback_query.message.edit_media(
            media=InputMediaPhoto(PHOTO_URL, caption=text),
            reply_markup=buttons
        )

    # ================= MOVIES =================
    elif data == "movies":

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
            media=InputMediaPhoto(PHOTO_URL, caption="🎬 Movies"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ================= SONGS =================
    elif data == "songs":

        all_songs = await songs.find().to_list(length=10)

        buttons = []
        row = []

        for s in all_songs:
            row.append(
                InlineKeyboardButton(
                    s["name"][:18],
                    callback_data=f"song_{s['_id']}"
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
            media=InputMediaPhoto(PHOTO_URL, caption="🎵 Songs"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ================= PLAY MOVIE =================
    elif data.startswith("movie_"):

        movie_id = data.split("_")[1]

        movie = await movies.find_one({"_id": ObjectId(movie_id)})

        if movie:
            await callback_query.message.reply_video(
                movie["file_id"],
                caption=f"🎬 {movie['name']}"
            )

    # ================= PLAY SONG =================
    elif data.startswith("song_"):

        song_id = data.split("_")[1]

        song = await songs.find_one({"_id": ObjectId(song_id)})

        if song:
            await callback_query.message.reply_audio(
                song["file_id"],
                caption=f"🎵 {song['name']}"
            )

# ================= START BOT =================
print("Bot Started...")
keep_alive()
bot.run()
