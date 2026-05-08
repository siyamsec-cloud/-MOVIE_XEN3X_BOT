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
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "MovieBot")

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

print("✅ DB Connected")

# ================= BOT =================
bot = Client(
    "NetflixBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()

# ================= ADMIN CHECK =================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
✨ 𝗡𝗘𝗧𝗙𝗟𝗜𝗫 𝗛𝗨𝗕 𝗣𝗥𝗢 ✨

👋 Welcome {message.from_user.first_name}

━━━━━━━━━━━━━━━
🎬 Movies | 🎵 Songs | 📺 Bachelor Point
"""

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Movies", callback_data="movies_0"),
            InlineKeyboardButton("🎵 Songs", callback_data="songs_0")
        ],
        [
            InlineKeyboardButton("📺 Bachelor Point", callback_data="bechelor_0")
        ],
        [
            InlineKeyboardButton("🔐 Admin", callback_data="admin")
        ]
    ])

    await message.reply_photo(
        photo=PHOTO_URL,
        caption=text,
        reply_markup=buttons
    )

# ================= AUTO POSTER =================
def poster(title, category):

    if category == "movie":
        emoji = "🎬 MOVIE"
    elif category == "song":
        emoji = "🎵 SONG"
    else:
        emoji = "📺 BACHELOR"

    return f"""
✨ {emoji} RELEASED ✨

━━━━━━━━━━━━━━━
📌 TITLE: {title}
━━━━━━━━━━━━━━━

🔥 NETFLIX HUB PRO
"""

# ================= SAVE CONTENT =================
@bot.on_message(filters.channel)
async def save(client, message):

    try:

        file_id = None

        if message.video:
            file_id = message.video.file_id

        elif message.document:
            file_id = message.document.file_id

        elif message.audio:

            await songs.insert_one({
                "name": message.caption or "Song",
                "file_id": message.audio.file_id
            })

            return

        if not file_id:
            return

        caption = (message.caption or "").lower()

        # ===== BACHELOR =====
        if "#bachelor" in caption:

            await bechelor.insert_one({
                "name": message.caption,
                "file_id": file_id
            })

            await message.reply_text(poster(message.caption, "bachelor"))

        # ===== MOVIES =====
        else:

            await movies.insert_one({
                "name": message.caption,
                "file_id": file_id
            })

            await message.reply_text(poster(message.caption, "movie"))

    except Exception as e:
        print("SAVE ERROR:", e)

# ================= ADMIN PANEL =================
@bot.on_message(filters.command("admin"))
async def admin(client, message):

    if not is_admin(message.from_user.id):
        return await message.reply("❌ Access Denied")

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ]
    ])

    await message.reply_text("🔐 ADMIN PANEL", reply_markup=buttons)

# ================= ADMIN CALLBACK =================
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

        await query.message.reply_text(f"""
📊 BOT STATS

🎬 Movies: {m}
🎵 Songs: {s}
📺 Bachelor: {b}
""")

    # ===== MOVIES LIST =====
    if data.startswith("movies_"):

        page = int(data.split("_")[1])
        limit = 10

        data_list = await movies.find().skip(page * limit).to_list(length=limit)

        buttons = []
        row = []

        for m in data_list:

            row.append(
                InlineKeyboardButton(
                    m.get("name", "Movie")[:18],
                    callback_data=f"movie_{str(m['_id'])}"
                )
            )

            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        nav = []

        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"movies_{page-1}"))

        if len(data_list) == limit:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"movies_{page+1}"))

        if nav:
            buttons.append(nav)

        await query.message.edit_media(
            InputMediaPhoto(PHOTO_URL, "🎬 MOVIES"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ===== BACHELOR =====
    if data.startswith("bechelor_"):

        page = int(data.split("_")[1])
        limit = 10

        data_list = await bechelor.find().skip(page * limit).to_list(length=limit)

        buttons = []
        row = []

        for b in data_list:

            row.append(
                InlineKeyboardButton(
                    b.get("name", "Episode")[:18],
                    callback_data=f"bp_{str(b['_id'])}"
                )
            )

            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        nav = []

        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"bechelor_{page-1}"))

        if len(data_list) == limit:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"bechelor_{page+1}"))

        if nav:
            buttons.append(nav)

        await query.message.edit_media(
            InputMediaPhoto(PHOTO_URL, "📺 BACHELOR POINT"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ===== PLAY MOVIE =====
    if data.startswith("movie_"):

        mid = data.split("_")[1]

        movie = await movies.find_one({"_id": ObjectId(mid)})

        if movie:
            await query.message.reply_video(movie["file_id"], caption=poster(movie["name"], "movie"))

    # ===== PLAY BACHELOR =====
    if data.startswith("bp_"):

        bid = data.split("_")[1]

        item = await bechelor.find_one({"_id": ObjectId(bid)})

        if item:
            await query.message.reply_video(item["file_id"], caption=poster(item["name"], "bachelor"))

# ================= SEARCH =================
@bot.on_message(filters.private & filters.text)
async def search(client, message):

    if message.text.startswith("/"):
        return

    name = message.text

    movie = await movies.find_one({"name": {"$regex": name, "$options": "i"}})

    if movie:
        await message.reply_video(movie["file_id"], caption=poster(movie["name"], "movie"))
        return

    bp = await bechelor.find_one({"name": {"$regex": name, "$options": "i"}})

    if bp:
        await message.reply_video(bp["file_id"], caption=poster(bp["name"], "bachelor"))
        return

    song = await songs.find_one({"name": {"$regex": name, "$options": "i"}})

    if song:
        await message.reply_audio(song["file_id"])
        return

    await message.reply_text("😔 Not Found")

# ================= RUN =================
print("🚀 Bot Running")
bot.run()
