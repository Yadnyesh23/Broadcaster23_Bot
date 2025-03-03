from pyrogram import Client, filters
from pymongo import MongoClient
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Load from environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Your Telegram ID

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
users_collection = db["users"]
settings_collection = db["settings"]

# Initialize Pyrogram Client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to get welcome message
def get_welcome_message():
    msg_data = settings_collection.find_one({"_id": "welcome_msg"})
    return msg_data["message"] if msg_data else "Welcome to the bot!"

# Bot Activation - Send welcome message on /start
@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    users_collection.update_one({"_id": user_id}, {"$set": {"id": user_id}}, upsert=True)
    welcome_msg = get_welcome_message()
    message.reply_text(welcome_msg)

# Admin - Set Custom Welcome Message
@bot.on_message(filters.command("setmsg") & filters.user(ADMIN_ID))
def set_welcome_message(client, message):
    new_message = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if new_message:
        settings_collection.update_one({"_id": "welcome_msg"}, {"$set": {"message": new_message}}, upsert=True)
        message.reply_text("✅ Welcome message updated!")
    else:
        message.reply_text("❌ Please provide a new message.")

# Admin - Broadcast Message
@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
def broadcast(client, message):
    text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if text:
        users = users_collection.find()
        count = 0
        for user in users:
            try:
                bot.send_message(user["_id"], text)
                count += 1
            except:
                pass
        message.reply_text(f"✅ Broadcast sent to {count} users.")
    else:
        message.reply_text("❌ Please provide a message to broadcast.")

print("🤖 Bot is running...")
bot.run()
