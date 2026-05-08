import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import os
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask
from threading import Thread

# ================= SAFE CONFIG =================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "MovieBot")

PHOTO_URL = "https://i.postimg.cc/XJycncFq/Picsart-26-05-01-12-48-36-061.png"

# ================= VALIDATION =================
if not all([API_ID, API_HASH, BOT_TOKEN, MONGO_URI]):
    print("❌ Missing ENV variables!")
    exit()

# ================= MONGO =================
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DB_NAME]

movies = db.movies
songs = db.songs
bechelor = db.bechelor

print("✅ Mongo Connected")

# ================= BOT =================
bot = Client(
    "MovieBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= FLASK KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

def run():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run).start()

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(client, message):

    text = f"""
🍿 NETFLIX HUB

👋 Hi {message.from_user.first_name}

━━━━━━━━━━━━━━━
🎬 Movies | 🎵 Songs | 📺 Bachelor Point

🔎 Search your favourite movie or series
"""

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Movies", callback_data="movies"),
            InlineKeyboardButton("🎵 Songs", callback_data="songs")
        ],
        [
            InlineKeyboardButton("📺 Bachelor Point", callback_data="bechelor")
        ]
    ])

    await message.reply_photo(
        photo=PHOTO_URL,
        caption=text,
        reply_markup=buttons
    )

# ================= SAVE CONTENT =================
@bot.on_message(filters.channel)
async def save_content(client, message):

    try:

        print("📥 New Channel Post")

        file_id = None

        # ===== VIDEO =====
        if message.video:
            file_id = message.video.file_id

        # ===== DOCUMENT =====
        elif message.document:
            file_id = message.document.file_id

        # ===== AUDIO =====
        elif message.audio:

            title = message.caption or message.audio.title or "Unknown Song"

            await songs.insert_one({
                "name": title,
                "file_id": message.audio.file_id
            })

            print(f"🎵 Saved Song: {title}")
            return

        # ===== NO FILE =====
        if not file_id:
            return

        caption = (message.caption or "").lower()

        # ===== BACHELOR POINT =====
        if "#bachelor" in caption:

            await bechelor.insert_one({
                "name": message.caption or "Bachelor Point",
                "file_id": file_id
            })

            print(f"📺 Saved Bachelor Point: {message.caption}")

        # ===== MOVIES =====
        else:

            await movies.insert_one({
                "name": message.caption or "Unknown Movie",
                "file_id": file_id
            })

            print(f"🎬 Saved Movie: {message.caption}")

    except Exception as e:
        print("SAVE ERROR:", e)

# ================= CALLBACK =================
@bot.on_callback_query()
async def callback(client, query):

    data = query.data

    try:

        # ===== HOME =====
        if data == "home":

            text = """
🍿 NETFLIX HUB

🎬 Movies | 🎵 Songs | 📺 Bachelor Point
"""

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 Movies", callback_data="movies"),
                    InlineKeyboardButton("🎵 Songs", callback_data="songs")
                ],
                [
                    InlineKeyboardButton("📺 Bachelor Point", callback_data="bechelor")
                ]
            ])

            await query.message.edit_media(
                InputMediaPhoto(PHOTO_URL, text),
                reply_markup=buttons
            )

        # ===== MOVIES LIST =====
        elif data == "movies":

            data_list = await movies.find().to_list(length=20)

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

            buttons.append([
                InlineKeyboardButton("🔙 Back", callback_data="home")
            ])

            await query.message.edit_media(
                InputMediaPhoto(PHOTO_URL, "🎬 Movies"),
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # ===== SONGS LIST =====
        elif data == "songs":

            data_list = await songs.find().to_list(length=20)

            buttons = []
            row = []

            for s in data_list:

                row.append(
                    InlineKeyboardButton(
                        s.get("name", "Song")[:18],
                        callback_data=f"song_{str(s['_id'])}"
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

            await query.message.edit_media(
                InputMediaPhoto(PHOTO_URL, "🎵 Songs"),
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # ===== BACHELOR POINT LIST =====
        elif data == "bechelor":

            data_list = await bechelor.find().to_list(length=20)

            buttons = []
            row = []

            for b in data_list:

                row.append(
                    InlineKeyboardButton(
                        b.get("name", "Bachelor")[:18],
                        callback_data=f"bechelor_{str(b['_id'])}"
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

            await query.message.edit_media(
                InputMediaPhoto(PHOTO_URL, "📺 Bachelor Point"),
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # ===== PLAY MOVIE =====
        elif data.startswith("movie_"):

            try:

                mid = data.split("_")[1]

                movie = await movies.find_one({
                    "_id": ObjectId(mid)
                })

                if movie:

                    try:
                        await query.message.reply_video(
                            movie["file_id"],
                            caption=f"🎬 {movie['name']}"
                        )

                    except:

                        await query.message.reply_document(
                            movie["file_id"],
                            caption=f"🎬 {movie['name']}"
                        )

            except Exception as e:
                print(e)
                await query.message.reply_text("❌ Movie error")

        # ===== PLAY BACHELOR =====
        elif data.startswith("bechelor_"):

            try:

                bid = data.split("_")[1]

                item = await bechelor.find_one({
                    "_id": ObjectId(bid)
                })

                if item:

                    try:
                        await query.message.reply_video(
                            item["file_id"],
                            caption=f"📺 {item['name']}"
                        )

                    except:

                        await query.message.reply_document(
                            item["file_id"],
                            caption=f"📺 {item['name']}"
                        )

            except Exception as e:
                print(e)
                await query.message.reply_text("❌ Bachelor error")

        # ===== PLAY SONG =====
        elif data.startswith("song_"):

            try:

                sid = data.split("_")[1]

                song = await songs.find_one({
                    "_id": ObjectId(sid)
                })

                if song:

                    await query.message.reply_audio(
                        song["file_id"],
                        caption=f"🎵 {song['name']}"
                    )

            except Exception as e:
                print(e)
                await query.message.reply_text("❌ Song error")

    except Exception as e:
        print("CALLBACK ERROR:", e)

# ================= SEARCH =================
@bot.on_message(filters.private & filters.text)
async def search_movie(client, message):

    if message.text.startswith("/"):
        return

    name = message.text.strip()

    # ===== SEARCH MOVIES =====
    result = await movies.find_one({
        "name": {
            "$regex": name,
            "$options": "i"
        }
    })

    if result:

        await message.reply_video(
            result["file_id"],
            caption=f"🎬 {result['name']}"
        )

        return

    # ===== SEARCH BACHELOR =====
    bechelor_result = await bechelor.find_one({
        "name": {
            "$regex": name,
            "$options": "i"
        }
    })

    if bechelor_result:

        await message.reply_video(
            bechelor_result["file_id"],
            caption=f"📺 {bechelor_result['name']}"
        )

        return

    # ===== SEARCH SONG =====
    song = await songs.find_one({
        "name": {
            "$regex": name,
            "$options": "i"
        }
    })

    if song:

        await message.reply_audio(
            song["file_id"],
            caption=f"🎵 {song['name']}"
        )

        return

    await message.reply_text("😔 No result found")

# ================= RUN BOT =================
print("🚀 Bot Started")
bot.run()
