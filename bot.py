import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask
from threading import Thread

# ================= CONFIG =================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")

DB_NAME = "MovieBot"
ADMIN_ID = 6298355162

PHOTO_URL = "https://i.postimg.cc/XJycncFq/Picsart-26-05-01-12-48-36-061.png"

if not all([API_ID, API_HASH, BOT_TOKEN, MONGO_URI]):
    print("❌ Missing ENV")
    exit()

# ================= DB =================
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DB_NAME]

movies = db.movies
songs = db.songs
bechelor = db.bechelor

# ================= BOT =================
bot = Client("NetflixBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()

# ================= STATE =================
user_state = {}

def is_admin(uid):
    return uid == ADMIN_ID

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🎬 NETFLIX HUB PRO

👋 Hello {message.from_user.first_name}

━━━━━━━━━━━━━━
🎬 Movies | 🎵 Songs | 📺 Bachelor
"""

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Movies", callback_data="movies_0"),
            InlineKeyboardButton("🎵 Songs", callback_data="songs_0")
        ],
        [
            InlineKeyboardButton("📺 Bachelor", callback_data="bp_0")
        ],
        [
            InlineKeyboardButton("🔐 Admin", callback_data="admin")
        ]
    ])

    await message.reply_photo(PHOTO_URL, text, reply_markup=buttons)

# ================= ADMIN PANEL =================
@bot.on_callback_query(filters.regex("admin"))
async def admin_panel(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer("❌ No Access")

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("🎬 Add Movie", callback_data="add_movie"),
            InlineKeyboardButton("🎵 Add Song", callback_data="add_song")
        ],
        [
            InlineKeyboardButton("📺 Add Bachelor", callback_data="add_bp")
        ]
    ])

    await query.message.reply_text("🔐 ADMIN PANEL", reply_markup=buttons)

# ================= CALLBACK =================
@bot.on_callback_query()
async def callback(client, query):

    data = query.data

    # ===== STATS =====
    if data == "stats":

        if not is_admin(query.from_user.id):
            return

        m = await movies.count_documents({})
        s = await songs.count_documents({})
        b = await bechelor.count_documents({})

        return await query.message.reply_text(
            f"📊 Stats\n🎬 Movies: {m}\n🎵 Songs: {s}\n📺 Bachelor: {b}"
        )

    # ===== SET STATES =====
    if data == "add_movie":
        user_state[query.from_user.id] = "movie"
        return await query.message.reply_text("🎬 Send Movie Video")

    if data == "add_bp":
        user_state[query.from_user.id] = "bp"
        return await query.message.reply_text("📺 Send Bachelor Video")

    if data == "add_song":
        user_state[query.from_user.id] = "song"
        return await query.message.reply_text("🎵 Send Audio Song")

# ================= SAVE FIX (IMPORTANT) =================
@bot.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def save(client, message):

    if not is_admin(message.from_user.id):
        return

    state = user_state.get(message.from_user.id)

    file_id = None

    # 🔥 FIXED VIDEO DETECTION
    if message.video:
        file_id = message.video.file_id

    elif message.document and message.document.mime_type and "video" in message.document.mime_type:
        file_id = message.document.file_id

    elif message.audio:
        file_id = message.audio.file_id

    if not file_id:
        return await message.reply("❌ Invalid file")

    # ===== MOVIE =====
    if state == "movie":

        await movies.insert_one({
            "name": message.caption or "Movie",
            "file_id": file_id
        })

        user_state.pop(message.from_user.id, None)

        return await message.reply("🎬 Movie Added Successfully")

    # ===== BACHELOR =====
    if state == "bp":

        await bechelor.insert_one({
            "name": message.caption or "Bachelor",
            "file_id": file_id
        })

        user_state.pop(message.from_user.id, None)

        return await message.reply("📺 Bachelor Added Successfully")

    # ===== SONG =====
    if state == "song":

        await songs.insert_one({
            "name": message.caption or "Song",
            "file_id": file_id
        })

        user_state.pop(message.from_user.id, None)

        return await message.reply("🎵 Song Added Successfully")

# ================= PLAY MOVIE =================
@bot.on_callback_query(filters.regex("movie_"))
async def play_movie(client, query):

    mid = query.data.split("_")[1]

    movie = await movies.find_one({"_id": ObjectId(mid)})

    if movie:
        await query.message.reply_video(movie["file_id"], caption=movie["name"])

# ================= PLAY BACHELOR =================
@bot.on_callback_query(filters.regex("bp_"))
async def play_bp(client, query):

    bid = query.data.split("_")[1]

    bp = await bechelor.find_one({"_id": ObjectId(bid)})

    if bp:
        await query.message.reply_video(bp["file_id"], caption=bp["name"])

# ================= RUN =================
print("🚀 Bot Running")
bot.run()
