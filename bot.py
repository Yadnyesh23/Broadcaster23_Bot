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
admin_collection = db["admins"]  # ✅ Now using this for admins

# Initialize Pyrogram Client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to check if a user is an admin
def is_admin(user_id):
    return admin_collection.find_one({"_id": user_id}) is not None  # ✅ More efficient

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

    if is_admin(new_admin_id):
        return message.reply_text("⚠️ This user is already an admin.")

    try:
        admin_collection.insert_one({"_id": new_admin_id})  # ✅ Store admins correctly
        message.reply_text(f"✅ User {new_admin_id} has been added as an admin!")
    except Exception as e:
        message.reply_text("❌ Database error while adding admin.")
        print(f"Error: {e}")

# Admin - Set Custom Welcome Message
@bot.on_message(filters.command("setmsg") & filters.create(lambda _, __, message: is_admin(message.from_user.id)))
def set_welcome_message(client, message):
    new_message = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if new_message:
        try:
            settings_collection.update_one({"_id": "welcome_msg"}, {"$set": {"message": new_message}}, upsert=True)
            message.reply_text("✅ Welcome message updated!")
        except Exception as e:
            message.reply_text("❌ Database error while updating message.")
            print(f"Error: {e}")
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
