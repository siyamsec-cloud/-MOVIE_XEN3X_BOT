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
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

ADMIN_ID = 6298355162
DB_NAME = "XEN3X"

POSTER = "https://i.postimg.cc/XJycncFq/Picsart-26-05-01-12-48-36-061.png"

# ================= CHECK =================
if not all([API_ID, API_HASH, BOT_TOKEN, MONGO_URI]):
    print("❌ Missing ENV Variables")
    exit()

# ================= DB =================
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DB_NAME]

movies = db.movies
songs = db.songs
series = db.series

# ================= BOT =================
bot = Client(
    "XEN3X_BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "XEN3X BOT RUNNING"

Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()

# ================= STATE =================
state = {}

def is_admin(uid):
    return uid == ADMIN_ID

# ================= UI DESIGN =================
def poster(title, typ):

    icon = {
        "movie": "🎬 MOVIE",
        "song": "🎵 SONG",
        "series": "📺 SERIES"
    }

    return f"""
🔥 {icon[typ]} RELEASED 🔥

━━━━━━━━━━━━━━
📌 {title}
━━━━━━━━━━━━━━
⚡ XEN3X STREAM HUB
"""

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(_, msg):

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Movies", callback_data="movies"),
            InlineKeyboardButton("🎵 Songs", callback_data="songs")
        ],
        [
            InlineKeyboardButton("📺 Series", callback_data="series")
        ],
        [
            InlineKeyboardButton("🔐 Admin Panel", callback_data="admin")
        ]
    ])

    await msg.reply_photo(
        POSTER,
        caption="🍿 Welcome to XEN3X Movie Hub\nSelect category below 👇",
        reply_markup=kb
    )

# ================= ADMIN PANEL =================
@bot.on_callback_query(filters.regex("admin"))
async def admin(_, q):

    if not is_admin(q.from_user.id):
        return await q.answer("❌ No Access")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [
            InlineKeyboardButton("🎬 Add Movie", callback_data="add_movie"),
            InlineKeyboardButton("🎵 Add Song", callback_data="add_song")
        ],
        [
            InlineKeyboardButton("📺 Add Series", callback_data="add_series")
        ]
    ])

    await q.message.reply_text("🔐 XEN3X ADMIN PANEL", reply_markup=kb)

# ================= CALLBACK =================
@bot.on_callback_query()
async def cb(_, q):

    data = q.data

    # ===== STATS =====
    if data == "stats":

        m = await movies.count_documents({})
        s = await songs.count_documents({})
        r = await series.count_documents({})

        return await q.message.reply_text(
            f"📊 XEN3X STATS\n\n🎬 Movies: {m}\n🎵 Songs: {s}\n📺 Series: {r}"
        )

    # ===== SET STATE =====
    if data == "add_movie":
        state[q.from_user.id] = "movie"
        return await q.message.reply_text("🎬 Send Movie Video")

    if data == "add_song":
        state[q.from_user.id] = "song"
        return await q.message.reply_text("🎵 Send Song Audio")

    if data == "add_series":
        state[q.from_user.id] = "series"
        return await q.message.reply_text("📺 Send Series Video")

# ================= SAVE SYSTEM =================
@bot.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def save(_, msg):

    if not is_admin(msg.from_user.id):
        return

    st = state.get(msg.from_user.id)

    file_id = None

    # ===== VIDEO FIX =====
    if msg.video:
        file_id = msg.video.file_id

    elif msg.document and msg.document.mime_type and "video" in msg.document.mime_type:
        file_id = msg.document.file_id

    elif msg.audio:
        file_id = msg.audio.file_id

    if not file_id:
        return await msg.reply("❌ Invalid File")

    # ===== MOVIE =====
    if st == "movie":

        await movies.insert_one({
            "name": msg.caption or "Movie",
            "file_id": file_id
        })

        state.pop(msg.from_user.id, None)
        return await msg.reply("🎬 Movie Added Successfully")

    # ===== SONG =====
    if st == "song":

        await songs.insert_one({
            "name": msg.caption or "Song",
            "file_id": file_id
        })

        state.pop(msg.from_user.id, None)
        return await msg.reply("🎵 Song Added Successfully")

    # ===== SERIES =====
    if st == "series":

        await series.insert_one({
            "name": msg.caption or "Series",
            "file_id": file_id
        })

        state.pop(msg.from_user.id, None)
        return await msg.reply("📺 Series Added Successfully")

# ================= PLAY =================
@bot.on_callback_query(filters.regex("movie_"))
async def play_movie(_, q):

    m = await movies.find_one({"_id": ObjectId(q.data.split("_")[1])})

    if m:
        await q.message.reply_video(m["file_id"], caption=m["name"])

@bot.on_callback_query(filters.regex("song_"))
async def play_song(_, q):

    s = await songs.find_one({"_id": ObjectId(q.data.split("_")[1])})

    if s:
        await q.message.reply_audio(s["file_id"], caption=s["name"])

@bot.on_callback_query(filters.regex("series_"))
async def play_series(_, q):

    r = await series.find_one({"_id": ObjectId(q.data.split("_")[1])})

    if r:
        await q.message.reply_video(r["file_id"], caption=r["name"])

# ================= RUN =================
print("🚀 XEN3X BOT RUNNING")
bot.run()
