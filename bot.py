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
FORCE_JOIN_CHANNEL = "@DeepXTrace2"
VERIFIED_USERS_FILE = "verified_users.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Accept": "application/json"
}
WELCOME_MESSAGE = (
    "╭────────────────────────╮\n"
    "   🔍 DEEP TRACE BOT\n"
    "╰────────────────────────╯\n\n"
    "Mobile    ➜ /num 9876543210\n"
    "Aadhaar   ➜ /aadhaar 123456789012\n"
    "GST       ➜ /gst 24ABCDE1234F1Z5\n"
    "IFSC      ➜ /ifsc SBIN0000000\n"
    "UPI       ➜ /upi username@bank\n"
    "FAM       ➜ /fam username@fam\n"
    "Vehicle   ➜ /vehicle GJ01AB1234\n\n"
    "📩 Contact Admin\n"
    "/admin your message\n\n"
    "⏳ Files auto-delete in 60 seconds"
)

# ================= ADMIN CONFIG =================
ADMIN_IDS = [5221493804]

# ================= LICENCE FILES =================
KEYS_FILE = "keys.txt"
USED_KEYS_FILE = "used_keys.json"
ACTIVE_USERS_FILE = "active_users.json"

# ================= LICENCE FUNCTIONS =================
def init_licence_files():
    if not os.path.exists(KEYS_FILE):
        open(KEYS_FILE, "w").close()
    if not os.path.exists(USED_KEYS_FILE):
        with open(USED_KEYS_FILE, "w") as f:
            json.dump({}, f)
    if not os.path.exists(ACTIVE_USERS_FILE):
        with open(ACTIVE_USERS_FILE, "w") as f:
            json.dump({}, f)

def load_keys():
    with open(KEYS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_key(key):
    with open(KEYS_FILE, "a") as f:
        f.write(key + "\n")

def load_used_keys():
    with open(USED_KEYS_FILE, "r") as f:
        return json.load(f)

def save_used_keys(data):
    with open(USED_KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_active_users():
    with open(ACTIVE_USERS_FILE, "r") as f:
        return json.load(f)

def save_active_users(data):
    with open(ACTIVE_USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

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
def parse_address(addr):
    if not addr:
        return "Not Available"
    parts = addr.replace("!!", "!").split("!")
    parts = [x.title() for x in parts if x.strip()]
    return ", ".join(parts)

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    r = requests.post(
        TG_API + "/sendMessage",
        json=payload,
        timeout=20
    )
    return r.json()["result"]["message_id"]

def delete_message(chat_id, message_id):
    requests.post(
        TG_API + "/deleteMessage",
        json={"chat_id": chat_id, "message_id": message_id},
        timeout=20
    )

def send_txt_file_with_caption(chat_id, filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    caption = (
        "✅ File Generated Successfully\n"
        f"📂 {filename}\n"
        "⏳ This message will auto-delete in 60s"
    )

    with open(filename, "rb") as f:
        r = requests.post(
            TG_API + "/sendDocument",
            files={"document": f},
            data={"chat_id": chat_id, "caption": caption},
            timeout=30
        )

    os.remove(filename)
    return r.json()["result"]["message_id"]

def auto_delete_file(chat_id, file_msg_id, delay=60):
    time.sleep(delay)
    delete_message(chat_id, file_msg_id)
import json

def load_verified_users():
    try:
        with open(VERIFIED_USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_verified_users(data):
    with open(VERIFIED_USERS_FILE, "w") as f:
        json.dump(data, f)

def is_user_verified(user_id):
    data = load_verified_users()
    return str(user_id) in data

def mark_user_verified(user_id):
    data = load_verified_users()
    data[str(user_id)] = True
    save_verified_users(data)

def send_join_message(chat_id):
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "➕ Add me to your Group / Channel",
                    "url": "https://t.me/YourBotUsername?startgroup=true"
                }
            ],
            [
                {
                    "text": "📢 Join Channel",
                    "url": "https://t.me/DeepXTrace2"
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
        "🔒 Access Required\n\n"
        "To use Deep Trace Bot in groups or channels,\n"
        "please join our official channel.\n\n"
        "⏳ This message will auto-delete in 60s"
    )

    msg_id = send_message(chat_id, text, reply_markup=keyboard)
    
    # Auto-delete after 60 seconds
    threading.Thread(
        target=lambda: (time.sleep(60), delete_message(chat_id, msg_id)),
        daemon=True
    ).start()
    

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
ID Number   : {d.get('id_number')}
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
def process_message(chat_id, text, user_id):
    # Sirf Telegram service messages ko block karo
    SYSTEM_BOT_IDS = [777000]  # Telegram official notifications only
    
    if user_id in SYSTEM_BOT_IDS:
        print(f"⚠️ Blocked Telegram service message: {user_id}")
        return
    raw = text.strip()
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
    # ===== END DEBUG =====

    # ===== JOIN VERIFICATION (GROUP ONLY) =====
    if chat_id != user_id:  # Sirf group mein
        if user_id != 1087968824 and not is_user_verified(user_id):
            # Check if command or meaningful input
            if raw.startswith("/") or (len(raw) > 5 and not raw.isspace()):
                send_join_message(chat_id)
                return
    # ===== END JOIN CHECK =====
    
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
            f"🔑 New Licence Key Generated\n\n<code>{key}</code>\n\nTap the key to copy"
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
        
        send_message(chat_id, msg)
        return

    if lower == "/activeusers":
        if not is_admin(user_id):
            return
        
        active_users = load_active_users()
        
        if not active_users:
            send_message(chat_id, "No active users")
            return
        
        msg = "👥 Active Users\n\n"
        
        for user_key, data in active_users.items():
            uid = user_key.split("_")[0]
            remaining = get_remaining_time(data["expiry"])
            msg += f"User ID: {uid}\nTime Left: {remaining}\n\n"
        
        send_message(chat_id, msg)
        return

    if lower.startswith("/blockkey "):
        if not is_admin(user_id):
            return
        
        if not clean_text:
            send_message(chat_id, "❌ Please provide key\n💡 Example: /blockkey DTX-XXXX")
            return
        
        block_key(clean_text)
        send_message(chat_id, f"✅ Key blocked: {clean_text}")
        return

    if lower == "/admincmd":
        if not is_admin(user_id):
            return
        
        send_message(
            chat_id,
            "👑 Admin Licence Commands\n\n"
            "/genkey\n→ Generate new copyable licence key\n\n"
            "/showkeys\n→ View licence keys & remaining time\n\n"
            "/activeusers\n→ View active users\n\n"
            "/blockkey DTX-XXXX\n→ Block a licence key"
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
                "/admin I need help"
            )
            return

        chat_type = "Private Chat"
        chat_name = ""

        if chat_id != user_id:
            chat_type = "Group Chat"
            chat_name = u["message"]["chat"].get("title", "")

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

        send_message(chat_id, "✅ Your message has been sent to the Admin")
        return
    
    # ---------- /reply (Admin Reply) ----------
    if lower.startswith("/reply "):
        if not is_admin(user_id):
            return

        parts = clean_text.split(" ", 1)
        if len(parts) < 2:
            send_message(
                chat_id,
                "❌ Use format:\n/reply USER_ID message"
            )
            return

        try:
            target_user_id = int(parts[0])
        except:
            send_message(chat_id, "❌ Invalid User ID")
            return

        reply_text = parts[1]

        send_message(
            target_user_id,
            "📩 Message from Admin\n\n" + reply_text
        )

        send_message(chat_id, "✅ Reply sent to user")
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
        send_message(chat_id, WELCOME_MESSAGE)
        return

    # ---------- Direct info without command ----------
    if not raw.startswith('/'):
        if is_mobile_number(raw):
            send_message(
                chat_id,
                f"📱 Looks like you entered a mobile number!\n\n"
                f"💡 Please use:\n/num {raw}\n\n"
                f"📝 Example: /num {raw}"
            )
            return
            
        elif is_aadhaar_number(raw):
            send_message(
                chat_id,
                f"🆔 Looks like you entered an Aadhaar number!\n\n"
                f"💡 Please use:\n/aadhaar {raw}\n\n"
                f"📝 Example: /aadhaar {raw}"
            )
            return
            
        elif is_gstin(raw):
            send_message(
                chat_id,
                f"🏢 Looks like you entered a GSTIN!\n\n"
                f"💡 Please use:\n/gst {raw}\n\n"
                f"📝 Example: /gst {raw}"
            )
            return
            
        elif is_ifsc_code(raw):
            send_message(
                chat_id,
                f"🏦 Looks like you entered an IFSC code!\n\n"
                f"💡 Please use:\n/ifsc {raw}\n\n"
                f"📝 Example: /ifsc {raw}"
            )
            return
            
        elif is_upi_id(raw):
            send_message(
                chat_id,
                f"💸 Looks like you entered a UPI ID!\n\n"
                f"💡 Please use:\n/upi {raw}\n\n"
                f"📝 Example: /upi {raw}"
            )
            return
            
        elif is_fam_id(raw):
            send_message(
                chat_id,
                f"👨‍👩‍👧‍👦 Looks like you entered a FAM ID!\n\n"
                f"💡 Please use:\n/fam {raw}\n\n"
                f"📝 Example: /fam {raw}"
            )
            return
            
        elif is_vehicle_number(raw):
            send_message(
                chat_id,
                f"🚗 Looks like you entered a vehicle number!\n\n"
                f"💡 Please use:\n/vehicle {raw}\n\n"
                f"📝 Example: /vehicle {raw}"
            )
            return
            
        else:
            # Random text - NO RESPONSE
            return

    # ---------- /num ----------
    if lower.startswith("/num "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide mobile number\n💡 Example: /num 9876543210")
            return
            
        if not is_mobile_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid mobile number!\n\n"
                "💡 Example: /num 9876543210\n"
                "📌 Format: 10 digits, starts with 6-9"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            res = requests.get(MOBILE_API + clean_text, headers=HEADERS, timeout=30).json()
            r = res.get("data", {}).get("data", {}).get("result", [])

            if not r:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return

            fid = send_txt_file_with_caption(
                chat_id,
                f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_common_txt(r[0])
            )
            delete_message(chat_id, loading)
            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- /aadhaar ----------
    if lower.startswith("/aadhaar "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide Aadhaar number\n💡 Example: /aadhaar 123456789012")
            return
            
        if not is_aadhaar_number(clean_text):
            send_message(
                chat_id,
                "❌ Invalid Aadhaar number!\n\n"
                "💡 Example: /aadhaar 123456789012\n"
                "📌 Format: 12 digits, no spaces"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            res = requests.get(AADHAAR_API + clean_text, headers=HEADERS, timeout=30).json()
            r = res.get("data", {}).get("result", [])
            if not r:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_common_txt(r[0]))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- /gst ----------
    if lower.startswith("/gst "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide GSTIN\n💡 Example: /gst 24ABCDE1234F1Z5")
            return
            
        if not is_gstin(clean_text.upper()):
            send_message(
                chat_id,
                "❌ Invalid GSTIN!\n\n"
                "💡 Example: /gst 24ABCDE1234F1Z5\n"
                "📌 Format: 24ABCDE1234F1Z5"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            d = requests.get(GST_API + clean_text.upper(), headers=HEADERS, timeout=30).json().get("data", {}).get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_gst_txt(d))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- /ifsc ----------
    if lower.startswith("/ifsc "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide IFSC code\n💡 Example: /ifsc SBIN0000000")
            return
            
        if not is_ifsc_code(clean_text.upper()):
            send_message(
                chat_id,
                "❌ Invalid IFSC code!\n\n"
                "💡 Example: /ifsc SBIN0000000\n"
                "📌 Format: SBIN0000000 (11 chars, 5th char=0)"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            d = requests.get(IFSC_API + clean_text.upper(), headers=HEADERS, timeout=30).json().get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_ifsc_txt(d))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- /upi ----------
    if lower.startswith("/upi "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide UPI ID\n💡 Example: /upi username@bank")
            return

        if not is_upi_id(clean_text):
            send_message(
                chat_id,
                "❌ Invalid UPI ID!\n\n"
                "💡 Example: /upi username@bank\n"
                "📌 Format: Must contain @ symbol"
            )
            return

        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            res = requests.get(UPI_API + clean_text, headers=HEADERS, timeout=30).json()
            arr = res.get("data", {}).get("data", {}).get("verify_chumts", [])
            if not arr:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(
                chat_id,
                f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                build_upi_txt(arr[0])
            )
            delete_message(chat_id, loading)
            threading.Thread(
                target=auto_delete_file,
                args=(chat_id, fid),
                daemon=True
            ).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- /fam ----------
    if lower.startswith("/fam "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide FAM ID\n💡 Example: /fam username@fam")
            return
            
        if not is_fam_id(clean_text):
            send_message(
                chat_id,
                "❌ Invalid FAM ID!\n\n"
                "💡 Example: /fam username@fam\n"
                "📌 Format: Must end with @fam"
            )
            return
            
        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")
        try:
            d = requests.get(FAM_API + clean_text, headers=HEADERS, timeout=30).json().get("data", {})
            if not d:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found")
                return
            fid = send_txt_file_with_caption(chat_id, f"Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt", build_fam_txt(d))
            delete_message(chat_id, loading)
            threading.Thread(target=auto_delete_file, args=(chat_id, fid), daemon=True).start()
        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- /vehicle ----------
    if lower.startswith("/vehicle "):
        if not clean_text:
            send_message(chat_id, "❌ Please provide vehicle number\n💡 Example: /vehicle GJ01AB1234")
            return
            
        reg = clean_text.upper()
        if not is_vehicle_number(reg):
            send_message(
                chat_id,
                "❌ Invalid vehicle number!\n\n"
                "💡 Example: /vehicle GJ01AB1234\n"
                "📌 Format: XX##XXX####"
            )
            return

        loading = send_message(chat_id, "🔍 Fetching details… please wait ⏳")

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
                    f"Vehicle_Report_{reg}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt",
                    content
                )

                delete_message(chat_id, loading)
                threading.Thread(
                    target=auto_delete_file,
                    args=(chat_id, fid),
                  daemon=True
                ).start()
            else:
                delete_message(chat_id, loading)
                send_message(chat_id, "⚠️ No record found for this vehicle")

        except:
            delete_message(chat_id, loading)
            send_message(chat_id, "📂❌ No database found")
        return

    # ---------- Invalid command (starts with / but not valid) ----------
    # NO RESPONSE - just return
    return

# ================= START =================
def main():
    init_licence_files()
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
                    user_id = q["from"]["id"]  # Button press karne wala user
                    callback_id = q["id"]
                    message_id = q["message"]["message_id"]

                    print(f"\n{'='*50}")
                    print(f"🔔 CALLBACK QUERY")
                    print(f"{'='*50}")
                    print(f"User ID (Button Press): {user_id}")
                    print(f"Chat ID: {chat_id}")
                    print(f"Callback Data: {data}")
                    print(f"{'='*50}\n")

                    if data == "join_confirm":
                        try:
                            # First answer callback to remove loading
                            requests.post(
                                TG_API + "/answerCallbackQuery",
                                json={"callback_query_id": callback_id}
                            )
                            
                            member = requests.get(
                                TG_API + "/getChatMember",
                                params={
                                    "chat_id": FORCE_JOIN_CHANNEL,
                                    "user_id": user_id
                                }
                            ).json()

                            status = member.get("result", {}).get("status")
                            print(f"Channel Status: {status}")

                            if status in ["member", "administrator", "creator"]:
                                mark_user_verified(user_id)
                                
                                verified_data = load_verified_users()
                                print(f"✅ User {user_id} verified")
                                print(f"Verified Users: {verified_data}")

                                # Show success popup
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
                            else:
                                # Show error popup
                                requests.post(
                                    TG_API + "/answerCallbackQuery",
                                    json={
                                        "callback_query_id": callback_id,
                                        "text": "❌ Please join the channel first!\n\nClick 'Join Channel' button and try again.",
                                        "show_alert": True
                                    }
                                )
                        except Exception as e:
                            print(f"❌ Verification Error: {e}")
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
                    
                    # User ID properly extract karo
                    if "from" in msg:
                        user_id = msg["from"]["id"]
                        
                        # Process message (system bot IDs check process_message mein hai)
                        process_message(chat_id, text, user_id)
                    else:
                        print("⚠️ Message without 'from' field - skipping")
                        continue

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
