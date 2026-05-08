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

# ================= ADMIN STATE =================
user_state = {}

def is_admin(uid):
    return uid == ADMIN_ID

# ================= POSTER =================
def poster(title, cat):

    if cat == "movie":
        emoji = "🎬 MOVIE"
    elif cat == "song":
        emoji = "🎵 SONG"
    else:
        emoji = "📺 BACHELOR"

    return f"""
✨ {emoji} RELEASED ✨

━━━━━━━━━━━━━━
📌 {title}
━━━━━━━━━━━━━━

🔥 NETFLIX HUB PRO
"""

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

# ================= ADMIN ACTIONS =================
@bot.on_callback_query()
async def admin_actions(client, query):

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

    # ===== ADD STATES =====
    if data == "add_movie":
        user_state[query.from_user.id] = "movie"
        return await query.message.reply_text("🎬 Send Movie Video")

    if data == "add_song":
        user_state[query.from_user.id] = "song"
        return await query.message.reply_text("🎵 Send Song Audio")

    if data == "add_bp":
        user_state[query.from_user.id] = "bp"
        return await query.message.reply_text("📺 Send Bachelor Video")

    # ===== DELETE =====
    if data.startswith("del_"):

        if not is_admin(query.from_user.id):
            return

        _, typ, id = data.split("_")

        from bson import ObjectId

        if typ == "movie":
            await movies.delete_one({"_id": ObjectId(id)})
        elif typ == "song":
            await songs.delete_one({"_id": ObjectId(id)})
        elif typ == "bp":
            await bechelor.delete_one({"_id": ObjectId(id)})

        return await query.message.edit_text("🗑 Deleted Successfully")

# ================= SAVE SYSTEM =================
@bot.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def save(client, message):

    uid = message.from_user.id

    if not is_admin(uid):
        return

    state = user_state.get(uid)

    # ===== MOVIE =====
    if state == "movie":

        file_id = message.video.file_id if message.video else message.document.file_id

        data = await movies.insert_one({
            "name": message.caption or "Movie",
            "file_id": file_id
        })

        user_state.pop(uid, None)

        await message.reply_photo(
            PHOTO_URL,
            caption=poster(message.caption, "movie")
        )

    # ===== SONG =====
    elif state == "song":

        await songs.insert_one({
            "name": message.caption or "Song",
            "file_id": message.audio.file_id
        })

        user_state.pop(uid, None)

        await message.reply_text("🎵 Song Added")

    # ===== BACHELOR =====
    elif state == "bp":

        file_id = message.video.file_id if message.video else message.document.file_id

        await bechelor.insert_one({
            "name": message.caption or "Bachelor",
            "file_id": file_id
        })

        user_state.pop(uid, None)

        await message.reply_photo(
            PHOTO_URL,
            caption=poster(message.caption, "bachelor")
        )

# ================= RUN =================
print("🚀 Bot Running")
bot.run()
