from pyrogram import Client, filters
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]

# Collections
users_collection = db["users"]
admins_collection = db["admins"]
settings_collection = db["settings"]

# Initialize Pyrogram Client
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def is_admin(user_id):
    return admins_collection.find_one({"_id": user_id}) is not None

@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id

    # Store user ID in MongoDB
    users_collection.update_one({"_id": user_id}, {"$set": {"id": user_id}}, upsert=True)

    # Get welcome message
    msg_data = settings_collection.find_one({"_id": "welcome_msg"})
    welcome_msg = msg_data["message"] if msg_data else "Welcome to the bot!"

    

@bot.on_message(filters.command("setmsg"))
def set_welcome_message(client, message):
    if not is_admin(message.from_user.id):
        return message.reply_text("You are not an admin.")

    new_message = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if new_message:
        settings_collection.update_one({"_id": "welcome_msg"}, {"$set": {"message": new_message}}, upsert=True)
        message.reply_text("Welcome message updated!")
    else:
        message.reply_text("Please provide a new message.")

@bot.on_message(filters.command("broadcast"))
def broadcast(client, message):
    if not is_admin(message.from_user.id):
        return message.reply_text("You are not an admin.")

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
        message.reply_text(f"Broadcast sent to {count} users.")
    else:
        message.reply_text("Please provide a message to broadcast.")
