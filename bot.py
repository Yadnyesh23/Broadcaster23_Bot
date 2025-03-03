from pyrogram import Client, filters
from pymongo import MongoClient
import os

# Load from environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
users_collection = db["users"]
settings_collection = db["settings"]

# Initialize Pyrogram Client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to get current admin IDs
def get_admins():
    admin_data = settings_collection.find_one({"_id": "admins"})
    return admin_data["admin_ids"] if admin_data else []

# Function to check if a user is an admin
def is_admin(user_id):
    return user_id in get_admins()

# Add a new admin (Command: /addadmin user_id)
@bot.on_message(filters.command("addadmin"))
def add_admin(client, message):
    sender_id = message.from_user.id

    if not is_admin(sender_id):
        return message.reply_text("❌ You are not authorized to add admins.")

    parts = message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].isdigit():
        return message.reply_text("❌ Please provide a valid user ID.")

    new_admin_id = int(parts[1])
    current_admins = get_admins()

    if new_admin_id in current_admins:
        return message.reply_text("⚠️ This user is already an admin.")

    current_admins.append(new_admin_id)
    settings_collection.update_one({"_id": "admins"}, {"$set": {"admin_ids": current_admins}}, upsert=True)

    message.reply_text(f"✅ User {new_admin_id} has been added as an admin!")

# Admin - Set Custom Welcome Message
@bot.on_message(filters.command("setmsg") & filters.create(lambda _, __, message: is_admin(message.from_user.id)))
def set_welcome_message(client, message):
    new_message = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if new_message:
        settings_collection.update_one({"_id": "welcome_msg"}, {"$set": {"message": new_message}}, upsert=True)
        message.reply_text("✅ Welcome message updated!")
    else:
        message.reply_text("❌ Please provide a new message.")

# Admin - Broadcast Message
@bot.on_message(filters.command("broadcast") & filters.create(lambda _, __, message: is_admin(message.from_user.id)))
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
