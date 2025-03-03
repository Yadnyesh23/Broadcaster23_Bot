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

# Function to check if a user is an admin
def is_admin(user_id):
    return admins_collection.find_one({"_id": int(user_id)}) is not None  # Ensure ID is an integer

# Handle `/start` command (Registers Users)
@bot.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id

    # Store user ID in MongoDB (if not already registered)
    users_collection.update_one({"_id": user_id}, {"$set": {"id": user_id}}, upsert=True)

    # Get welcome message
    msg_data = settings_collection.find_one({"_id": "welcome_msg"})
    welcome_msg = msg_data["message"] if msg_data else "Welcome to the bot!"

    message.reply_text(welcome_msg)

# ✅ Add a New Admin (Only Existing Admins Can Use)
@bot.on_message(filters.command("addadmin"))
def add_admin(client, message):
    if not is_admin(message.from_user.id):  
        return message.reply_text("❌ You are not authorized to use this command.")

    try:
        new_admin_id = int(message.text.split()[1])  # Extract user ID from command
        if is_admin(new_admin_id):
            return message.reply_text("✅ User is already an admin.")
        
        admins_collection.insert_one({"_id": new_admin_id})  # Add to MongoDB
        message.reply_text(f"✅ Added {new_admin_id} as an admin.")
    
    except Exception as e:
        message.reply_text("❌ Invalid ID. Use: /addadmin <user_id>")
        print(f"Error adding admin: {str(e)}")

# ✅ Remove an Admin (Only Admins Can Remove Other Admins)
@bot.on_message(filters.command("removeadmin"))
def remove_admin(client, message):
    if not is_admin(message.from_user.id):  
        return message.reply_text("❌ You are not authorized to use this command.")

    try:
        remove_admin_id = int(message.text.split()[1])  
        if not is_admin(remove_admin_id):
            return message.reply_text("❌ User is not an admin.")
        
        admins_collection.delete_one({"_id": remove_admin_id})  
        message.reply_text(f"✅ Removed {remove_admin_id} from admin list.")
    
    except:
        message.reply_text("❌ Invalid ID. Use: /removeadmin <user_id>")

# ✅ List All Admins
@bot.on_message(filters.command("listadmins"))
def list_admins(client, message):
    admin_list = admins_collection.find()
    admins = [str(admin["_id"]) for admin in admin_list]

    if admins:
        message.reply_text("👑 Admins:\n" + "\n".join(admins))
    else:
        message.reply_text("❌ No admins found.")

# ✅ Set Custom Welcome Message (Admin Only)
@bot.on_message(filters.command("setmsg"))
def set_welcome_message(client, message):
    if not is_admin(message.from_user.id):
        return message.reply_text("❌ You are not an admin.")

    new_message = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if new_message:
        settings_collection.update_one({"_id": "welcome_msg"}, {"$set": {"message": new_message}}, upsert=True)
        message.reply_text("✅ Welcome message updated!")
    else:
        message.reply_text("❌ Please provide a new message.")

# ✅ Broadcast a Message to All Users (Admin Only)
@bot.on_message(filters.command("broadcast"))
def broadcast(client, message):
    if not is_admin(message.from_user.id):
        return message.reply_text("❌ You are not an admin.")

    text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if text:
        users = users_collection.find()
        count = 0
        for user in users:
            try:
                client.send_message(user["_id"], text)  # Use `client.send_message`, not `bot.send_message`
                count += 1
            except Exception as e:
                print(f"❌ Failed to send message to {user['_id']}: {e}")
        message.reply_text(f"✅ Broadcast sent to {count} users.")
    else:
        message.reply_text("❌ Please provide a message to broadcast.")

# ✅ Run the Bot
print("🤖 Bot is running...")
bot.run()
