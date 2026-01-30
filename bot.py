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
from bson import ObjectId

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
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not set in environment variables!")
    print("Please set BOT_TOKEN in Render Environment Variables")
    exit(1)

if not MONGODB_URI:
    print("Error: MONGODB_URI not set in environment variables!")
    print("Please set MONGODB_URI in Render Environment Variables")
    exit(1)

# ================= MONGODB CONNECTION =================
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client['deeptracex_bot']
    
    # Collections
    active_users_col = db['active_users']
    verified_users_col = db['verified_users']
    licence_keys_col = db['licence_keys']
    used_keys_col = db['used_keys']
    disabled_commands_col = db['disabled_commands']
    stats_col = db['stats']
    redeem_codes_col = db['redeem_codes']
    authorized_chats_col = db['authorized_chats']
    settings_col = db['settings']
    
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

MOBILE_API = "https://api.b77bf911.workers.dev/mobile?number="
AADHAAR_API = "https://api.b77bf911.workers.dev/aadhaar?id="
GST_API = "https://api.b77bf911.workers.dev/gst?number="
IFSC_API = "https://api.b77bf911.workers.dev/ifsc?code="
UPI_API = "https://api.b77bf911.workers.dev/upi?id="
FAM_API = "https://api.b77bf911.workers.dev/upi2?id="
VEHICLE_API = "https://api.b77bf911.workers.dev/vehicle?registration="
OSINT_API = "https://api.b77bf911.workers.dev/telegram?user="
TRACE_API = "https://king.mr-unknown.workers.dev/Pera?track="
GMAIL_API = "https://king.mr-unknown.workers.dev/Pera?mail="
VNUM_API = "https://api.paanel.shop/numapi.php?action=api&key=num_wanted&test1="

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

# ================= MONGODB HELPER FUNCTIONS =================

def get_force_join_channel():
    """Get force join channel link from MongoDB"""
    setting = settings_col.find_one({"key": "force_join_channel"})
    if setting:
        return setting["value"]
    # Default fallback
    default_channel = "@DeepXTraceOfficial"
    settings_col.update_one(
        {"key": "force_join_channel"},
        {"$set": {"value": default_channel}},
        upsert=True
    )
    return default_channel

def update_force_join_channel(channel_link):
    """Update force join channel link"""
    settings_col.update_one(
        {"key": "force_join_channel"},
        {"$set": {"value": channel_link, "updated_at": datetime.now()}},
        upsert=True
    )

def load_disabled_commands():
    """Load disabled commands from MongoDB"""
    doc = disabled_commands_col.find_one({"type": "disabled_list"})
    if doc and "commands" in doc:
        return doc["commands"]
    return []

def save_disabled_commands(commands):
    """Save disabled commands to MongoDB"""
    disabled_commands_col.update_one(
        {"type": "disabled_list"},
        {"$set": {"commands": commands, "updated_at": datetime.now()}},
        upsert=True
    )

def load_verified_users():
    """Load verified users from MongoDB"""
    users = {}
    for doc in verified_users_col.find():
        users[str(doc["user_id"])] = {
            "verified_at": doc["verified_at"].isoformat() if isinstance(doc["verified_at"], datetime) else doc["verified_at"]
        }
    return users

def mark_user_verified(user_id):
    """Mark user as verified in MongoDB"""
    verified_users_col.update_one(
        {"user_id": user_id},
        {"$set": {"verified_at": datetime.now()}},
        upsert=True
    )

def is_user_verified(user_id):
    """Check if user is verified"""
    return verified_users_col.find_one({"user_id": user_id}) is not None

def load_keys():
    """Load licence keys from MongoDB"""
    keys = []
    for doc in licence_keys_col.find({"active": True}):
        keys.append(doc["key"])
    return keys

def save_key(key):
    """Save licence key to MongoDB"""
    licence_keys_col.insert_one({
        "key": key,
        "active": True,
        "created_at": datetime.now()
    })

def load_used_keys():
    """Load used keys from MongoDB"""
    used = {}
    for doc in used_keys_col.find():
        used[doc["key"]] = {
            "user_id": doc["user_id"],
            "chat_id": doc["chat_id"],
            "activated_at": doc["activated_at"].isoformat() if isinstance(doc["activated_at"], datetime) else doc["activated_at"],
            "expiry": doc["expiry"].isoformat() if isinstance(doc["expiry"], datetime) else doc["expiry"]
        }
    return used

def save_used_keys_entry(key, user_id, chat_id, expiry):
    """Save used key entry to MongoDB"""
    used_keys_col.insert_one({
        "key": key,
        "user_id": user_id,
        "chat_id": chat_id,
        "activated_at": datetime.now(),
        "expiry": expiry
    })

def load_active_users():
    """Load active users from MongoDB"""
    active = {}
    for doc in active_users_col.find():
        user_key = f"{doc['user_id']}_{doc['chat_id']}"
        active[user_key] = {
            "key": doc["key"],
            "expiry": doc["expiry"].isoformat() if isinstance(doc["expiry"], datetime) else doc["expiry"]
        }
    return active

def save_active_user_entry(user_id, chat_id, key, expiry):
    """Save active user entry to MongoDB"""
    active_users_col.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$set": {"key": key, "expiry": expiry}},
        upsert=True
    )

def remove_active_user(user_id, chat_id):
    """Remove active user from MongoDB"""
    active_users_col.delete_one({"user_id": user_id, "chat_id": chat_id})

def generate_licence_key():
    chars = string.ascii_uppercase + string.digits
    key = "DEEPXTRACE-" + "".join(random.choices(chars, k=8))
    return key

def generate_redeem_code():
    """Generate redeem code for group/channel authorization"""
    chars = string.ascii_uppercase + string.digits
    code = "REDEEM-" + "".join(random.choices(chars, k=10))
    return code

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_private_chat(chat_id, user_id):
    return chat_id == user_id

def is_chat_authorized(chat_id):
    """Check if group/channel is authorized"""
    if chat_id > 0:
        return True
    
    auth = authorized_chats_col.find_one({"chat_id": chat_id})
    if not auth:
        return False
    
    # Check if expired
    if auth.get("expires_at"):
        expiry = auth["expires_at"] if isinstance(auth["expires_at"], datetime) else datetime.fromisoformat(auth["expires_at"])
        if datetime.now() > expiry:
            return False
    
    return auth.get("verified", False)

def show_authorization_required(chat_id):
    """Show authorization required message for groups/channels"""
    msg = (
        "🔒 Authorization Required\n\n"
        "This group/channel is not authorized to use DeepTraceXBot.\n\n"
        "Please contact admin to get your Redeem Code.\n\n"
        "👤 Admin: @imvrct\n\n"
        "Then verify using:\n"
        "/code YOUR_REDEEM_CODE"
    )
    send_message(chat_id, msg)

def check_licence(user_id, chat_id):
    if not is_private_chat(chat_id, user_id):
        return True
    
    active_users = load_active_users()
    user_key = f"{user_id}_{chat_id}"
    
    if user_key in active_users:
        expiry = datetime.fromisoformat(active_users[user_key]["expiry"])
        if datetime.now() < expiry:
            return True
        else:
            remove_active_user(user_id, chat_id)
            return False
    
    return False

def activate_licence(user_id, chat_id, key):
    keys = load_keys()
    used_keys = load_used_keys()
    
    if key not in keys:
        return "invalid"
    
    if key in used_keys:
        return "used"
    
    expiry = datetime.now() + timedelta(hours=5)
    
    save_used_keys_entry(key, user_id, chat_id, expiry)
    save_active_user_entry(user_id, chat_id, key, expiry)
    
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
    licence_keys_col.update_one(
        {"key": key},
        {"$set": {"active": False}}
    )
    
    used_keys_col.delete_many({"key": key})
    active_users_col.delete_many({"key": key})

# ================= TELEGRAM FUNCTIONS =================
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
    
    resp = requests.post(TG_API + "/sendMessage", json=payload).json()
    if resp.get("ok"):
        return resp["result"]["message_id"]
    return None

def delete_message(chat_id, message_id):
    try:
        requests.post(TG_API + "/deleteMessage", json={
            "chat_id": chat_id,
            "message_id": message_id
        })
    except:
        pass

def send_txt_file(chat_id, filename, content, reply_to=None):
    files = {"document": (filename, content.encode("utf-8"))}
    data = {"chat_id": chat_id}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    
    resp = requests.post(TG_API + "/sendDocument", data=data, files=files).json()
    if resp.get("ok"):
        return resp["result"]["message_id"]
    return None

def send_txt_file_with_caption(chat_id, filename, content, caption="", reply_to_message_id=None):
    files = {"document": (filename, content.encode("utf-8"))}
    data = {"chat_id": chat_id, "caption": caption}
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id
    
    resp = requests.post(TG_API + "/sendDocument", data=data, files=files).json()
    if resp.get("ok"):
        return resp["result"]["message_id"]
    return None

def auto_delete_file(chat_id, message_id, delay=60):
    time.sleep(delay)
    delete_message(chat_id, message_id)

# ================= VALIDATORS =================
def is_mobile_number(text):
    return bool(re.match(r"^[6-9]\d{9}$", text))

def is_aadhaar(text):
    return bool(re.match(r"^\d{12}$", text))

def is_gst(text):
    return bool(re.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]{2}$", text.upper()))

def is_ifsc(text):
    return bool(re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", text.upper()))

def is_vehicle_number(text):
    return bool(re.match(r"^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$", text.upper()))

# ================= BUILDERS =================
def build_mobile_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   📱 MOBILE NUMBER REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📞 Mobile       : {d.get('mobile', 'N/A')}",
        f"👤 Name         : {d.get('name', 'N/A')}",
        f"🏠 Address      : {d.get('address', 'N/A')}",
        f"📬 Pincode      : {d.get('pincode', 'N/A')}",
        f"📧 Email        : {d.get('email', 'N/A')}",
        f"🔗 Social       : {d.get('social', 'N/A')}",
        f"🎂 DOB          : {d.get('dob', 'N/A')}",
        f"⚧  Gender       : {d.get('gender', 'N/A')}",
        f"👨‍👩‍👧 Father       : {d.get('father', 'N/A')}",
        f"📱 Alternate    : {d.get('alternate', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_aadhaar_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   🆔 AADHAAR CARD REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"🆔 Aadhaar      : {d.get('aadhaar', 'N/A')}",
        f"👤 Name         : {d.get('name', 'N/A')}",
        f"🎂 DOB          : {d.get('dob', 'N/A')}",
        f"⚧  Gender       : {d.get('gender', 'N/A')}",
        f"🏠 Address      : {d.get('address', 'N/A')}",
        f"📬 Pincode      : {d.get('pincode', 'N/A')}",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        f"📧 Email        : {d.get('email', 'N/A')}",
        f"👨‍👩‍👧 Father       : {d.get('father', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_gst_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   📋 GST REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"🔢 GSTIN        : {d.get('gstin', 'N/A')}",
        f"🏢 Legal Name   : {d.get('legal_name', 'N/A')}",
        f"🏪 Trade Name   : {d.get('trade_name', 'N/A')}",
        f"📅 Reg Date     : {d.get('registration_date', 'N/A')}",
        f"📊 Status       : {d.get('status', 'N/A')}",
        f"🏠 Address      : {d.get('address', 'N/A')}",
        f"📬 Pincode      : {d.get('pincode', 'N/A')}",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        f"📧 Email        : {d.get('email', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_ifsc_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   🏦 IFSC CODE REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"🔢 IFSC         : {d.get('ifsc', 'N/A')}",
        f"🏦 Bank         : {d.get('bank', 'N/A')}",
        f"🏢 Branch       : {d.get('branch', 'N/A')}",
        f"📍 City         : {d.get('city', 'N/A')}",
        f"🗺️  State        : {d.get('state', 'N/A')}",
        f"🏠 Address      : {d.get('address', 'N/A')}",
        f"📞 Contact      : {d.get('contact', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_upi_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   💳 UPI ID REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"💳 UPI ID       : {d.get('upi', 'N/A')}",
        f"👤 Name         : {d.get('name', 'N/A')}",
        f"🏦 Bank         : {d.get('bank', 'N/A')}",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_fam_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   💰 FAM PAY REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"💰 FAM ID       : {d.get('fam', 'N/A')}",
        f"👤 Name         : {d.get('name', 'N/A')}",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        f"📧 Email        : {d.get('email', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_vehicle_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   🚗 VEHICLE REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"🚗 Registration : {d.get('registration', 'N/A')}",
        f"👤 Owner        : {d.get('owner', 'N/A')}",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        f"🏢 Maker        : {d.get('maker', 'N/A')}",
        f"📋 Model        : {d.get('model', 'N/A')}",
        f"⛽ Fuel         : {d.get('fuel', 'N/A')}",
        f"🎨 Color        : {d.get('color', 'N/A')}",
        f"📅 Reg Date     : {d.get('reg_date', 'N/A')}",
        f"🏠 Address      : {d.get('address', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_vnum_txt(d):
    """Build TXT for /vnum command based on API response"""
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   🚗 VEHICLE NUMBER REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"Registration No : {d.get('reg_no', 'N/A')}",
        f"Owner Name      : {d.get('owner_name', 'N/A')}",
        f"Father Name     : {d.get('father_name', 'N/A')}",
        f"Mobile No       : {d.get('mobile_no', 'N/A')}",
        f"RTO             : {d.get('rto', 'N/A')}",
        f"Vehicle Model   : {d.get('vehicle_model', 'N/A')}",
        f"Maker           : {d.get('maker', 'N/A')}",
        f"Fuel Type       : {d.get('fuel_type', 'N/A')}",
        f"Vehicle Color   : {d.get('vehicle_color', 'N/A')}",
        f"Chassis No      : {d.get('chasi_no', 'N/A')}",
        f"Engine No       : {d.get('engine_no', 'N/A')}",
        f"Registration Dt : {d.get('regn_dt', 'N/A')}",
        f"Insurance Comp  : {d.get('insurance_comp', 'N/A')}",
        f"Insurance Upto  : {d.get('ins_upto', 'N/A')}",
        f"Fitness Upto    : {d.get('fitness_upto', 'N/A')}",
        f"No of Seats     : {d.get('no_of_seats', 'N/A')}",
        f"Body Type       : {d.get('body_type_desc', 'N/A')}",
        f"Resale Value    : {d.get('resale_value', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_tg_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   🔍 TELEGRAM OSINT REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"👤 Username     : {d.get('username', 'N/A')}",
        f"🆔 User ID      : {d.get('user_id', 'N/A')}",
        f"📛 Name         : {d.get('name', 'N/A')}",
        f"📝 Bio          : {d.get('bio', 'N/A')}",
        f"📱 Phone        : {d.get('phone', 'N/A')}",
        f"🌐 Status       : {d.get('status', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_trace_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   🛰️ TRACE REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        f"👤 Name         : {d.get('name', 'N/A')}",
        f"🏠 Address      : {d.get('address', 'N/A')}",
        f"📬 Pincode      : {d.get('pincode', 'N/A')}",
        f"📧 Email        : {d.get('email', 'N/A')}",
        f"🔗 Social       : {d.get('social', 'N/A')}",
        f"🎂 DOB          : {d.get('dob', 'N/A')}",
        f"⚧  Gender       : {d.get('gender', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def build_gmail_txt(d):
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "   📧 GMAIL REPORT",
        "━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"📧 Email        : {d.get('email', 'N/A')}",
        f"👤 Name         : {d.get('name', 'N/A')}",
        f"📱 Mobile       : {d.get('mobile', 'N/A')}",
        f"🔗 Social       : {d.get('social', 'N/A')}",
        f"🏠 Location     : {d.get('location', 'N/A')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🔍 Powered by DeepTraceXBot",
        "━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

# ================= MESSAGE HANDLER =================
def process_message(chat_id, text, user_id, reply_to):
    lower = text.lower()
    clean_text = text.split(maxsplit=1)[1].strip() if len(text.split()) > 1 else ""

    # ===== CHECK GROUP/CHANNEL AUTHORIZATION =====
    if chat_id < 0:
        if not is_chat_authorized(chat_id):
            if not lower.startswith("/code "):
                show_authorization_required(chat_id)
                return

    # ===== CHECK FORCE JOIN FOR GROUPS/CHANNELS (CONTINUOUSLY) =====
    if chat_id < 0:
        if not is_user_verified(user_id):
            FORCE_JOIN_CHANNEL = get_force_join_channel()
            
            try:
                member = requests.get(
                    TG_API + "/getChatMember",
                    params={
                        "chat_id": FORCE_JOIN_CHANNEL,
                        "user_id": user_id
                    }
                ).json()
                
                status = member.get("result", {}).get("status")
                
                if status not in ["member", "administrator", "creator"]:
                    keyboard = {
                        "inline_keyboard": [[
                            {"text": "📢 Join Channel", "url": f"https://t.me/{FORCE_JOIN_CHANNEL.replace('@', '')}"},
                            {"text": "✅ Join Confirmation", "callback_data": "join_confirm"}
                        ]]
                    }
                    
                    send_message(
                        chat_id,
                        "🔒 Access Restricted\n\n"
                        "To use this bot, please:\n"
                        "1️⃣ Join our official channel\n"
                        "2️⃣ Click 'Join Confirmation'\n\n"
                        "✨ After joining, all features will be unlocked!",
                        reply_markup=keyboard
                    )
                    return
                else:
                    mark_user_verified(user_id)
            except Exception as e:
                print(f"Error checking membership: {e}")

    # ===== /start =====
    if lower == "/start":
        if is_private_chat(chat_id, user_id):
            if not check_licence(user_id, chat_id):
                send_message(
                    chat_id,
                    "🔐 DeepTraceXBot - Premium Access Required\n\n"
                    "This bot requires a valid licence key.\n\n"
                    "🔑 To activate:\n"
                    "/redeem YOUR_LICENCE_KEY\n\n"
                    "📩 Contact admin for licence key:\n"
                    "@imvrct"
                )
                return
        
        if not is_user_verified(user_id):
            FORCE_JOIN_CHANNEL = get_force_join_channel()
            keyboard = {
                "inline_keyboard": [[
                    {"text": "📢 Join Channel", "url": f"https://t.me/{FORCE_JOIN_CHANNEL.replace('@', '')}"},
                    {"text": "✅ Join Confirmation", "callback_data": "join_confirm"}
                ]]
            }
            
            send_message(
                chat_id,
                "🔒 Access Restricted\n\n"
                "To use this bot, please:\n"
                "1️⃣ Join our official channel\n"
                "2️⃣ Click 'Join Confirmation'\n\n"
                "✨ After joining, all features will be unlocked!",
                reply_markup=keyboard
            )
            return
        
        send_message(chat_id, get_welcome_message())
        return

    # ===== /help =====
    if lower == "/help":
        send_message(chat_id, get_welcome_message(), reply_to_message_id=reply_to)
        return

    # ===== ADMIN: /code (GENERATE REDEEM CODE) =====
    if lower == "/code" and is_admin(user_id):
        code = generate_redeem_code()
        expires_at = datetime.now() + timedelta(days=10)
        
        redeem_codes_col.insert_one({
            "code": code,
            "generated_by": user_id,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "used": False,
            "chat_id": None
        })
        
        send_message(
            chat_id,
            f"✅ Redeem Code Generated\n\n"
            f"🔑 Code: `{code}`\n"
            f"⏰ Valid for: 10 days\n"
            f"📅 Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Share this code with group/channel admin.",
            reply_to_message_id=reply_to
        )
        return

    # ===== /code YOUR_REDEEM_CODE (GROUP/CHANNEL AUTHORIZATION) =====
    if lower.startswith("/code "):
        if chat_id > 0:
            send_message(
                chat_id,
                "❌ This command is only for groups/channels.",
                reply_to_message_id=reply_to
            )
            return
        
        code = clean_text.strip()
        
        redeem = redeem_codes_col.find_one({"code": code})
        
        if not redeem:
            send_message(
                chat_id,
                "❌ Invalid redeem code!\n\n"
                "Please contact admin for valid code.\n"
                "👤 Admin: @imvrct",
                reply_to_message_id=reply_to
            )
            return
        
        if redeem.get("used"):
            send_message(
                chat_id,
                "❌ This redeem code has already been used!",
                reply_to_message_id=reply_to
            )
            return
        
        expires_at = redeem["expires_at"] if isinstance(redeem["expires_at"], datetime) else datetime.fromisoformat(redeem["expires_at"])
        
        if datetime.now() > expires_at:
            send_message(
                chat_id,
                "❌ This redeem code has expired!",
                reply_to_message_id=reply_to
            )
            return
        
        # Mark code as used
        redeem_codes_col.update_one(
            {"code": code},
            {"$set": {"used": True, "chat_id": chat_id, "used_at": datetime.now()}}
        )
        
        # Authorize chat
        chat_expires_at = datetime.now() + timedelta(days=10)
        authorized_chats_col.update_one(
            {"chat_id": chat_id},
            {"$set": {
                "verified": True,
                "verified_at": datetime.now(),
                "expires_at": chat_expires_at,
                "redeem_code": code
            }},
            upsert=True
        )
        
        send_message(
            chat_id,
            "✅ Authorization Successful!\n\n"
            "This group/channel is now verified.\n"
            "Access granted for 10 days.\n\n"
            "Thank you for using DeepTraceXBot 🚀",
            reply_to_message_id=reply_to
        )
        return

    # ===== ADMIN: /link (UPDATE FORCE JOIN CHANNEL) =====
    if lower.startswith("/link ") and is_admin(user_id):
        new_link = clean_text.strip()
        
        if not new_link.startswith("@"):
            send_message(
                chat_id,
                "❌ Invalid format!\n\n"
                "Usage: /link @channelname",
                reply_to_message_id=reply_to
            )
            return
        
        update_force_join_channel(new_link)
        
        send_message(
            chat_id,
            f"✅ Force join channel updated!\n\n"
            f"New channel: {new_link}",
            reply_to_message_id=reply_to
        )
        return

    # ===== ADMIN: /genkey =====
    if lower.startswith("/genkey") and is_admin(user_id):
        try:
            count = int(clean_text) if clean_text else 1
        except:
            count = 1
        
        keys = []
        for _ in range(count):
            key = generate_licence_key()
            save_key(key)
            keys.append(key)
        
        msg = "🔑 Licence Keys Generated:\n\n" + "\n".join([f"`{k}`" for k in keys])
        send_message(chat_id, msg, reply_to_message_id=reply_to)
        return

    # ===== ADMIN: /block =====
    if lower.startswith("/block ") and is_admin(user_id):
        key = clean_text
        block_key(key)
        send_message(
            chat_id,
            f"🚫 Key blocked: `{key}`",
            reply_to_message_id=reply_to
        )
        return

    # ===== ADMIN: /stats =====
    if lower == "/stats" and is_admin(user_id):
        total_keys = licence_keys_col.count_documents({"active": True})
        used_count = used_keys_col.count_documents({})
        active_count = active_users_col.count_documents({})
        
        msg = (
            "📊 Bot Statistics\n\n"
            f"🔑 Total Keys: {total_keys}\n"
            f"✅ Used Keys: {used_count}\n"
            f"👥 Active Users: {active_count}"
        )
        send_message(chat_id, msg, reply_to_message_id=reply_to)
        return

    # ===== ADMIN: /stop =====
    if lower.startswith("/stop ") and is_admin(user_id):
        cmd = clean_text.lower().replace("/", "")
        disabled = load_disabled_commands()
        
        if cmd not in disabled:
            disabled.append(cmd)
            save_disabled_commands(disabled)
            send_message(
                chat_id,
                f"🚫 Command /{cmd} has been disabled.",
                reply_to_message_id=reply_to
            )
        else:
            send_message(
                chat_id,
                f"⚠️ Command /{cmd} is already disabled.",
                reply_to_message_id=reply_to
            )
        return

    # ===== ADMIN: /resume =====
    if lower.startswith("/resume ") and is_admin(user_id):
        cmd = clean_text.lower().replace("/", "")
        disabled = load_disabled_commands()
        
        if cmd in disabled:
            disabled.remove(cmd)
            save_disabled_commands(disabled)
            send_message(
                chat_id,
                f"✅ Command /{cmd} has been enabled.",
                reply_to_message_id=reply_to
            )
        else:
            send_message(
                chat_id,
                f"⚠️ Command /{cmd} is not disabled.",
                reply_to_message_id=reply_to
            )
        return

    # ===== /redeem =====
    if lower.startswith("/redeem "):
        key = clean_text
        result = activate_licence(user_id, chat_id, key)
        
        if result == "invalid":
            send_message(
                chat_id,
                "❌ Invalid licence key!",
                reply_to_message_id=reply_to
            )
        elif result == "used":
            send_message(
                chat_id,
                "❌ This key has already been used!",
                reply_to_message_id=reply_to
            )
        elif result == "success":
            send_message(
                chat_id,
                "✅ Licence activated successfully!\n\n"
                "⏰ Valid for: 5 hours\n\n"
                "Use /mylicence to check remaining time.",
                reply_to_message_id=reply_to
            )
        return

    # ===== /mylicence =====
    if lower == "/mylicence":
        if not is_private_chat(chat_id, user_id):
            send_message(
                chat_id,
                "⚠️ This command only works in private chat.",
                reply_to_message_id=reply_to
            )
            return
        
        active_users = load_active_users()
        user_key = f"{user_id}_{chat_id}"
        
        if user_key in active_users:
            remaining = get_remaining_time(active_users[user_key]["expiry"])
            send_message(
                chat_id,
                f"✅ Your Licence Status\n\n"
                f"🔑 Key: {active_users[user_key]['key']}\n"
                f"⏰ Remaining: {remaining}",
                reply_to_message_id=reply_to
            )
        else:
            send_message(
                chat_id,
                "❌ No active licence found.\n\n"
                "Use /redeem YOUR_KEY to activate.",
                reply_to_message_id=reply_to
            )
        return

    # ===== CHECK DISABLED COMMANDS =====
    disabled = load_disabled_commands()
    cmd_name = lower.split()[0].replace("/", "")
    if cmd_name in disabled:
        return

    # ===== LICENCE CHECK FOR PRIVATE CHAT =====
    if is_private_chat(chat_id, user_id):
        if not check_licence(user_id, chat_id):
            send_message(
                chat_id,
                "🔐 Licence Expired or Not Found\n\n"
                "Please activate your licence:\n"
                "/redeem YOUR_KEY\n\n"
                "📩 Contact: @imvrct",
                reply_to_message_id=reply_to
            )
            return

    # ===== /admin =====
    if lower.startswith("/admin "):
        for admin_id in ADMIN_IDS:
            send_message(
                admin_id,
                f"📩 New Admin Message\n\n"
                f"👤 From: {user_id}\n"
                f"💬 Message:\n{clean_text}"
            )
        
        send_message(
            chat_id,
            "✅ Your message has been sent to admin.",
            reply_to_message_id=reply_to
        )
        return

    # ===== /num =====
    if lower.startswith("/num "):
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
            "🔍 Searching database…⏳",
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
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Mobile_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /aadhaar =====
    if lower.startswith("/aadhaar "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Aadhaar number\n💡 Example: /aadhaar 123456789012",
                reply_to_message_id=reply_to
            )
            return

        if not is_aadhaar(clean_text):
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
            "🔍 Searching database…⏳",
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
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Aadhaar_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /gst =====
    if lower.startswith("/gst "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide GST number\n💡 Example: /gst 24ABCDE1234F1Z5",
                reply_to_message_id=reply_to
            )
            return

        if not is_gst(clean_text):
            send_message(
                chat_id,
                "❌ Invalid GST number!\n\n"
                "💡 Example: /gst 24ABCDE1234F1Z5",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Searching database…⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                GST_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"GST_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /ifsc =====
    if lower.startswith("/ifsc "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide IFSC code\n💡 Example: /ifsc SBIN0000000",
                reply_to_message_id=reply_to
            )
            return

        if not is_ifsc(clean_text):
            send_message(
                chat_id,
                "❌ Invalid IFSC code!\n\n"
                "💡 Example: /ifsc SBIN0000000",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Searching database…⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                IFSC_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"IFSC_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /upi =====
    if lower.startswith("/upi "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide UPI ID\n💡 Example: /upi username@bank",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Searching database…⏳",
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
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"UPI_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /fam =====
    if lower.startswith("/fam "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide FAM ID\n💡 Example: /fam username@fam",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Searching database…⏳",
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
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"FamPay_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_fam_txt(d),
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /vehicle =====
    if lower.startswith("/vehicle "):
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
            "🔍 Searching database…⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                VEHICLE_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            if res.get("status") != "success":
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"Vehicle_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /vnum =====
    if lower.startswith("/vnum "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide vehicle number\n💡 Example: /vnum GJ03HD0255",
                reply_to_message_id=reply_to
            )
            return

        if not is_vehicle_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid vehicle number!\n\n"
                "💡 Example: /vnum GJ03HD0255",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Searching database…⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(
                VNUM_API + clean_text,
                headers=HEADERS,
                timeout=30
            ).json()

            rc_data = res.get("rc_data", {})
            
            if not rc_data.get("status") or not rc_data.get("data"):
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "⚠️ No record found",
                    reply_to_message_id=reply_to
                )
                return

            d = rc_data["data"][0]

            fid = send_txt_file_with_caption(
                chat_id,
                f"VNum_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
                "⚠️ No record found",
                reply_to_message_id=reply_to
            )

        return

    # ===== /tg =====
    if lower.startswith("/tg "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Telegram username\n💡 Example: /tg @username",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🛰️ Scanning Telegram…⏳",
            reply_to_message_id=reply_to
        )

        try:
            username = clean_text.replace("@", "")
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
                f"TG_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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

    # ===== /trace =====
    if lower.startswith("/trace "):
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
                f"Trace_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
 
    # ===== /gmail =====
    if lower.startswith("/gmail "):
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
                f"Gmail_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
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
    print("🤖 Bot is running...")
        
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
                            FORCE_JOIN_CHANNEL = get_force_join_channel()
                            
                            member = requests.get(
                                TG_API + "/getChatMember",
                                params={
                                    "chat_id": FORCE_JOIN_CHANNEL,
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

                    continue

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
