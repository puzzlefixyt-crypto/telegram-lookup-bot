from flask import Flask
import requests
import time
from datetime import datetime, timedelta
import os
import threading
import re
import json
import random
import string
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# ===== MONGODB SETUP =====
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    db = mongo_client["deepxtrace_bot"]
    
    # Collections
    users_col = db["users"]
    groups_col = db["groups"]
    channels_col = db["channels"]
    admins_col = db["admins"]
    verified_users_col = db["verified_users"]
    active_users_col = db["active_users"]
    used_keys_col = db["used_keys"]
    keys_col = db["keys"]
    disabled_commands_col = db["disabled_commands"]
    bot_settings_col = db["bot_settings"]
    
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")
    print("Please set MONGO_URI environment variable")
    exit(1)

# ===== PUBLIC COMMAND HELP CONFIG =====
BOT_USERNAME = "@DeepTraceXBot"

PUBLIC_HELP_MAP = {
    "/num": "💡 Usage: /num 98XXXXXXXX",
    "/upi": "💡 Usage: /upi username@bank",
    "/fam": "💡 Usage: /fam username@fam",
    "/gst": "💡 Usage: /gst 24ABCDE1234F1Z5",
    "/vehicle": "💡 Usage: /vehicle GJ01AB1234",
    "/tg": "💡 Usage: /tg @username",
    "/ifsc": "💡 Usage: /ifsc SBIN0000000",
    "/aadhaar": "💡 Usage: /aadhaar 12XXXXXXXXXX",
    "/trace": "💡 Usage: /trace 98XXXXXXXX",
    "/gmail": "💡 Usage: /gmail example@gmail.com",
    "/vnum": "💡 Usage: /vnum GJ03HD0255"
}

# ===== KEEP ALIVE FOR RENDER =====
app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_web, daemon=True).start()
# ================================

# ================= CONFIG =================
DISABLED_COMMANDS_FILE = "disabled_commands.json"
FORCE_JOIN_CHANNEL = "@DeepXTraceOfficial"
VERIFIED_USERS_FILE = "verified_users.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
# ===== BOT STATS FILE =====
STATS_FILE = "bot_stats.json"
if not BOT_TOKEN:
    print("Error: BOT_TOKEN not set in environment variables!")
    print("Please set BOT_TOKEN in Render Environment Variables")
    exit(1)

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

MOBILE_API = "https://api.b77bf911.workers.dev/mobile?number="
AADHAAR_API = "https://api.b77bf911.workers.dev/aadhaar?id="
GST_API = "https://api.b77bf911.workers.dev/gst?number="
IFSC_API = "https://api.b77bf911.workers.dev/ifsc?code="
UPI_API = "https://api.b77bf911.workers.dev/upi?id="
FAM_API = "https://api.b77bf911.workers.dev/upi2?id="
VEHICLE_API = "https://api.b77bf911.workers.dev/vehicle?registration="
VNUM_API = "https://api.paanel.shop/numapi.php?action=api&key=num_wanted&test1="
OSINT_API = "https://api.b77bf911.workers.dev/telegram?user="
TRACE_API = "https://king.mr-unknown.workers.dev/Pera?track="
GMAIL_API = "https://king.mr-unknown.workers.dev/Pera?mail="


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json"
}
WELCOME_MESSAGE = (
    "🛰️ DeepTraceXBot Intelligence\n\n"
    "ᴍᴏʙɪʟᴇ: /num 98XXXXXX10\n"
    "ᴀᴀᴅʜᴀᴀʀ: /aadhaar 1234XXXX9012\n"
    "ɢsᴛ: /gst 24ABCDE1234F1Z5\n"
    "ɪғsᴄ: /ifsc SBIN0000000\n"
    "ᴜᴘɪ: /upi username@bank\n"
    "ғᴀᴍ: /fam username@fam\n"
    "ᴠᴇʜɪᴄʟᴇ: /vehicle GJ01AB1234\n"
    "ᴠɴᴜᴍ: /vnum GJ03HD0255\n"
    "ᴛᴇʟᴇɢʀᴀᴍ: /tg @username\n"
    "ᴛʀᴀᴄᴇ: /trace 98XXXXXXXX\n"
    "ɢᴍᴀɪʟ: /gmail example@gmail.com\n\n"
    "📩 Admin: /admin your message\n"
    "📄 Files auto-delete in 60s"
)
COMMAND_ORDER = [
    ("num", "ᴍᴏʙɪʟᴇ: /num 98XXXXXX10"),
    ("aadhaar", "ᴀᴀᴅʜᴀᴀʀ: /aadhaar 1234XXXX9012"),
    ("gst", "ɢsᴛ: /gst 24ABCDE1234F1Z5"),
    ("ifsc", "ɪғsᴄ: /ifsc SBIN0000000"),
    ("upi", "ᴜᴘɪ: /upi username@bank"),
    ("fam", "ғᴀᴍ: /fam username@fam"),
    ("vehicle", "ᴠᴇʜɪᴄʟᴇ: /vehicle GJ01AB1234"),
    ("vnum", "ᴠɴᴜᴍ: /vnum GJ03HD0255"),
    ("tg", "ᴛᴇʟᴇɢʀᴀᴍ: /tg @username"),
    ("trace", "ᴛʀᴀᴄᴇ: /trace 98XXXXXXXX"),
    ("gmail", "ɢᴍᴀɪʟ: /gmail example@gmail.com"),
]

def get_welcome_message():
    disabled = load_disabled_commands()
    lines = ["🛰️ DeepTraceXBot Intelligence\n"]

    for cmd, text in COMMAND_ORDER:
        if cmd not in disabled:
            lines.append(text)

    lines.append("\n📩 Admin: /admin your message")
    lines.append("📄 Files auto-delete in 60s")
    return "\n".join(lines)
BOT_USERNAME = "@DeepTraceXBot"

HELP_MAP = {
    "/num": "💡 Usage: /num 98XXXXXXXX",
    "/upi": "💡 Usage: /upi username@bank",
    "/fam": "💡 Usage: /fam username@fam",
    "/gst": "💡 Usage: /gst 24ABCDE1234F1Z5",
    "/vehicle": "💡 Usage: /vehicle GJ01AB1234",
    "/vnum": "💡 Usage: /vnum GJ03HD0255",
    "/tg": "💡 Usage: /tg @username",
    "/ifsc": "💡 Usage: /ifsc SBIN0000000",
    "/aadhar": "💡 Usage: /aadhar 12XXXXXXXXXX",
    "/trace": "💡 Usage: /trace 98XXXXXXXX",
    "/gmail": "💡 Usage: /gmail example@gmail.com"
}

# ================= ADMIN CONFIG =================
ADMIN_IDS = [5221493804]

# ================= LICENCE FILES =================
KEYS_FILE = "keys.txt"
USED_KEYS_FILE = "used_keys.json"
ACTIVE_USERS_FILE = "active_users.json"

# -------- CREATE & SET EVENT LOOP (Python 3.13 FIX) --------

# -------- TELETHON CLIENT --------

# ================= MONGODB DATABASE FUNCTIONS =================

def get_force_join_channel():
    """Get current force join channel from MongoDB"""
    setting = bot_settings_col.find_one({"key": "force_join_channel"})
    if setting:
        return setting.get("value", "@DeepXTraceOfficial")
    return "@DeepXTraceOfficial"

def set_force_join_channel(channel_link):
    """Set force join channel in MongoDB"""
    bot_settings_col.update_one(
        {"key": "force_join_channel"},
        {"$set": {"value": channel_link, "updated_at": datetime.now()}},
        upsert=True
    )

def register_chat(chat_id, chat_type, member_count=0):
    """Register group/channel in MongoDB"""
    if chat_type == "private":
        users_col.update_one(
            {"user_id": chat_id},
            {"$set": {"user_id": chat_id, "last_active": datetime.now()}},
            upsert=True
        )
    elif chat_type in ["group", "supergroup"]:
        groups_col.update_one(
            {"group_id": chat_id},
            {"$set": {"group_id": chat_id, "member_count": member_count, "last_active": datetime.now()}},
            upsert=True
        )
    elif chat_type == "channel":
        channels_col.update_one(
            {"channel_id": chat_id},
            {"$set": {"channel_id": chat_id, "member_count": member_count, "last_active": datetime.now()}},
            upsert=True
        )

def get_all_chats():
    """Get all registered chats for broadcast"""
    all_chats = []
    
    # Get all users
    for user in users_col.find():
        all_chats.append({"chat_id": user["user_id"], "type": "private"})
    
    # Get all groups
    for group in groups_col.find():
        all_chats.append({"chat_id": group["group_id"], "type": "group"})
    
    # Get all channels
    for channel in channels_col.find():
        all_chats.append({"chat_id": channel["channel_id"], "type": "channel"})
    
    return all_chats

def check_member_count_requirement(chat_id, chat_type):
    """Check if group/channel has minimum 30 members"""
    if chat_type == "private":
        return True
    
    try:
        chat_info = requests.get(
            TG_API + "/getChat",
            params={"chat_id": chat_id}
        ).json()
        
        if not chat_info.get("ok"):
            return True
        
        # Get member count
        member_count_response = requests.get(
            TG_API + "/getChatMemberCount",
            params={"chat_id": chat_id}
        ).json()
        
        if member_count_response.get("ok"):
            member_count = member_count_response.get("result", 0)
            register_chat(chat_id, chat_type, member_count)
            return member_count >= 30
        
        return True
    except:
        return True

# ================= LICENCE FUNCTIONS =================
def init_licence_files():
    # MongoDB handles initialization automatically
    pass

def load_keys():
    """Load keys from MongoDB"""
    keys_list = []
    for key_doc in keys_col.find():
        keys_list.append(key_doc["key"])
    return keys_list

def save_key(key):
    """Save key to MongoDB"""
    keys_col.insert_one({"key": key, "created_at": datetime.now()})

def load_used_keys():
    """Load used keys from MongoDB"""
    used_keys = {}
    for doc in used_keys_col.find():
        used_keys[doc["key"]] = {
            "user_id": doc["user_id"],
            "chat_id": doc["chat_id"],
            "activated_at": doc["activated_at"],
            "expiry": doc["expiry"]
        }
    return used_keys

def save_used_keys(data):
    """Save used keys to MongoDB"""
    # This function is kept for compatibility but not needed with MongoDB
    pass

def load_active_users():
    """Load active users from MongoDB"""
    active_users = {}
    for doc in active_users_col.find():
        user_key = f"{doc['user_id']}_{doc['chat_id']}"
        active_users[user_key] = {
            "key": doc["key"],
            "expiry": doc["expiry"]
        }
    return active_users

def save_active_users(data):
    """Save active users to MongoDB"""
    # This function is kept for compatibility but not needed with MongoDB
    pass

def generate_licence_key():
    chars = string.ascii_uppercase + string.digits
    key = "DEEPXTRACE-" + "".join(random.choices(chars, k=8))
    return key

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_private_chat(chat_id, user_id):
    return chat_id == user_id

def check_licence(user_id, chat_id):
    if not is_private_chat(chat_id, user_id):
        return True
    
    user_key = f"{user_id}_{chat_id}"
    doc = active_users_col.find_one({"user_id": user_id, "chat_id": chat_id})
    
    if doc:
        expiry = datetime.fromisoformat(doc["expiry"])
        if datetime.now() < expiry:
            return True
        else:
            active_users_col.delete_one({"user_id": user_id, "chat_id": chat_id})
            return False
    
    return False

def activate_licence(user_id, chat_id, key):
    # Check if key exists
    key_doc = keys_col.find_one({"key": key})
    if not key_doc:
        return "invalid"
    
    # Check if key is already used
    used_key_doc = used_keys_col.find_one({"key": key})
    if used_key_doc:
        return "used"
    
    expiry = datetime.now() + timedelta(hours=5)
    
    # Mark key as used
    used_keys_col.insert_one({
        "key": key,
        "user_id": user_id,
        "chat_id": chat_id,
        "activated_at": datetime.now().isoformat(),
        "expiry": expiry.isoformat()
    })
    
    # Activate user
    active_users_col.insert_one({
        "user_id": user_id,
        "chat_id": chat_id,
        "key": key,
        "expiry": expiry.isoformat()
    })
    
    return "success"

def get_remaining_time(expiry_str):
    expiry = datetime.fromisoformat(expiry_str)
    remaining = expiry - datetime.now()
    
    if remaining.total_seconds() <= 0:
        return "Expired"
    
    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)
    
    return f"{hours}h {minutes}m left"

def block_key(key):
    # Remove from keys collection
    keys_col.delete_one({"key": key})
    
    # Remove from used keys
    used_keys_col.delete_one({"key": key})
    
    # Remove active users with this key
    active_users_col.delete_many({"key": key})

# ================= VERIFIED USERS (FORCE JOIN) =================

def mark_user_verified(user_id):
    """Mark user as verified in MongoDB"""
    verified_users_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "verified_at": datetime.now()}},
        upsert=True
    )

def is_user_verified(user_id):
    """Check if user is verified in MongoDB"""
    return verified_users_col.find_one({"user_id": user_id}) is not None

def unverify_user(user_id):
    """Remove user verification in MongoDB"""
    verified_users_col.delete_one({"user_id": user_id})

# ================= DISABLED COMMANDS =================

def load_disabled_commands():
    """Load disabled commands from MongoDB"""
    doc = disabled_commands_col.find_one({"key": "disabled_list"})
    if doc:
        return doc.get("commands", [])
    return []

def save_disabled_commands(disabled_list):
    """Save disabled commands to MongoDB"""
    disabled_commands_col.update_one(
        {"key": "disabled_list"},
        {"$set": {"commands": disabled_list}},
        upsert=True
    )

# ================= BROADCAST FUNCTION =================

def broadcast_message(message_text):
    """Broadcast message to all registered chats"""
    all_chats = get_all_chats()
    success_count = 0
    fail_count = 0
    
    for chat in all_chats:
        try:
            send_message(chat["chat_id"], message_text)
            success_count += 1
            time.sleep(0.05)  # Rate limiting
        except:
            fail_count += 1
    
    return success_count, fail_count

# ================= API HANDLERS =================

def send_message(chat_id, text, reply_to_message_id=None, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        r = requests.post(TG_API + "/sendMessage", json=payload)
        result = r.json()
        if result.get("ok"):
            return result["result"]["message_id"]
        return None
    except:
        return None

def delete_message(chat_id, message_id):
    try:
        requests.post(
            TG_API + "/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id}
        )
    except:
        pass

def send_txt_file_with_caption(chat_id, filename, content, reply_to_message_id=None):
    try:
        files = {"document": (filename, content.encode("utf-8"), "text/plain")}
        data = {"chat_id": chat_id}
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        
        r = requests.post(TG_API + "/sendDocument", data=data, files=files)
        result = r.json()
        if result.get("ok"):
            return result["result"]["message_id"]
        return None
    except:
        return None

def auto_delete_file(chat_id, file_message_id):
    time.sleep(60)
    delete_message(chat_id, file_message_id)

# ================= VALIDATORS =================

def is_mobile_number(text):
    return bool(re.fullmatch(r"[6-9]\d{9}", text))

def is_aadhaar_number(text):
    return bool(re.fullmatch(r"\d{12}", text))

def is_gst_number(text):
    return bool(re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}", text.upper()))

def is_ifsc_code(text):
    return bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", text.upper()))

def is_vehicle_number(text):
    return bool(re.fullmatch(r"[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}", text.upper()))

# ================= TEXT BUILDERS =================

def build_mobile_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "       🛰️ MOBILE NUMBER REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"📱 Number: {data.get('phone_number', 'N/A')}\n"
    txt += f"👤 Name: {data.get('name', 'N/A')}\n"
    txt += f"🎂 DOB: {data.get('dob', 'N/A')}\n"
    txt += f"⚧️ Gender: {data.get('gender', 'N/A')}\n"
    txt += f"📍 Location: {data.get('location', 'N/A')}\n"
    txt += f"📮 Pincode: {data.get('pincode', 'N/A')}\n"
    txt += f"🏢 Operator: {data.get('operator', 'N/A')}\n"
    txt += f"🌐 Circle: {data.get('circle', 'N/A')}\n"
    txt += f"📧 Email: {data.get('email', 'N/A')}\n"
    txt += f"📧 Alt Email: {data.get('alt_email', 'N/A')}\n"
    txt += f"🏠 Address: {data.get('address', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n"
    txt += f"📱 Alt Number: {data.get('alt_number', 'N/A')}\n"
    txt += f"🆔 UID: {data.get('uid', 'N/A')}\n"
    txt += f"👨‍👩‍👧 Father: {data.get('father_name', 'N/A')}\n"
    txt += f"👩 Mother: {data.get('mother_name', 'N/A')}\n"
    txt += f"💍 Spouse: {data.get('spouse_name', 'N/A')}\n"
    txt += f"🏦 Bank: {data.get('bank_name', 'N/A')}\n"
    txt += f"💳 Account: {data.get('account_number', 'N/A')}\n"
    txt += f"🔢 IFSC: {data.get('ifsc_code', 'N/A')}\n"
    txt += f"🏛️ Branch: {data.get('branch', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_aadhaar_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "          🪪 AADHAAR REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"🆔 Aadhaar: {data.get('aadhaar_number', 'N/A')}\n"
    txt += f"👤 Name: {data.get('name', 'N/A')}\n"
    txt += f"🎂 DOB: {data.get('dob', 'N/A')}\n"
    txt += f"⚧️ Gender: {data.get('gender', 'N/A')}\n"
    txt += f"📧 Email: {data.get('email', 'N/A')}\n"
    txt += f"📱 Mobile: {data.get('mobile', 'N/A')}\n"
    txt += f"🏠 Address: {data.get('address', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n"
    txt += f"📮 Pincode: {data.get('pincode', 'N/A')}\n"
    txt += f"👨‍👩‍👧 Father: {data.get('father_name', 'N/A')}\n"
    txt += f"💍 Spouse: {data.get('spouse_name', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_gst_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "           🏛️ GST REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"🔢 GSTIN: {data.get('gstin', 'N/A')}\n"
    txt += f"🏢 Legal Name: {data.get('legal_name', 'N/A')}\n"
    txt += f"🏷️ Trade Name: {data.get('trade_name', 'N/A')}\n"
    txt += f"📅 Registration Date: {data.get('registration_date', 'N/A')}\n"
    txt += f"📊 Status: {data.get('status', 'N/A')}\n"
    txt += f"🏗️ Type: {data.get('taxpayer_type', 'N/A')}\n"
    txt += f"🏠 Address: {data.get('address', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n"
    txt += f"📮 Pincode: {data.get('pincode', 'N/A')}\n"
    txt += f"📧 Email: {data.get('email', 'N/A')}\n"
    txt += f"📱 Mobile: {data.get('mobile', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_ifsc_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "          🏦 IFSC REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"🔢 IFSC: {data.get('ifsc', 'N/A')}\n"
    txt += f"🏦 Bank: {data.get('bank', 'N/A')}\n"
    txt += f"🏛️ Branch: {data.get('branch', 'N/A')}\n"
    txt += f"🏠 Address: {data.get('address', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n"
    txt += f"📱 Contact: {data.get('contact', 'N/A')}\n"
    txt += f"💱 MICR: {data.get('micr', 'N/A')}\n"
    txt += f"💳 UPI: {data.get('upi', 'N/A')}\n"
    txt += f"💸 RTGS: {data.get('rtgs', 'N/A')}\n"
    txt += f"💰 NEFT: {data.get('neft', 'N/A')}\n"
    txt += f"💵 IMPS: {data.get('imps', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_upi_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "           💸 UPI REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"💳 UPI ID: {data.get('upi_id', 'N/A')}\n"
    txt += f"👤 Name: {data.get('name', 'N/A')}\n"
    txt += f"🏦 Bank: {data.get('bank', 'N/A')}\n"
    txt += f"📱 Mobile: {data.get('mobile', 'N/A')}\n"
    txt += f"📧 Email: {data.get('email', 'N/A')}\n"
    txt += f"📍 Location: {data.get('location', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_vehicle_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "          🚗 VEHICLE REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"🚙 Reg No: {data.get('registration_number', 'N/A')}\n"
    txt += f"📅 Reg Date: {data.get('registration_date', 'N/A')}\n"
    txt += f"👤 Owner: {data.get('owner_name', 'N/A')}\n"
    txt += f"🏢 Company: {data.get('maker', 'N/A')}\n"
    txt += f"🚗 Model: {data.get('vehicle_model', 'N/A')}\n"
    txt += f"⛽ Fuel: {data.get('fuel_type', 'N/A')}\n"
    txt += f"🎨 Color: {data.get('vehicle_color', 'N/A')}\n"
    txt += f"🔧 Class: {data.get('vehicle_class', 'N/A')}\n"
    txt += f"🔢 Chassis: {data.get('chassis_number', 'N/A')}\n"
    txt += f"⚙️ Engine: {data.get('engine_number', 'N/A')}\n"
    txt += f"🏛️ RTO: {data.get('rto', 'N/A')}\n"
    txt += f"🛡️ Insurance: {data.get('insurance_company', 'N/A')}\n"
    txt += f"📅 Ins Upto: {data.get('insurance_upto', 'N/A')}\n"
    txt += f"✅ Fitness: {data.get('fitness_upto', 'N/A')}\n"
    txt += f"💺 Seats: {data.get('no_of_seats', 'N/A')}\n"
    txt += f"🔊 Cubic Cap: {data.get('cubic_capacity', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_vnum_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "      🚗 VEHICLE NUMBER REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"🚙 Reg No: {data.get('reg_no', 'N/A')}\n"
    txt += f"📅 Reg Date: {data.get('regn_dt', 'N/A')}\n"
    txt += f"👤 Owner: {data.get('owner_name', 'N/A')}\n"
    txt += f"🏢 Maker: {data.get('maker', 'N/A')}\n"
    txt += f"🚗 Model: {data.get('vehicle_model', 'N/A')}\n"
    txt += f"⛽ Fuel: {data.get('fuel_type', 'N/A')}\n"
    txt += f"🎨 Color: {data.get('vehicle_color', 'N/A')}\n"
    txt += f"🔧 Class: {data.get('vh_class', 'N/A')}\n"
    txt += f"🔢 Chassis: {data.get('chasi_no', 'N/A')}\n"
    txt += f"⚙️ Engine: {data.get('engine_no', 'N/A')}\n"
    txt += f"🏛️ RTO: {data.get('rto', 'N/A')}\n"
    txt += f"🛡️ Insurance: {data.get('insurance_comp', 'N/A')}\n"
    txt += f"📅 Ins Upto: {data.get('ins_upto', 'N/A')}\n"
    txt += f"✅ Fitness: {data.get('fitness_upto', 'N/A')}\n"
    txt += f"💺 Seats: {data.get('no_of_seats', 'N/A')}\n"
    txt += f"🔊 Cubic Cap: {data.get('cubic_cap', 'N/A')}\n"
    txt += f"📱 Mobile: {data.get('mobile_no', 'N/A')}\n"
    txt += f"💰 Resale Value: {data.get('resale_value', 'N/A')}\n"
    txt += f"📊 Status: {data.get('status', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_tg_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "       📱 TELEGRAM OSINT REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"👤 Username: {data.get('username', 'N/A')}\n"
    txt += f"🆔 User ID: {data.get('user_id', 'N/A')}\n"
    txt += f"📛 Name: {data.get('name', 'N/A')}\n"
    txt += f"📝 Bio: {data.get('bio', 'N/A')}\n"
    txt += f"📱 Phone: {data.get('phone', 'N/A')}\n"
    txt += f"🖼️ Profile Pic: {data.get('profile_pic', 'N/A')}\n"
    txt += f"📅 Created: {data.get('created_date', 'N/A')}\n"
    txt += f"🌐 Language: {data.get('language', 'N/A')}\n"
    txt += f"🤖 Bot: {data.get('is_bot', 'N/A')}\n"
    txt += f"✅ Verified: {data.get('is_verified', 'N/A')}\n"
    txt += f"🔒 Premium: {data.get('is_premium', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_trace_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "        🔍 TRACE REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"📱 Mobile: {data.get('mobile', 'N/A')}\n"
    txt += f"👤 Name: {data.get('name', 'N/A')}\n"
    txt += f"📧 Email: {data.get('email', 'N/A')}\n"
    txt += f"🏠 Address: {data.get('address', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n"
    txt += f"📮 Pincode: {data.get('pincode', 'N/A')}\n"
    txt += f"🌐 Operator: {data.get('operator', 'N/A')}\n"
    txt += f"📍 Circle: {data.get('circle', 'N/A')}\n"
    txt += f"💼 Occupation: {data.get('occupation', 'N/A')}\n"
    txt += f"🎓 Education: {data.get('education', 'N/A')}\n"
    txt += f"🎂 DOB: {data.get('dob', 'N/A')}\n"
    txt += f"⚧️ Gender: {data.get('gender', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

def build_gmail_txt(data):
    txt = "╔══════════════════════════════╗\n"
    txt += "         📧 GMAIL REPORT\n"
    txt += "╚══════════════════════════════╝\n\n"
    txt += f"📧 Email: {data.get('email', 'N/A')}\n"
    txt += f"👤 Name: {data.get('name', 'N/A')}\n"
    txt += f"📱 Mobile: {data.get('mobile', 'N/A')}\n"
    txt += f"🎂 DOB: {data.get('dob', 'N/A')}\n"
    txt += f"⚧️ Gender: {data.get('gender', 'N/A')}\n"
    txt += f"🏠 Address: {data.get('address', 'N/A')}\n"
    txt += f"🏙️ City: {data.get('city', 'N/A')}\n"
    txt += f"🗺️ State: {data.get('state', 'N/A')}\n"
    txt += f"📮 Pincode: {data.get('pincode', 'N/A')}\n"
    txt += f"📍 Location: {data.get('location', 'N/A')}\n"
    txt += f"🔗 Social: {data.get('social_media', 'N/A')}\n\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "      🔐 DeepTraceXBot\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return txt

# ================= GET FORCE JOIN POPUP =================

def get_force_join_popup(chat_type):
    """Return force join popup only for groups/channels, not private"""
    if chat_type == "private":
        return None
    
    force_channel = get_force_join_channel()
    return {
        "inline_keyboard": [[
            {
                "text": "📢 Join Channel",
                "url": f"https://t.me/{force_channel.replace('@', '')}"
            }
        ]]
    }

def check_user_in_channel(user_id):
    """Check if user is in force join channel"""
    force_channel = get_force_join_channel()
    try:
        member = requests.get(
            TG_API + "/getChatMember",
            params={
                "chat_id": force_channel,
                "user_id": user_id
            }
        ).json()
        
        status = member.get("result", {}).get("status")
        return status in ["member", "administrator", "creator"]
    except:
        return False

# ================= MESSAGE PROCESSING =================

def process_message(chat_id, text, user_id, reply_to):
    lower = text.lower().strip()
    
    # Register chat in MongoDB
    try:
        chat_info = requests.get(TG_API + "/getChat", params={"chat_id": chat_id}).json()
        chat_type = chat_info.get("result", {}).get("type", "private")
        register_chat(chat_id, chat_type)
    except:
        chat_type = "private" if chat_id == user_id else "group"
    
    # Check member count requirement for groups/channels
    if not check_member_count_requirement(chat_id, chat_type):
        send_message(
            chat_id,
            "For using this bot in your group or channel, minimum 30 members required.",
            reply_to_message_id=reply_to
        )
        return
    
    # Check if user has left channel (only for group/channel)
    if chat_type != "private":
        if is_user_verified(user_id):
            if not check_user_in_channel(user_id):
                unverify_user(user_id)

    # Admin Commands
    if is_admin(user_id):
        # /link command
        if lower.startswith("/link "):
            channel_link = text.split(maxsplit=1)[1].strip()
            set_force_join_channel(channel_link)
            send_message(
                chat_id,
                f"✅ Force join channel updated to: {channel_link}",
                reply_to_message_id=reply_to
            )
            return
        
        # /broadcast command
        if lower.startswith("/broadcast "):
            broadcast_text = text.split(maxsplit=1)[1].strip()
            send_message(
                chat_id,
                "🔄 Broadcasting message...",
                reply_to_message_id=reply_to
            )
            success, fail = broadcast_message(broadcast_text)
            send_message(
                chat_id,
                f"✅ Broadcast complete!\n\n📊 Success: {success}\n❌ Failed: {fail}",
                reply_to_message_id=reply_to
            )
            return
        
        # /genkey
        if lower == "/genkey":
            key = generate_licence_key()
            save_key(key)
            send_message(
                chat_id,
                f"🔑 New Key Generated:\n\n`{key}`\n\n✅ Valid for 5 hours after activation",
                reply_to_message_id=reply_to
            )
            return
        
        # /blockkey
        if lower.startswith("/blockkey "):
            key = text.split(maxsplit=1)[1].strip()
            block_key(key)
            send_message(
                chat_id,
                f"🔒 Key Blocked:\n`{key}`",
                reply_to_message_id=reply_to
            )
            return
        
        # /enable
        if lower.startswith("/enable "):
            cmd = text.split(maxsplit=1)[1].strip().lower()
            disabled = load_disabled_commands()
            if cmd in disabled:
                disabled.remove(cmd)
                save_disabled_commands(disabled)
                send_message(
                    chat_id,
                    f"✅ Command /{cmd} enabled",
                    reply_to_message_id=reply_to
                )
            else:
                send_message(
                    chat_id,
                    f"⚠️ Command /{cmd} is already enabled",
                    reply_to_message_id=reply_to
                )
            return
        
        # /disable
        if lower.startswith("/disable "):
            cmd = text.split(maxsplit=1)[1].strip().lower()
            disabled = load_disabled_commands()
            if cmd not in disabled:
                disabled.append(cmd)
                save_disabled_commands(disabled)
                send_message(
                    chat_id,
                    f"🚫 Command /{cmd} disabled",
                    reply_to_message_id=reply_to
                )
            else:
                send_message(
                    chat_id,
                    f"⚠️ Command /{cmd} is already disabled",
                    reply_to_message_id=reply_to
                )
            return
        
        # /admincmd
        if lower == "/admincmd":
            admin_help = (
                "🔧 ADMIN COMMANDS\n\n"
                "🔑 /genkey - Generate new licence key\n"
                "🔒 /blockkey <key> - Block a key\n"
                "✅ /enable <cmd> - Enable command\n"
                "🚫 /disable <cmd> - Disable command\n"
                "📢 /link <channel_link> - Set force join channel\n"
                "📣 /broadcast <message> - Broadcast to all users\n"
                "📊 /stats - Bot statistics"
            )
            send_message(chat_id, admin_help, reply_to_message_id=reply_to)
            return

    # Check disabled commands
    disabled_cmds = load_disabled_commands()
    
    # /start
    if lower == "/start":
        if not is_private_chat(chat_id, user_id):
            popup = get_force_join_popup(chat_type)
            send_message(chat_id, get_welcome_message(), reply_to_message_id=reply_to, reply_markup=popup)
            return
        
        if not is_user_verified(user_id):
            force_channel = get_force_join_channel()
            markup = {
                "inline_keyboard": [
                    [{"text": "📢 Join Channel", "url": f"https://t.me/{force_channel.replace('@', '')}"}],
                    [{"text": "✅ Join Confirmation", "callback_data": "join_confirm"}]
                ]
            }
            send_message(
                chat_id,
                f"⚠️ Access Denied!\n\n"
                f"🔐 You must join our channel first:\n{force_channel}\n\n"
                f"👉 Click 'Join Channel' → Join → Click 'Join Confirmation'",
                reply_markup=markup
            )
            return
        
        if not check_licence(user_id, chat_id):
            send_message(
                chat_id,
                "⚠️ No Active Licence!\n\n"
                "🔑 Use: /redeem YOUR_KEY\n"
                "💬 Or contact admin via /admin",
                reply_to_message_id=reply_to
            )
            return
        
        send_message(chat_id, get_welcome_message(), reply_to_message_id=reply_to)
        return
    
    # /redeem (Private only)
    if lower.startswith("/redeem "):
        if not is_private_chat(chat_id, user_id):
            return
        
        if not is_user_verified(user_id):
            force_channel = get_force_join_channel()
            markup = {
                "inline_keyboard": [
                    [{"text": "📢 Join Channel", "url": f"https://t.me/{force_channel.replace('@', '')}"}],
                    [{"text": "✅ Join Confirmation", "callback_data": "join_confirm"}]
                ]
            }
            send_message(
                chat_id,
                f"⚠️ Access Denied!\n\n"
                f"🔐 You must join our channel first:\n{force_channel}\n\n"
                f"👉 Click 'Join Channel' → Join → Click 'Join Confirmation'",
                reply_markup=markup
            )
            return
        
        key = text.split(maxsplit=1)[1].strip()
        result = activate_licence(user_id, chat_id, key)
        
        if result == "success":
            send_message(
                chat_id,
                "✅ Licence Activated!\n\n"
                "⏰ Valid for 5 hours\n"
                "📌 Use /status to check remaining time",
                reply_to_message_id=reply_to
            )
        elif result == "invalid":
            send_message(
                chat_id,
                "❌ Invalid Key!\n\n"
                "💬 Contact admin via /admin for valid key",
                reply_to_message_id=reply_to
            )
        elif result == "used":
            send_message(
                chat_id,
                "❌ Key Already Used!\n\n"
                "💬 Contact admin via /admin for new key",
                reply_to_message_id=reply_to
            )
        return
    
    # /status (Private only)
    if lower == "/status":
        if not is_private_chat(chat_id, user_id):
            return
        
        doc = active_users_col.find_one({"user_id": user_id, "chat_id": chat_id})
        
        if doc:
            remaining = get_remaining_time(doc["expiry"])
            send_message(
                chat_id,
                f"📊 Licence Status\n\n"
                f"🔑 Key: {doc['key']}\n"
                f"⏰ Time Left: {remaining}",
                reply_to_message_id=reply_to
            )
        else:
            send_message(
                chat_id,
                "❌ No Active Licence!\n\n"
                "🔑 Use: /redeem YOUR_KEY",
                reply_to_message_id=reply_to
            )
        return
    
    # Check licence for private chat
    if is_private_chat(chat_id, user_id):
        if not is_user_verified(user_id):
            force_channel = get_force_join_channel()
            markup = {
                "inline_keyboard": [
                    [{"text": "📢 Join Channel", "url": f"https://t.me/{force_channel.replace('@', '')}"}],
                    [{"text": "✅ Join Confirmation", "callback_data": "join_confirm"}]
                ]
            }
            send_message(
                chat_id,
                f"⚠️ Access Denied!\n\n"
                f"🔐 You must join our channel first:\n{force_channel}\n\n"
                f"👉 Click 'Join Channel' → Join → Click 'Join Confirmation'",
                reply_markup=markup
            )
            return
        
        if not check_licence(user_id, chat_id):
            send_message(
                chat_id,
                "⚠️ No Active Licence!\n\n"
                "🔑 Use: /redeem YOUR_KEY\n"
                "💬 Or contact admin via /admin",
                reply_to_message_id=reply_to
            )
            return

    # /admin message forwarding
    if lower.startswith("/admin "):
        msg_text = text.split(maxsplit=1)[1] if len(text.split(maxsplit=1)) > 1 else ""
        if msg_text:
            for admin_id in ADMIN_IDS:
                send_message(
                    admin_id,
                    f"📩 Message from User {user_id}:\n\n{msg_text}"
                )
            send_message(
                chat_id,
                "✅ Message sent to admin!",
                reply_to_message_id=reply_to
            )
        else:
            send_message(
                chat_id,
                "❌ Please provide a message\n💡 Example: /admin I need help",
                reply_to_message_id=reply_to
            )
        return

    # Extract clean text
    clean_text = text.split(maxsplit=1)[1].strip() if len(text.split()) > 1 else ""

    # ---------- /num ----------
    if lower.startswith("/num "):
        if "num" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide mobile number\n💡 Example: /num 9876543210",
                reply_to_message_id=reply_to
            )
            return

        if not is_mobile_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid mobile number!\n\n"
                "💡 Example: /num 9876543210\n"
                "📌 Format: 10 digits, starts with 6-9",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Tracking number… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                MOBILE_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Mobile_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_mobile_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /num failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /aadhaar ----------
    if lower.startswith("/aadhaar "):
        if "aadhaar" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Aadhaar number\n💡 Example: /aadhaar 123456789012",
                reply_to_message_id=reply_to
            )
            return

        if not is_aadhaar_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid Aadhaar number!\n\n"
                "💡 Example: /aadhaar 123456789012\n"
                "📌 Format: 12 digits",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching Aadhaar data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                AADHAAR_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Aadhaar_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_aadhaar_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /aadhaar failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /gst ----------
    if lower.startswith("/gst "):
        if "gst" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide GST number\n💡 Example: /gst 24ABCDE1234F1Z5",
                reply_to_message_id=reply_to
            )
            return

        if not is_gst_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid GST number!\n\n"
                "💡 Example: /gst 24ABCDE1234F1Z5\n"
                "📌 Format: 15 characters",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching GST data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                GST_API + clean_text.upper(),
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"GST_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_gst_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /gst failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /ifsc ----------
    if lower.startswith("/ifsc "):
        if "ifsc" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide IFSC code\n💡 Example: /ifsc SBIN0000000",
                reply_to_message_id=reply_to
            )
            return

        if not is_ifsc_code(clean_text):
            send_message(
                chat_id,
                "❌ Invalid IFSC code!\n\n"
                "💡 Example: /ifsc SBIN0000000\n"
                "📌 Format: 11 characters",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching IFSC data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                IFSC_API + clean_text.upper(),
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"IFSC_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_ifsc_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /ifsc failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /upi ----------
    if lower.startswith("/upi "):
        if "upi" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide UPI ID\n💡 Example: /upi username@bank",
                reply_to_message_id=reply_to
            )
            return

        if "@" not in clean_text:
            send_message(
                chat_id,
                "❌ Invalid UPI ID!\n\n"
                "💡 Example: /upi username@bank",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching UPI data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                UPI_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"UPI_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_upi_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /upi failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /fam ----------
    if lower.startswith("/fam "):
        if "fam" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide FAM UPI ID\n💡 Example: /fam username@fam",
                reply_to_message_id=reply_to
            )
            return

        if "@" not in clean_text:
            send_message(
                chat_id,
                "❌ Invalid FAM UPI ID!\n\n"
                "💡 Example: /fam username@fam",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching FAM data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                FAM_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"FAM_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_upi_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /fam failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /vehicle ----------
    if lower.startswith("/vehicle "):
        if "vehicle" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide vehicle number\n💡 Example: /vehicle GJ01AB1234",
                reply_to_message_id=reply_to
            )
            return

        if not is_vehicle_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid vehicle number!\n\n"
                "💡 Example: /vehicle GJ01AB1234",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching vehicle data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                VEHICLE_API + clean_text.upper(),
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Vehicle_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_vehicle_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /vehicle failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /vnum ----------
    if lower.startswith("/vnum "):
        if "vnum" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide vehicle number\n💡 Example: /vnum GJ03HD0255",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Fetching vehicle data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                VNUM_API + clean_text.upper(),
                headers=HEADERS,
                timeout=30
            ).json()

            if not res.get("rc_data", {}).get("status"):
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            data_list = res.get("rc_data", {}).get("data", [])
            if not data_list:
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = data_list[0]

            fid = send_txt_file_with_caption(
                chat_id,
                f"Vnum_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_vnum_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /vnum failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return

    # ---------- /tg ----------
    if lower.startswith("/tg "):
        if "tg" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Telegram username\n💡 Example: /tg @username",
                reply_to_message_id=reply_to
            )
            return

        username = clean_text.replace("@", "")

        loading = send_message(
            chat_id,
            "🛰️ Fetching Telegram data… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                OSINT_API + username,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"TG_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_tg_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /tg failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return


# ---------- /trace ----------
    if lower.startswith("/trace "):
        if "trace" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide mobile number\n💡 Example: /trace 9876543210",
                reply_to_message_id=reply_to
            )
            return

        if not is_mobile_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid mobile number!\n\n"
                "💡 Example: /trace 9876543210\n"
                "📌 Format: 10 digits, starts with 6-9",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Tracing number… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                TRACE_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Trace_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_trace_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /trace failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return
 
    # ---------- /gmail ----------
    if lower.startswith("/gmail "):
        if "gmail" in disabled_cmds:
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide email address\n💡 Example: /gmail test@gmail.com",
                reply_to_message_id=reply_to
            )
            return

        if "@" not in clean_text or "." not in clean_text:
            send_message(
                chat_id,
                "❌ Invalid email format!\n\n"
                "💡 Example: /gmail test@gmail.com",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "Fetching email data…⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                GMAIL_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "📂❌ Private account — no data available.",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Gmail_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_gmail_txt(d),
                reply_to_message_id=reply_to
            )

            delete_message(chat_id, loading)

            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /gmail failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )

        return


# ================= START =================
def main():
    init_licence_files()
    print("🤖 Bot is running...")
    
    # ✅ CORRECT Telethon start
        
    offset = 0

    while True:
        try:
            upd = requests.get(
                TG_API + "/getUpdates",
                params={"timeout": 30, "offset": offset}
            ).json()

            for u in upd.get("result", []):
                offset = u["update_id"] + 1

                # ===== CALLBACK QUERY HANDLING =====
                if "callback_query" in u:
                    q = u["callback_query"]
                    data = q.get("data")
                    chat_id = q["message"]["chat"]["id"]
                    user_id = q["from"]["id"]
                    callback_id = q["id"]
                    message_id = q["message"]["message_id"]

                    print(f"\n{'='*40}")
                    print("🔔 CALLBACK QUERY")
                    print(f"User ID: {user_id}")
                    print(f"Chat ID: {chat_id}")
                    print(f"Data: {data}")
                    print(f"{'='*40}\n")

                    if data == "join_confirm":
                        try:
                            force_channel = get_force_join_channel()
                            member = requests.get(
                                TG_API + "/getChatMember",
                                params={
                                    "chat_id": force_channel,
                                    "user_id": user_id
                                }
                            ).json()

                            status = member.get("result", {}).get("status")
                            print(f"Channel Status: {status}")

                            # ✅ USER JOINED → SUCCESS POPUP
                            if status in ["member", "administrator", "creator"]:
                                mark_user_verified(user_id)

                                requests.post(
                                    TG_API + "/answerCallbackQuery",
                                    json={
                                        "callback_query_id": callback_id,
                                        "text": "✅ Verification Successful!\n\nYou can now use the bot.",
                                        "show_alert": True
                                    }
                                )

                                delete_message(chat_id, message_id)
                                send_message(chat_id, get_welcome_message())

                            # ❌ USER NOT JOINED → FAIL POPUP
                            else:
                                requests.post(
                                    TG_API + "/answerCallbackQuery",
                                    json={
                                        "callback_query_id": callback_id,
                                        "text": "❌ Please join the channel first!\n\nThen click Join Confirmation again.",
                                        "show_alert": True
                                    }
                                )

                        except Exception as e:
                            print(f"❌ Callback Error: {e}")
                            requests.post(
                                TG_API + "/answerCallbackQuery",
                                json={
                                    "callback_query_id": callback_id,
                                    "text": "❌ Verification failed. Please try again.",
                                    "show_alert": True
                                }
                            )

                    continue  # 👈 callback handle ho gaya, next update pe jao

                # ===== NORMAL MESSAGE HANDLING =====
                if "message" in u and "text" in u["message"]:
                    msg = u["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg["text"]
                    message_id = msg["message_id"]

                    if "from" in msg:
                        user_id = msg["from"]["id"]
                        process_message(chat_id, text, user_id, message_id)
                    else:
                        print("⚠️ Message without 'from' field - skipping")
                        continue

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
