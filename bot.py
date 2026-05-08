‎import asyncio
‎asyncio.set_event_loop(asyncio.new_event_loop())
‎
‎import os
‎from pyrogram import Client, filters
‎from pyrogram.types import (
‎    InlineKeyboardMarkup,
‎    InlineKeyboardButton,
‎    InputMediaPhoto
‎)
‎from motor.motor_asyncio import AsyncIOMotorClient
‎from flask import Flask
‎from threading import Thread
‎
‎# ================= CONFIG =================
‎API_ID = int(os.getenv("API_ID"))
‎API_HASH = os.getenv("API_HASH")
‎BOT_TOKEN = os.getenv("BOT_TOKEN")
‎
‎MONGO_URI = os.getenv("MONGO_URI")
‎DB_NAME = os.getenv("DB_NAME", "MovieBot")
‎CHANNEL_ID = int(os.getenv("BIN_CHANNEL"))
‎
‎PHOTO_URL = "https://i.postimg.cc/d3k4WY38/file-00000000af0c720bb7bcdf801169a1bb.png"
‎
‎# ================= MONGO =================
‎mongo = AsyncIOMotorClient(MONGO_URI)
‎db = mongo[DB_NAME]
‎movies = db.movies
‎
‎print("Mongo Connected!")
‎
‎# ================= BOT =================
‎bot = Client(
‎    "MovieBot",
‎    api_id=API_ID,
‎    api_hash=API_HASH,
‎    bot_token=BOT_TOKEN
‎)
‎
‎# ================= FLASK =================
‎app = Flask(__name__)
‎
‎@app.route("/")
‎def home():
‎    return "Bot is running!"
‎
‎def run():
‎    app.run(host="0.0.0.0", port=10000)
‎
‎def keep_alive():
‎    Thread(target=run).start()
‎
‎# ================= START =================
‎@bot.on_message(filters.command("start"))
‎async def start(client, message):
‎
‎    text = f"""
‎🎬 MOVIE | XEN3X
‎
‎👋 Welcome {message.from_user.first_name}
‎
‎━━━━━━━━━━━━━━━
‎✨ Welcome to the best movie bot
‎
‎📌 Features:
‎• Movies
‎• Songs
‎• Fast Search
‎• Auto Filter
‎
‎━━━━━━━━━━━━━━━
‎🔎 Search your favourite movie or song
‎"""
‎
‎    buttons = InlineKeyboardMarkup(
‎        [
‎            [
‎                InlineKeyboardButton(
‎                    "👨‍💻 Developer Info",
‎                    callback_data="developer"
‎                )
‎            ],
‎            [
‎                InlineKeyboardButton(
‎                    "🎬 Upcoming Movies",
‎                    callback_data="upcoming"
‎                )
‎            ],
‎            [
‎                InlineKeyboardButton(
‎                    "🔥 Updates Channel",
‎                    url="https://t.me/moviexen3x"
‎                )
‎            ]
‎        ]
‎    )
‎
‎    await message.reply_photo(
‎        photo=PHOTO_URL,
‎        caption=text,
‎        reply_markup=buttons
‎    )
‎
‎# ================= SAVE MOVIES =================
‎@bot.on_message(filters.channel & filters.chat(CHANNEL_ID))
‎async def save_movie(client, message):
‎
‎    if message.video:
‎
‎        name = message.caption or "Unknown"
‎
‎        await movies.insert_one({
‎            "name": name,
‎            "file_id": message.video.file_id
‎        })
‎
‎        print(f"Saved movie: {name}")
‎
‎# ================= SEARCH =================
‎@bot.on_message(filters.private & filters.text)
‎async def search_movie(client, message):
‎
‎    if message.text.startswith("/"):
‎        return
‎
‎    movie_name = message.text.strip()
‎
‎    result = await movies.find_one({
‎        "name": {"$regex": movie_name, "$options": "i"}
‎    })
‎
‎    if result:
‎
‎        await message.reply_video(
‎            result["file_id"],
‎            caption=f"🎬 {result['name']}"
‎        )
‎
‎    else:
‎        await message.reply_text(
‎            f"😔 No movie found for: {movie_name}"
‎        )
‎
‎# ================= CALLBACK =================
‎@bot.on_callback_query()
‎async def callback(client, callback_query):
‎
‎    data = callback_query.data
‎
‎    # ===== Developer =====
‎    if data == "developer":
‎
‎        text = """
‎👨‍💻 Developer Information
‎
‎━━━━━━━━━━━━━━━
‎🧑 Name: MUHAMMAD SIYAM
‎🎬 Bot Name: MOVIE | XEN3X
‎⚡ Powered By Pyrogram
‎━━━━━━━━━━━━━━━
‎"""
‎
‎        buttons = InlineKeyboardMarkup(
‎            [
‎                [
‎                    InlineKeyboardButton(
‎                        "🔙 Back",
‎                        callback_data="back"
‎                    )
‎                ]
‎            ]
‎        )
‎
‎        await callback_query.message.edit_media(
‎            media=InputMediaPhoto(
‎                PHOTO_URL,
‎                caption=text
‎            ),
‎            reply_markup=buttons
‎        )
‎
‎    # ===== Upcoming =====
‎    elif data == "upcoming":
‎
‎        text = """
‎🎬 Upcoming Movies
‎
‎━━━━━━━━━━━━━━━
‎• DHURANDHAR
‎• Leo
‎• SITA RAM
‎• Salaar
‎• MAALIK
‎━━━━━━━━━━━━━━━
‎"""
‎
‎        buttons = InlineKeyboardMarkup(
‎            [
‎                [
‎                    InlineKeyboardButton(
‎                        "🔙 Back",
‎                        callback_data="back"
‎                    )
‎                ]
‎            ]
‎        )
‎
‎        await callback_query.message.edit_caption(
‎            caption=text,
‎            reply_markup=buttons
‎        )
‎
‎    # ===== Back =====
‎    elif data == "back":
‎
‎        text = f"""
‎🎬 MOVIE | XEN3X
‎
‎👋 Welcome {callback_query.from_user.first_name}
‎
‎━━━━━━━━━━━━━━━
‎✨ Welcome to the best movie bot
‎
‎📌 Features:
‎• Movies
‎• Songs
‎• Fast Search
‎• Auto Filter
‎
‎━━━━━━━━━━━━━━━
‎🔎 Search your favourite movie or song
‎"""
‎
‎        buttons = InlineKeyboardMarkup(
‎            [
‎                [
‎                    InlineKeyboardButton(
‎                        "👨‍💻 Developer Info",
‎                        callback_data="developer"
‎                    )
‎                ],
‎                [
‎                    InlineKeyboardButton(
‎                        "🎬 Upcoming Movies",
‎                        callback_data="upcoming"
‎                    )
‎                ],
‎                [
‎                    InlineKeyboardButton(
‎                        "🔥 Updates Channel",
‎                        url="https://t.me/"
‎                    )
‎                ]
‎            ]
‎        )
‎
‎        await callback_query.message.edit_media(
‎            media=InputMediaPhoto(
‎                PHOTO_URL,
‎                caption=text
‎            ),
‎            reply_markup=buttons
‎        )
‎
‎# ================= START BOT =================
‎print("Bot Started...")
‎keep_alive()
‎bot.run()
‎
