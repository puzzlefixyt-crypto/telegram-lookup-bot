from flask import Flask
import requests
import time
from datetime import datetime, timedelta
import os
import threading
import re
import random
import string
from mongo_db import (
    load_verified_users,
    save_verified_users,
    load_active_users,
    save_active_users,
    load_used_keys,
    save_used_keys,
    load_stats,
    save_stats,
    load_disabled_commands,
    save_disabled_commands
)

# ===== PUBLIC COMMAND HELP CONFIG =====
BOT_USERNAME = "@DeepTraceXBot"

PUBLIC_HELP_MAP = {
    "/num": "💡 Usage: /num 98XXXXXXXX",
    "/upi": "💡 Usage: /upi username@bank",
    "/fam": "💡 Usage: /fam username@fam",
    "/gst": "💡 Usage: /gst 24ABCDE1234F1Z5",
    "/vehicle": "💡 Usage: /vehicle GJ01AB1234",
    "/ifsc": "💡 Usage: /ifsc SBIN0000000",
    "/aadhaar": "💡 Usage: /aadhaar 12XXXXXXXXXX",
    "/trace": "💡 Usage: /trace 98XXXXXXXX",
    "/gmail": "💡 Usage: /gmail example@gmail.com"
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
FORCE_JOIN_CHANNEL = "@DeepXTraceOfficial"
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8208876135:AAFgboLqlMxiiNcD9Ejko5QEz3l1FlTgTzk"
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
OSINT_API = "https://api.b77bf911.workers.dev/telegram?user="
TRACE_API = "https://king.mr-unknown.workers.dev/Pera?track="
GMAIL_API = "https://king.mr-unknown.workers.dev/Pera?mail="
VNUM_API = "https://api.paanel.shop/numapi.php?action=api&key=num_wanted&test1="
IP_API = "https://abbas-apis.vercel.app/api/ip?ip="
FF_API = "https://abbas-apis.vercel.app/api/ff-info?uid="
TRUECALLER_API = "https://abbas-apis.vercel.app/api/num-name?number="


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json"
}
WELCOME_MESSAGE = (
    "🛰️ <b>DeepTraceXBot Intelligence</b>\n\n"
    "ᴍᴏʙɪʟᴇ: <code>/num</code> <code>98XXXXXX10</code>\n"
    "ᴛʀᴜᴇᴄᴀʟʟᴇʀ: <code>/truecaller</code> <code>98XXXXXXXX</code>\n"
    "ᴀᴀᴅʜᴀᴀʀ: <code>/aadhaar</code> <code>1234XXXX9012</code>\n"
    "ɢsᴛ: <code>/gst</code> <code>24ABCDE1234F1Z5</code>\n"
    "ɪғsᴄ: <code>/ifsc</code> <code>SBIN0000000</code>\n"
    "ᴜᴘɪ: <code>/upi</code> <code>username@bank</code>\n"
    "ғᴀᴍ: <code>/fam</code> <code>username@fam</code>\n"
    "ᴠᴇʜɪᴄʟᴇ: <code>/vehicle</code> <code>GJ01AB1234</code>\n"
    "ᴠɴᴜᴍ: <code>/vnum</code> <code>GJ01AB1234</code>\n"
    "ɪᴘ: <code>/ip</code> <code>8.8.8.8</code>\n"
    "ᴛʀᴀᴄᴇ: <code>/trace</code> <code>98XXXXXXXX</code>\n"
    "ɢᴍᴀɪʟ: <code>/gmail</code> <code>example@gmail.com</code>\n"
    "ғғ: <code>/ff</code> <code>2819649271</code>\n\n"
    "📩 Admin: <code>/admin</code> <code>your message</code>\n"
    "📄 Files auto-delete in 60s"
)
COMMAND_ORDER = [
    ("num", "ᴍᴏʙɪʟᴇ: /num 98XXXXXX10"),
    ("truecaller", "ᴛʀᴜᴇᴄᴀʟʟᴇʀ: /truecaller 98XXXXXXXX"),
    ("aadhaar", "ᴀᴀᴅʜᴀᴀʀ: /aadhaar 1234XXXX9012"),
    ("gst", "ɢsᴛ: /gst 24ABCDE1234F1Z5"),
    ("ifsc", "ɪғsᴄ: /ifsc SBIN0000000"),
    ("upi", "ᴜᴘɪ: /upi username@bank"),
    ("fam", "ғᴀᴍ: /fam username@fam"),
    ("vehicle", "ᴠᴇʜɪᴄʟᴇ: /vehicle GJ01AB1234"),
    ("vnum", "ᴠɴᴜᴍ: /vnum GJ01AB1234"),
    ("ip", "ɪᴘ: /ip 8.8.8.8"),
    ("trace", "ᴛʀᴀᴄᴇ: /trace 98XXXXXXXX"),
    ("ff", "ғғ: /ff 2819649271"),
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
    "/truecaller": "💡 Usage: /truecaller 98XXXXXXXX",
    "/upi": "💡 Usage: /upi username@bank",
    "/fam": "💡 Usage: /fam username@fam",
    "/gst": "💡 Usage: /gst 24ABCDE1234F1Z5",
    "/vehicle": "💡 Usage: /vehicle GJ01AB1234",
    "/ifsc": "💡 Usage: /ifsc SBIN0000000",
    "/aadhar": "💡 Usage: /aadhar 12XXXXXXXXXX",
    "/trace": "💡 Usage: /trace 98XXXXXXXX",
    "/gmail": "💡 Usage: /gmail example@gmail.com",
    "/vnum": "💡 Usage: /vnum GJ01AB1234",
    "/ip": "💡 Usage: /ip 8.8.8.8",
    "/ff": "💡 Usage: /ff 2819649271",


}

# ================= ADMIN CONFIG =================
ADMIN_IDS = [5221493804]

# ================= LICENCE FILES =================
KEYS_FILE = "keys.txt"

# -------- CREATE & SET EVENT LOOP (Python 3.13 FIX) --------

# -------- TELETHON CLIENT --------

# ================= LICENCE FUNCTIONS =================
def init_licence_files():
    if not os.path.exists(KEYS_FILE):
        open(KEYS_FILE, "w").close()

def load_keys():
    with open(KEYS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_key(key):
    with open(KEYS_FILE, "a") as f:
        f.write(key + "\n")

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
    
    active_users = load_active_users()
    user_key = f"{user_id}_{chat_id}"
    
    if user_key in active_users:
        expiry = datetime.fromisoformat(active_users[user_key]["expiry"])
        if datetime.now() < expiry:
            return True
        else:
            del active_users[user_key]
            save_active_users(active_users)
            return False
    
    return False

def activate_licence(user_id, chat_id, key):
    keys = load_keys()
    used_keys = load_used_keys()
    active_users = load_active_users()
    
    if key not in keys:
        return "invalid"
    
    if key in used_keys:
        return "used"
    
    user_key = f"{user_id}_{chat_id}"
    expiry = datetime.now() + timedelta(hours=5)
    
    used_keys[key] = {
        "user_id": user_id,
        "chat_id": chat_id,
        "activated_at": datetime.now().isoformat(),
        "expiry": expiry.isoformat()
    }
    
    active_users[user_key] = {
        "key": key,
        "expiry": expiry.isoformat()
    }
    
    save_used_keys(used_keys)
    save_active_users(active_users)
    
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
    keys = load_keys()
    used_keys = load_used_keys()
    active_users = load_active_users()
    
    if key in keys:
        keys.remove(key)
        with open(KEYS_FILE, "w") as f:
            for k in keys:
                f.write(k + "\n")
    
    if key in used_keys:
        del used_keys[key]
        save_used_keys(used_keys)
    
    to_remove = []
    for user_key, data in active_users.items():
        if data["key"] == key:
            to_remove.append(user_key)
    
    for user_key in to_remove:
        del active_users[user_key]
    
    save_active_users(active_users)

# ================= HELPERS =================
def format_ampm(dt_str):
    if not dt_str:
        return "Not Available"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        return dt_str

def parse_address(addr):
    if not addr:
        return "Not Available"
    parts = addr.replace("!!", "!").split("!")
    parts = [x.title() for x in parts if x.strip()]
    return ", ".join(parts)

def send_message(chat_id, text, reply_markup=None, reply_to_message_id=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id

    r = requests.post(
        TG_API + "/sendMessage",
        json=payload,
        timeout=20
    )
    try:
        return r.json()["result"]["message_id"]
    except Exception as e:
        print(f"[send_message ERROR] {r.text}")
        return None

def delete_message(chat_id, message_id):
    requests.post(
        TG_API + "/deleteMessage",
        json={"chat_id": chat_id, "message_id": message_id},
        timeout=20
    )

def send_txt_file_with_caption(chat_id, filename, content, reply_to_message_id=None):
    branding = "\n\n----------------------------\nDesigned & Powered by @imvrct"
    final_content = content.strip() + branding

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_content)

    caption = (
        "✅ File Generated Successfully\n"
        f"📂 {filename}\n"
        "⏳ File auto-delete in 60s\n"
        "⚡ Powered by @imvrct"
    )

    payload = {"chat_id": chat_id, "caption": caption}
    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id

    with open(filename, "rb") as f:
        r = requests.post(
            TG_API + "/sendDocument",
            files={"document": f},
            data=payload,
            timeout=30
        )

    os.remove(filename)
    return r.json()["result"]["message_id"]


def auto_delete_file(chat_id, file_msg_id, delay=60):
    time.sleep(delay)
    delete_message(chat_id, file_msg_id)

def is_command_disabled(cmd):
    return cmd.lower() in load_disabled_commands()

def is_user_verified(user_id):
    data = load_verified_users()
    return user_id in data

def mark_user_verified(user_id):
    data = load_verified_users()
    if user_id not in data:
        data.append(user_id)
    save_verified_users(data)

def send_join_message(chat_id, reply_to_message_id=None):
    keyboard = {
        "inline_keyboard": [
            
            [
                {
                    "text": "📢 Join Channel",
                    "url": "https://t.me/DeepXTraceOfficial"
                }
            ],
            [
                {
                    "text": "✅ Joined Confirmation",
                    "callback_data": "join_confirm"
                }
            ]
        ]
    }

    text = (
        "🔒 𝗔𝗰𝗰𝗲𝘀𝘀 𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱\n\n"
    "Join our official channel to continue.\n\n"
    "⏳ Verification auto-deletes in 60s"
    )

    msg_id = send_message(chat_id, text, reply_markup=keyboard, reply_to_message_id=reply_to_message_id)
    
    # Auto-delete after 60 seconds
    threading.Thread(
        target=lambda: (time.sleep(60), delete_message(chat_id, msg_id)),
        daemon=True
    ).start()

async def resolve_username(username):
    try:
        print(f"[DEBUG] Resolving username: {username}")
        entity = await tg_client.get_entity(username)
        return entity.id
    except Exception as e:
        print(f"[DEBUG] Resolve error: {e}")
        return None

def format_tg_output(d):
    return (
        "👤 <b>Telegram User Report</b>\n\n"

        "🆔 <b>User ID:</b> "
        f"<code>{d.get('id')}</code>\n"

        "👤 <b>Name:</b> "
        f"{d.get('first_name','')} {d.get('last_name','')}\n"

        "🤖 <b>Bot Account:</b> "
        f"{'Yes' if d.get('is_bot') else 'No'}\n"

        "🟢 <b>Status:</b> "
        f"{'Active' if d.get('is_active') else 'Inactive'}\n\n"

        "━━━━━━━━━━━━━━\n"
        "🕒 <b>Activity</b>\n"

        "📅 <b>First Message:</b> "
        f"{format_ampm(d.get('first_msg_date'))}\n"

        "⏱️ <b>Last Seen:</b> "
        f"{format_ampm(d.get('last_msg_date'))}\n\n"

        "━━━━━━━━━━━━━━\n"
        "💬 <b>Messages</b>\n"

        "✉️ <b>Total Messages:</b> "
        f"{d.get('total_msg_count')}\n"

        "👥 <b>Group Messages:</b> "
        f"{d.get('msg_in_groups_count')}\n"

        "🛡️ <b>Admin Rights:</b> "
        f"{'Yes' if d.get('adm_in_groups') else 'No'}\n\n"

        "━━━━━━━━━━━━━━\n"
        "👥 <b>Groups</b>\n"

        "📦 <b>Total Groups:</b> "
        f"{d.get('total_groups')}\n\n"

        "━━━━━━━━━━━━━━\n"
        "🏷️ <b>Identity</b>\n"

        "✏️ <b>Name Changes:</b> "
        f"{d.get('names_count')}\n"

        "🔗 <b>Username Changes:</b> "
        f"{d.get('usernames_count')}"
    )
    
def format_ff_output(d):
    return (
        "🔥 <b>FREE FIRE PLAYER REPORT</b> 🔥\n\n"
        
        "🆔 <b>UID:</b> "
        f"<code>{d.get('🆔 ID')}</code>\n\n"
        
        "👤 <b>Nickname:</b> "
        f"{d.get('👤 Nickname')}\n"
        
        "🌍 <b>Region:</b> "
        f"{d.get('🌎 Region')}\n"
        
        "🎖️ <b>Level:</b> "
        f"{d.get('🎖️ Level')}\n"
        
        "🏆 <b>Ranked Points:</b> "
        f"{d.get('🏆 Ranked Points')}\n"
        
        "👍 <b>Likes:</b> "
        f"{d.get('👍 Likes')}\n\n"
        
        "📅 <b>Account Created:</b>\n"
        f"{d.get('📅 Account Created')}\n\n"
        
        "📈 <b>Experience (XP):</b> "
        f"{d.get('📈 Experience (XP)')}\n"
        
        "📝 <b>Signature:</b>\n"
        f"{d.get('📝 Signature – Bio')}\n\n"
        
        "📢 <b>Influencer:</b> "
        f"{d.get('📢 Influencer')}\n"
        
        "🔄 <b>Profile Updated:</b>\n"
        f"{d.get('🔄 Profile Updated')}\n"
        
        "🕒 <b>Last Login:</b>\n"
        f"{d.get('🕒 Last Login')}\n\n"
        
        "💎 <b>Prime:</b> "
        f"{d.get('🥇 Prime')}\n\n"
        
        "━━━━━━━━━━━━━━━━━━\n"
        "⏳ <i>Message auto-delete in 60 seconds</i>\n"
        "⚡ <b>Powered By</b> <code>@imvrct</code>"
    )

# ================= TXT BUILDERS =================
def build_common_txt(d):
    address = parse_address(d.get("address"))
    return f"""
LOOKUP REPORT
-------------------

Name        : {d.get('name')}
Father Name : {d.get('father_name')}
Mobile      : {d.get('mobile')}
Alt Mobile  : {d.get('alt_mobile')}
Circle      : {d.get('circle')}
Address     : {address}
Id Number   : {d.get('id_number')}
Email       : {d.get('email') if d.get('email') else 'Not Available'}

Checked On  : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_gst_txt(d):
    addr = ", ".join(str(x) for x in [
        d.get("AddrBnm"), d.get("AddrBno"), d.get("AddrFlno"),
        d.get("AddrSt"), d.get("AddrLoc"), d.get("AddrPncd")
    ] if x)

    return f"""
GST LOOKUP REPORT
-------------------

GSTIN            : {d.get('Gstin')}
Trade Name       : {d.get('TradeName')}
Legal Name       : {d.get('LegalName')}
Address          : {addr}
State Code       : {d.get('StateCode')}
Taxpayer Type    : {d.get('TxpType')}
Status           : {d.get('Status')}
Block Status     : {d.get('BlkStatus')}
Registration Dt  : {d.get('DtReg')}
Deregistration Dt: {d.get('DtDReg') if d.get('DtDReg') else 'Not Available'}

Checked On       : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_ifsc_txt(d):
    return f"""
IFSC LOOKUP REPORT
-------------------

Bank Name    : {d.get('BANK')}
Bank Code    : {d.get('BANKCODE')}
IFSC Code    : {d.get('IFSC')}
Branch       : {d.get('BRANCH')}
Address      : {d.get('ADDRESS')}
City         : {d.get('CITY')}
District     : {d.get('DISTRICT')}
State        : {d.get('STATE')}
Contact      : {d.get('CONTACT')}
MICR         : {d.get('MICR')}
NEFT         : {d.get('NEFT')}
RTGS         : {d.get('RTGS')}
IMPS         : {d.get('IMPS')}
UPI          : {d.get('UPI')}
SWIFT        : {d.get('SWIFT') if d.get('SWIFT') else 'Not Available'}
ISO Code     : {d.get('ISO3166')}
Centre       : {d.get('CENTRE')}

Checked On   : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_upi_txt(d):
    return f"""
UPI LOOKUP REPORT
-------------------

Name                 : {d.get('name')}
VPA                  : {d.get('vpa')}
IFSC                 : {d.get('ifsc')}
Account Number       : {d.get('acc_no')}
Merchant             : {d.get('is_merchant')}
Merchant Verified    : {d.get('is_merchant_verified')}
Internal Merchant    : {d.get('is_internal_merchant')}
FamPay User          : {d.get('is_fampay_user')}
FamPay Username      : {d.get('fampay_username')}
FamPay First Name    : {d.get('fampay_first_name')}
FamPay Last Name     : {d.get('fampay_last_name')}

Checked On           : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_fam_txt(d):
    return f"""
FAM LOOKUP REPORT
-------------------

FAM ID      : {d.get('fam_id')}
Name        : {d.get('name')}
Phone       : {d.get('phone')}
Source      : {d.get('source')}
Status      : {d.get('status')}
Type        : {d.get('type')}

Checked On  : {datetime.now().strftime('%d-%m-%Y')}
"""

def build_vehicle_txt(reg, data):
    """Build vehicle report from single API response"""
    return f"""
VEHICLE LOOKUP REPORT
---------------------

Registration Number : {reg}
Owner Name         : {data.get('owner_name', 'Not Available')}
Make / Model       : {data.get('make_model', 'Not Available')}
Fuel Type          : {data.get('fuel_type', 'Not Available')}
Vehicle Type       : {data.get('vehicle_type', 'Not Available')}
Registration Date  : {data.get('registration_date', 'Not Available')}
Registration Place : {data.get('registration_address', 'Not Available')}
Engine Number      : {data.get('engine_number', 'Not Available')}
Chassis Number     : {data.get('chassis_number', 'Not Available')}
Commercial Vehicle : {data.get('is_commercial', 'Not Available')}
Previous Insurer   : {data.get('previous_insurer', 'Not Available')}
Policy Expiry Date : {data.get('previous_policy_expiry_date', 'Not Available')}
Permanent Address  : {data.get('permanent_address', 'Not Available')}
Present Address    : {data.get('present_address', 'Not Available')}

Checked On         : {datetime.now().strftime('%d-%m-%Y')}
"""
def build_vnum_txt(d):
    return f"""VEHICLE LOOKUP REPORT
----------------------------

Registration Number : {d.get('reg_no')}
Owner Name         : {d.get('owner_name')}
Father Name        : {d.get('father_name')}
Mobile Number      : {d.get('mobile_no')}
Vehicle Model      : {d.get('vehicle_model')}
Maker              : {d.get('maker')}
Fuel Type          : {d.get('fuel_type')}
Vehicle Class      : {d.get('vh_class')}
Vehicle Category   : {d.get('vehicle_category')}
Color              : {d.get('vehicle_color')}
Engine Number      : {d.get('engine_no')}
Chassis Number     : {d.get('chasi_no')}
Registration Date  : {d.get('regn_dt')}
RTO                : {d.get('rto')}
Insurance Company  : {d.get('insurance_comp')}
Insurance Upto     : {d.get('ins_upto')}
Fitness Upto       : {d.get('fitness_upto')}
No of Seats        : {d.get('no_of_seats')}
Cubic Capacity     : {d.get('cubic_cap')}
Resale Value       : {d.get('resale_value')}

Checked On         : {datetime.now().strftime('%d-%m-%Y')}
"""
def build_trace_txt(d):
    return f"""
TRACE LOOKUP REPORT
-------------------

Number             : {d.get('Number')}
Country            : {d.get('Country')}
Connection         : {d.get('Connection')}
Language           : {d.get('Language')}
SIM Card           : {d.get('SIM Card')}
Complaints         : {d.get('Complaints')}

Owner Name         : {d.get('Owner Name')}
Owner Personality  : {d.get('Owner Personality')}

Mobile Locations   : {d.get('Mobile Locations')}
Tower Locations    : {d.get('Tower Locations')}

Tracker ID         : {d.get('Tracker ID')}
Tracking History   : {d.get('Tracking History')}

Checked On         : {datetime.now().strftime('%d-%m-%Y')}
"""
def build_gmail_txt(d):
    breaches = d.get("Breaches", [])
    breaches_text = ", ".join(breaches) if breaches else "None"

    mx = d.get("MX_Records", [])
    mx_text = ", ".join(mx) if mx else "Not Available"

    return f"""
GMAIL LOOKUP REPORT
-------------------

Email              : {d.get('Email')}
Domain             : {d.get('Domain')}
IP Address         : {d.get('IP')}
Registrar          : {d.get('Registrar')}

Total Breaches     : {d.get('Total_Breaches')}
Breaches List      : {breaches_text}

MX Records         : {mx_text}

Checked On         : {datetime.now().strftime('%d-%m-%Y')}
"""
def build_ip_txt(d):
    return f"""
IP LOOKUP REPORT
-------------------

IP Address     : {d.get('IP')}
ISP            : {d.get('ISP')}
Organization   : {d.get('ORG')}
ASN            : {d.get('ASN')}
Domain         : {d.get('Domain')}

Country        : {d.get('Country')} ({d.get('Country_Code')})
Region         : {d.get('Region')}
City           : {d.get('City')}
Postal Code    : {d.get('Postal')}
Continent      : {d.get('Continent')}

Latitude       : {d.get('Latitude')}
Longitude      : {d.get('Longitude')}
Location       : {d.get('Location')}

Timezone       : {d.get('Timezone')}
UTC Offset     : {d.get('Timezone_Offset')}

Type           : {d.get('Type')}

Checked On     : {datetime.now().strftime('%d-%m-%Y')}
"""
# ================= VALIDATION FUNCTIONS =================
def is_mobile_number(text):
    """Check if text is a valid mobile number"""
    if not text.isdigit() or len(text) != 10:
        return False
    if text[0] not in '6789':
        return False
    return True

def is_aadhaar_number(text):
    """Check if text is a valid Aadhaar number"""
    if not text.isdigit() or len(text) != 12:
        return False
    if text[0] in '01':
        return False
    return True

def is_gstin(text):
    """Check if text is a valid GSTIN"""
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'
    return bool(re.match(pattern, text))

def is_ifsc_code(text):
    """Check if text is a valid IFSC code"""
    if len(text) != 11:
        return False
    if not text[:4].isalpha():
        return False
    if text[4] != '0':
        return False
    return True

def is_upi_id(text):
    """Check if text is a valid UPI ID"""
    return '@' in text and not text.endswith('@fam')

def is_fam_id(text):
    """Check if text is a valid FAM ID"""
    return '@' in text and text.endswith('@fam')

def is_vehicle_number(text):
    """Check if text is a valid vehicle number"""
    pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'
    return bool(re.match(pattern, text))

# ================= BOT LOGIC =================
def process_message(chat_id, text, user_id, message_id):
    # Sirf Telegram service messages ko block karo
    SYSTEM_BOT_IDS = [777000]  # Telegram official notifications only
    
    if user_id in SYSTEM_BOT_IDS:
        print(f"⚠️ Blocked Telegram service message: {user_id}")
        return
    raw = text.strip()
    if raw.startswith("/"):
        cmd_name = raw.split()[0].replace("/", "").lower()
        if is_command_disabled(cmd_name):
            return
    lower = raw.lower()
    # ===== DEBUG LOGGING =====
    print(f"\n{'='*50}")
    print(f"📨 NEW MESSAGE")
    print(f"{'='*50}")
    print(f"User ID: {user_id}")
    print(f"Chat ID: {chat_id}")
    print(f"Message: {raw}")
    print(f"Is Group: {chat_id != user_id}")
    print(f"Is Verified: {is_user_verified(user_id)}")
    
    # Verification file check
    verified_data = load_verified_users()
    print(f"Verified Users in File: {verified_data}")
    print(f"User {user_id} in File: {str(user_id) in verified_data}")
    print(f"{'='*50}\n")

    # ===== STATS TRACKING =====
    stats = load_stats()
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        chat_type = u["message"]["chat"]["type"]
    except:
        chat_type = "private"

    # Private chat
    if chat_type == "private":
        stats["private_users"].setdefault(str(user_id), today)

    # Group / Supergroup
    elif chat_type in ["group", "supergroup"]:
        stats["groups"].setdefault(str(chat_id), today)

    # Channel
    elif chat_type == "channel":
        stats["channels"].setdefault(str(chat_id), today)

    save_stats(stats)
    # ===== END STATS =====
    # ===== END DEBUG =====

    # Determine if reply is needed
    reply_to = None if (chat_id == user_id or lower == "/start") else message_id

    # ===== JOIN VERIFICATION (GROUP ONLY) =====
    if chat_id != user_id:  # Sirf group mein
        if user_id != 1087968824 and not is_user_verified(user_id):
            # Check if command or meaningful input
            if (raw.startswith("/") and not lower.startswith("/admin")) or (len(raw) > 5 and not raw.isspace()):
                send_join_message(chat_id, reply_to_message_id=reply_to)
                return
    # ===== END JOIN CHECK =====
    
    # ---------- Public empty commands (/cmd@bot) ----------
    for cmd, help_text in PUBLIC_HELP_MAP.items():
        if lower == f"{cmd}{BOT_USERNAME}":

            # ❌ Not verified → force join
            if not is_user_verified(user_id):
                send_join_message(
                    chat_id,
                    reply_to_message_id=reply_to
                )
                return

            # ✅ Verified → show short help
            send_message(
                chat_id,
                help_text,
                reply_to_message_id=reply_to
            )
            return
    
    # Extract clean text from command
    clean_text = raw
    if raw.startswith('/'):
        parts = raw.split(' ', 1)
        if len(parts) > 1:
            clean_text = parts[1].strip()
        else:
            clean_text = ""
   
    # ========== ADMIN COMMANDS ==========
    if lower == "/genkey":
        if not is_admin(user_id):
            return
        key = generate_licence_key()
        save_key(key)
        send_message(
            chat_id,
            f"🔑 New Licence Key Generated\n\n<code>{key}</code>\n\nTap the key to copy",
            reply_to_message_id=reply_to
        )
        return

    if lower == "/showkeys":
        if not is_admin(user_id):
            return
        
        keys = load_keys()
        used_keys = load_used_keys()
        active_users = load_active_users()
        
        available = []
        active = []
        expired = []
        
        for key in keys[:30]:
            if key in used_keys:
                expiry_str = used_keys[key]["expiry"]
                remaining = get_remaining_time(expiry_str)
                if remaining == "Expired":
                    expired.append(f"<code>{key}</code> → Expired")
                else:
                    active.append(f"<code>{key}</code> → {remaining}")
            else:
                available.append(f"<code>{key}</code> → Not Activated")
        
        msg = "📊 Licence Keys Status\n\n"
        
        if available:
            msg += "🟢 Available:\n" + "\n".join(available) + "\n\n"
        
        if active:
            msg += "🟡 Active:\n" + "\n".join(active) + "\n\n"
        
        if expired:
            msg += "🔴 Expired:\n" + "\n".join(expired)
        
        if not available and not active and not expired:
            msg += "No keys found"
        
        send_message(chat_id, msg, reply_to_message_id=reply_to)
        return

    if lower == "/activeusers":
        if not is_admin(user_id):
            return
        
        active_users = load_active_users()
        
        if not active_users:
            send_message(chat_id, "No active users", reply_to_message_id=reply_to)
            return
        
        msg = "👥 Active Users\n\n"
        
        for user_key, data in active_users.items():
            uid = user_key.split("_")[0]
            remaining = get_remaining_time(data["expiry"])
            msg += f"User ID: {uid}\nTime Left: {remaining}\n\n"
        
        send_message(chat_id, msg, reply_to_message_id=reply_to)
        return


    if lower.startswith("/blockkey "):
        if not is_admin(user_id):
            return
        
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide key\n💡 Example: /blockkey DTX-XXXX",
                reply_to_message_id=reply_to
            )
            return
        
        block_key(clean_text)
        send_message(
            chat_id,
            f"✅ Key blocked: {clean_text}",
            reply_to_message_id=reply_to
        )
        return


    if lower.startswith("/stop "):
        if not is_admin(user_id):
            return

        target = clean_text.lower()
        disabled = load_disabled_commands()

        if target not in disabled:
            disabled.append(target)
            save_disabled_commands(disabled)

        send_message(
            chat_id,
            f"✅ /{target} command stopped successfully",
            reply_to_message_id=reply_to
        )
        return


    if lower.startswith("/resume "):
        if not is_admin(user_id):
            return

        target = clean_text.lower()
        disabled = load_disabled_commands()

        if target in disabled:
            disabled.remove(target)
            save_disabled_commands(disabled)

        send_message(
            chat_id,
            f"✅ /{target} command resumed successfully",
            reply_to_message_id=reply_to
        )
        return
        

    # ---------- /admincmd ----------
    if lower == "/admincmd":
        if not is_admin(user_id):
            return

        send_message(
            chat_id,
            "👑 Admin Licence Commands\n\n"
            "/genkey\n→ Generate new copyable licence key\n\n"
            "/showkeys\n→ View licence keys & remaining time\n\n"
            "/activeusers\n→ View active users\n\n"
            "/user\n→ View total & today user statistics\n\n"
            "/blockkey DTX-XXXX\n→ Block a licence key\n\n"
            "/stop command_name\n→ Disable any user command\n\n"
            "/resume command_name\n→ Enable command again",
            reply_to_message_id=reply_to
        )
        return

    # ---------- /user ----------
    if lower == "/user":
        if not is_admin(user_id):
            return

        stats = load_stats()
        today = datetime.now().strftime("%Y-%m-%d")

        # Total counts
        total_private = len(stats.get("private_users", {}))
        total_groups = len(stats.get("groups", {}))
        total_channels = len(stats.get("channels", {}))
        total_verified = len(load_verified_users())

        # Today counts
        today_private = sum(
            1 for d in stats.get("private_users", {}).values() if d == today
        )
        today_groups = sum(
            1 for d in stats.get("groups", {}).values() if d == today
        )
        today_channels = sum(
            1 for d in stats.get("channels", {}).values() if d == today
        )
        today_verified = sum(
            1 for d in stats.get("verified_today", {}).values() if d == today
        )

        send_message(
            chat_id,
            "📊 <b>Bot User Statistics</b>\n\n"
            f"👤 Total Private Users   : {total_private}\n"
            f"👥 Total Active Groups   : {total_groups}\n"
            f"📢 Total Active Channels : {total_channels}\n\n"
            f"✅ Total Join Verified   : {total_verified}\n\n"
            "──────── <b>Today Data</b> ────────\n"
            f"👤 New Private Users   : {today_private}\n"
            f"👥 New Groups Added    : {today_groups}\n"
            f"📢 New Channels Added  : {today_channels}\n"
            f"✅ New Join Verified   : {today_verified}\n\n"
            "🛡️ Access Level : Admin",
            reply_to_message_id=reply_to
        )
        return

    # ---------- /admin (Send message to Admin) ----------
    if lower.startswith("/admin"):
        msg = clean_text

        if not msg:
            send_message(
                chat_id,
                "❌ Please write your message\n\n"
                "💡 Example:\n"
                "/admin I need help",
                reply_to_message_id=reply_to
            )
            return

        chat_type = "Private Chat"
        chat_name = ""

        if chat_id != user_id:
            chat_type = "Group Chat"
            chat_name = str(chat_id)

        admin_text = (
            "📩 New Message to Admin\n\n"
            f"👤 User ID: {user_id}\n"
            f"💬 Chat Type: {chat_type}\n"
            f"🏷 Chat Name: {chat_name}\n\n"
            "📝 Message:\n"
            f"{msg}"
        )

        for admin_id in ADMIN_IDS:
            send_message(admin_id, admin_text)

        send_message(chat_id, "✅ Your message has been sent to the Admin", reply_to_message_id=reply_to)
        return

    # ---------- /reply ----------
    if lower.startswith("/reply "):
        if not is_admin(user_id):
            return

        parts = clean_text.split(" ", 1)
        if len(parts) < 2:
            send_message(
                chat_id,
                "❌ Use format:\n/reply USER_ID message",
                reply_to_message_id=reply_to
            )
            return

        try:
            target_user_id = int(parts[0])
        except:
            send_message(chat_id, "❌ Invalid User ID", reply_to_message_id=reply_to)
            return

        reply_text = parts[1]

        send_message(
            target_user_id,
            "📩 Message from Admin\n\n" + reply_text
        )

        send_message(chat_id, "✅ Reply sent to user", reply_to_message_id=reply_to)
        return

    # ========== LICENCE CHECK FOR PRIVATE CHAT ==========
    if is_private_chat(chat_id, user_id):
        if lower.startswith("/key "):
            if not clean_text:
                send_message(chat_id, "❌ Please provide licence key\n💡 Example: /key DTX-ABC123XYZ456")
                return
    
                     
            result = activate_licence(user_id, chat_id, clean_text)
            
            if result == "invalid":
                send_message(chat_id, "❌ Invalid licence key")
                return
            elif result == "used":
                send_message(chat_id, "❌ This key has already been used")
                return
            elif result == "success":
                send_message(
                    chat_id,
                    "✅ Login Successful 🎉\n\n"
"Licence Activated\n\n"
"🕒 Valid for: 5 Hours\n"
"📱 Single Device\n\n"
"⚡ Access Enabled\n\n"
"👉 Click /start to Start Using 🚀✨"
                )
                return
        
        if not check_licence(user_id, chat_id):
            send_message(
                chat_id,
                "🔐 Personal Access Required\n\n"
                "Enter your licence key\n"
                "Example:\n"
                "/key DTX-ABC123XYZ456\n\n"
                "📩 Contact Admin 👉 @imvrct"
            )
            return

    # ---------- /start ----------
    if lower == "/start":
        send_message(chat_id, get_welcome_message())
        return

    # ---------- Direct info without command ----------
    if not raw.startswith('/'):
        if is_mobile_number(raw):
            send_message(
                chat_id,
                f"📱 Looks like you entered a mobile number!\n\n"
                f"💡 Please use:\n/num {raw}\n\n"
                f"📝 Example: /num {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        elif is_aadhaar_number(raw):
            send_message(
                chat_id,
                f"🆔 Looks like you entered an Aadhaar number!\n\n"
                f"💡 Please use:\n/aadhaar {raw}\n\n"
                f"📝 Example: /aadhaar {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        elif is_gstin(raw):
            send_message(
                chat_id,
                f"🏢 Looks like you entered a GSTIN!\n\n"
                f"💡 Please use:\n/gst {raw}\n\n"
                f"📝 Example: /gst {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        elif is_ifsc_code(raw):
            send_message(
                chat_id,
                f"🏦 Looks like you entered an IFSC code!\n\n"
                f"💡 Please use:\n/ifsc {raw}\n\n"
                f"📝 Example: /ifsc {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        elif is_upi_id(raw):
            send_message(
                chat_id,
                f"💸 Looks like you entered a UPI ID!\n\n"
                f"💡 Please use:\n/upi {raw}\n\n"
                f"📝 Example: /upi {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        elif is_fam_id(raw):
            send_message(
                chat_id,
                f"👨‍👩‍👧‍👦 Looks like you entered a FAM ID!\n\n"
                f"💡 Please use:\n/fam {raw}\n\n"
                f"📝 Example: /fam {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        elif is_vehicle_number(raw):
            send_message(
                chat_id,
                f"🚗 Looks like you entered a vehicle number!\n\n"
                f"💡 Please use:\n/vehicle {raw}\n\n"
                f"📝 Example: /vehicle {raw}",
                reply_to_message_id=reply_to
            )
            return
            
        else:
            # Random text - NO RESPONSE
            return

    # ---------- /num ----------
    if lower.startswith("/num "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide mobile number\n💡 Example: /num 9876543210", reply_to_message_id=reply_to)
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
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)
        try:
            res = requests.get(MOBILE_API + clean_text, headers=HEADERS, timeout=30).json()
            r = res.get("data", [])


            if not r:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return

            fid = send_txt_file_with_caption(
                chat_id,
                f"Report_{clean_text}.txt",
                build_common_txt(r[0]),
                reply_to_message_id=reply_to
            )
            delete_message(chat_id, loading)
            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /aadhaar ----------
    if lower.startswith("/aadhaar "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide Aadhaar number\n💡 Example: /aadhaar 123456789012", reply_to_message_id=reply_to)
            return
            
        if not is_aadhaar_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid Aadhaar number!\n\n"
                "💡 Example: /aadhaar 123456789012\n"
                "📌 Format: 12 digits, no spaces",
                reply_to_message_id=reply_to
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)
        try:
            res = requests.get(AADHAAR_API + clean_text, headers=HEADERS, timeout=30).json()
            r = res.get("data", {}).get("result", [])
            if not r:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{clean_text}.txt", build_common_txt(r[0]), reply_to_message_id=reply_to)
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /gst ----------
    if lower.startswith("/gst "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide GSTIN\n💡 Example: /gst 24ABCDE1234F1Z5", reply_to_message_id=reply_to)
            return
            
        if not is_gstin(clean_text.upper()):
            send_message(
                chat_id,
                "❌ Invalid GSTIN!\n\n"
                "💡 Example: /gst 24ABCDE1234F1Z5\n"
                "📌 Format: 24ABCDE1234F1Z5",
                reply_to_message_id=reply_to
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)
        try:
            d = requests.get(GST_API + clean_text.upper(), headers=HEADERS, timeout=30).json().get("data", {}).get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{clean_text}.txt", build_gst_txt(d), reply_to_message_id=reply_to)
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /ifsc ----------
    if lower.startswith("/ifsc "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide IFSC code\n💡 Example: /ifsc SBIN0000000", reply_to_message_id=reply_to)
            return
            
        if not is_ifsc_code(clean_text.upper()):
            send_message(
                chat_id,
                "❌ Invalid IFSC code!\n\n"
                "💡 Example: /ifsc SBIN0000000\n"
                "📌 Format: SBIN0000000 (11 chars, 5th char=0)",
                reply_to_message_id=reply_to
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)
        try:
            d = requests.get(IFSC_API + clean_text.upper(), headers=HEADERS, timeout=30).json().get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{clean_text}.txt", build_ifsc_txt(d), reply_to_message_id=reply_to)
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /upi ----------
    if lower.startswith("/upi "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide UPI ID\n💡 Example: /upi username@bank", reply_to_message_id=reply_to)
            return

        if not is_upi_id(clean_text):
            send_message(
                chat_id,
                "❌ Invalid UPI ID!\n\n"
                "💡 Example: /upi username@bank\n"
                "📌 Format: Must contain @ symbol",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)
        try:
            res = requests.get(UPI_API + clean_text, headers=HEADERS, timeout=30).json()
            arr = res.get("data", {}).get("data", {}).get("verify_chumts", [])
            if not arr:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return
            fid = send_txt_file_with_caption(
                chat_id,
                f"Report_{clean_text}.txt",
                build_upi_txt(arr[0]),
                reply_to_message_id=reply_to
            )
            delete_message(chat_id, loading)
            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /fam ----------
    if lower.startswith("/fam "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide FAM ID\n💡 Example: /fam username@fam", reply_to_message_id=reply_to)
            return
            
        if not is_fam_id(clean_text):
            send_message(
                chat_id,
                "❌ Invalid FAM ID!\n\n"
                "💡 Example: /fam username@fam\n"
                "📌 Format: Must end with @fam",
                reply_to_message_id=reply_to
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)
        try:
            d = requests.get(FAM_API + clean_text, headers=HEADERS, timeout=30).json().get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{clean_text}.txt", build_fam_txt(d), reply_to_message_id=reply_to)
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /vehicle ----------
    if lower.startswith("/vehicle "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide vehicle number\n💡 Example: /vehicle GJ01AB1234", reply_to_message_id=reply_to)
            return
            
        reg = clean_text.upper()
        if not is_vehicle_number(reg):
            send_message(
                chat_id,
                "❌ Invalid vehicle number!\n\n"
                "💡 Example: /vehicle GJ01AB1234\n"
                "📌 Format: XX##XXX####",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳", reply_to_message_id=reply_to)

        try:
            # Try v1 API
            res = requests.get(VEHICLE_API + reg, headers=HEADERS, timeout=30).json()
            
            if res.get("success"):
                # Use v1 API data
                address_data = res.get("address", {})
                content = build_vehicle_txt(reg, address_data)
                
                # Send file
                fid = send_txt_file_with_caption(
                    chat_id,
                    f"Report_{clean_text}.txt",
                    content,
                    reply_to_message_id=reply_to
                )

                delete_message(chat_id, loading)
                threading.Thread(
                    target=auto_delete_file,
                    args=(chat_id, fid),
                  daemon=True
                ).start()
            else:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found for this vehicle", reply_to_message_id=reply_to)

        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found", reply_to_message_id=reply_to)
        return

    # ---------- /vnum ----------
    if lower.startswith("/vnum "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide vehicle number\n💡 Example: /vnum GJ03HD0255", reply_to_message_id=reply_to)
            return

        reg = clean_text.upper()
        if not is_vehicle_number(reg):
            send_message(
                chat_id,
                "❌ Invalid vehicle number!\n\n"
                "💡 Example: /vnum GJ03HD0255\n"
                "📌 Format: XX##XXX####",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(chat_id, "🔍 Fetching vehicle data… please wait ⏳", reply_to_message_id=reply_to)

        try:
            res = requests.get(VNUM_API + reg, timeout=30).json()
            data = res.get("rc_data", {}).get("data", [])

            if not data:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return   # ✅ yahin hona chahiye

            content = build_vnum_txt(data[0])

            fid = send_txt_file_with_caption(
                chat_id,
                f"vnum_{reg}.txt"
,
                content,
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
            print("VNUM ERROR:", e)
            send_message(chat_id, "📂❌ API error / server down", reply_to_message_id=reply_to)

        return

    
    # ---------- /tg ----------
    if lower.startswith("/tg "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Telegram username\n💡 Example: /tg @username",
                reply_to_message_id=reply_to
            )
            return

        username = clean_text
        if not username.startswith("@"):
            send_message(
                chat_id,
                "❌ Invalid username format!\n\n"
                "💡 Example: /tg @username\n"
                "📌 Format: Must start with @",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Resolving username… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            user_id_resolved = loop.run_until_complete(resolve_username(username))

            if not user_id_resolved:
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "❌ Username resolve FAILED",
                    reply_to_message_id=reply_to
                )
                return

            delete_message(chat_id, loading)

            loading2 = send_message(
                chat_id,
                f"🆔 Resolved ID: {user_id_resolved}\n🔍 Fetching data…",
                reply_to_message_id=reply_to
            )

            r = requests.get(OSINT_API + str(user_id_resolved), timeout=30).json()
            if not r.get("success"):
                delete_message(chat_id, loading2)
                send_message(
                    chat_id,
                    "❌ OSINT API failed",
                    reply_to_message_id=reply_to
                )
                return
                                
            delete_message(chat_id, loading2)

            # ✅ FINAL OUTPUT (BOTTOM TEXT PERFECT POSITION)
            final_text = (
                format_tg_output(r["data"]["data"])
                + "\n\n"
                + "━━━━━━━━━━━━━━\n"
                + "⏳ This response deleted in 60s ⏱️"
            )

            final_msg = send_message(
                chat_id,
                final_text,
                reply_to_message_id=reply_to
            )

            threading.Thread(
                target=lambda: (time.sleep(60), delete_message(chat_id, final_msg)),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print(f"[ERROR] /tg command failed: {e}")
            send_message(
                chat_id,
                "📂❌ Private account — no data available.",
                reply_to_message_id=reply_to
            )
        return
        
    # ---------- /tg ----------
    if lower.startswith("/tg "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Telegram username\n💡 Example: /tg @username",
                reply_to_message_id=reply_to
            )
            return

        username = clean_text
        if not username.startswith("@"):
            send_message(
                chat_id,
                "❌ Invalid username format!\n\n"
                "💡 Example: /tg @username\n"
                "📌 Format: Must start with @",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🔍 Resolving username… please wait ⏳",
            reply_to_message_id=reply_to
        )

        try:
            user_id_resolved = loop.run_until_complete(resolve_username(username))

            if not user_id_resolved:
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "❌ Username resolve FAILED",
                    reply_to_message_id=reply_to
                )
                return

            delete_message(chat_id, loading)

            loading2 = send_message(
                chat_id,
                f"🆔 Resolved ID: {user_id_resolved}\n🔍 Fetching data…",
                reply_to_message_id=reply_to
            )

            r = requests.get(OSINT_API + str(user_id_resolved), timeout=30).json()
            if not r.get("success"):
                delete_message(chat_id, loading2)
                send_message(
                    chat_id,
                    "❌ OSINT API failed",
                    reply_to_message_id=reply_to
                )
                return

            delete_message(chat_id, loading2)

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
                f"Report_{clean_text}.txt",
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
                f"Report_{clean_text}.txt",
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
    
    # ---------- /ip ----------
    if lower.startswith("/ip "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide IP\n💡 Example: /ip 8.8.8.8", reply_to_message_id=reply_to)
            return

        loading = send_message(chat_id, "🌐 Fetching IP details… ⏳", reply_to_message_id=reply_to)

        try:
            res = requests.get(IP_API + clean_text, headers=HEADERS, timeout=30).json()

            if not res.get("success"):
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found", reply_to_message_id=reply_to)
                return

            d = res.get("data", {})

            fid = send_txt_file_with_caption(
                chat_id,
                f"IP_{clean_text}.txt",
                build_ip_txt(d),
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
            print("IP ERROR:", e)
            send_message(chat_id, "📂❌ API error / server down", reply_to_message_id=reply_to)

        return
        
    # ---------- /ff ----------
    if lower.startswith("/ff "):
        if not clean_text:
            send_message(
                chat_id,
                "❌ Please provide Free Fire UID\n\n"
                "💡 Example:\n"
                "<code>/ff 2819649271</code>",
                reply_to_message_id=reply_to
            )
            return

        loading = send_message(
            chat_id,
            "🎮 Fetching Free Fire profile… ⏳",
            reply_to_message_id=reply_to
        )

        try:
            res = requests.get(FF_API + clean_text, headers=HEADERS, timeout=30).json()

            if not res.get("success"):
                delete_message(chat_id, loading)
                send_message(
                    chat_id,
                    "❌ No data found for this UID",
                    reply_to_message_id=reply_to
                )
                return

            d = res.get("data", {})

            delete_message(chat_id, loading)

            final_text = format_ff_output(d)

            final_msg = send_message(
                chat_id,
                final_text,
                reply_to_message_id=reply_to
            )

            # Auto delete in 60 seconds
            threading.Thread(
                target=lambda: (time.sleep(60), delete_message(chat_id, final_msg)),
                daemon=True
            ).start()

        except Exception as e:
            delete_message(chat_id, loading)
            print("FF ERROR:", e)
            send_message(
                chat_id,
                "📂❌ API error / server down",
                reply_to_message_id=reply_to
            )

        return
    
    # ---------- /truecaller ----------
    if lower.startswith("/truecaller "):
        if not clean_text:
            send_message(
                    chat_id,
            "❌ Please provide mobile number\n💡 Example: /truecaller 9876543210",
                    reply_to_message_id=reply_to
            )
            return

        if not is_mobile_number(clean_text):
            send_message(
                    chat_id,
            "❌ Invalid mobile number!\n\n"
            "💡 Example: /truecaller 9876543210\n"
            "📌 Format: 10 digits only",
                    reply_to_message_id=reply_to
            )
            return

    # Auto add 91
        number = "91" + clean_text

    loading = send_message(
        chat_id,
        "📞 Searching Truecaller… ⏳",
        reply_to_message_id=reply_to
    )

    try:
        res = requests.get(TRUECALLER_API + number, timeout=20).json()

        if not res.get("success"):
            delete_message(chat_id, loading)
            send_message(
                chat_id,
                "❌ No data found",
                reply_to_message_id=reply_to
            )
            return

        data = res.get("data", {})
        name = data.get("name", "Not Found")
        num = data.get("number", number)

        final_text = (
            "📞 <b>TRUECALLER RESULT</b>\n\n"
            f"👤 <b>Name:</b> {name}\n"
            f"📱 <b>Number:</b> <code>{num}</code>\n\n"
            "━━━━━━━━━━━━━━\n"
            "⏳ Auto delete in 60 seconds\n"
            "⚡ <b>Powered by</b> <code>@imvrct</code>"
        )

        delete_message(chat_id, loading)

        final_msg = send_message(
            chat_id,
            final_text,
            reply_to_message_id=reply_to
        )

        # Auto delete after 60s
        threading.Thread(
            target=lambda: (time.sleep(60), delete_message(chat_id, final_msg)),
            daemon=True
        ).start()

    except Exception as e:
        delete_message(chat_id, loading)
        print("TRUECALLER ERROR:", e)
        send_message(
            chat_id,
            "📂❌ API error / server down",
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
                                send_message(chat_id, WELCOME_MESSAGE)

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
