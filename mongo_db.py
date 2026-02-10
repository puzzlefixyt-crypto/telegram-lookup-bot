import os
from pymongo import MongoClient
from datetime import datetime

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if not MONGO_URI:
    print("❌ ERROR: MONGO_URI environment variable not set!")
    print("Please set MONGO_URI in Render Environment Variables")
    exit(1)

client = MongoClient(MONGO_URI)
db = client["deeptracex"]

# Collections
verified_users_collection = db["verified_users"]
active_users_collection = db["active_users"]
used_keys_collection = db["used_keys"]
stats_collection = db["stats"]
disabled_commands_collection = db["disabled_commands"]
bomb_credits_collection = db["bomb_credits"]

# ================= VERIFIED USERS =================
def load_verified_users():
    """Load verified users from MongoDB and return as a list"""
    doc = verified_users_collection.find_one({"_id": "verified_users"})
    if doc and "users" in doc:
        return doc["users"]
    return []

def save_verified_users(users_list):
    """Save verified users list to MongoDB"""
    verified_users_collection.update_one(
        {"_id": "verified_users"},
        {"$set": {"users": users_list}},
        upsert=True
    )

# ================= ACTIVE USERS =================
def load_active_users():
    """Load active users from MongoDB and return as a dictionary"""
    doc = active_users_collection.find_one({"_id": "active_users"})
    if doc and "data" in doc:
        return doc["data"]
    return {}

def save_active_users(data):
    """Save active users dictionary to MongoDB"""
    active_users_collection.update_one(
        {"_id": "active_users"},
        {"$set": {"data": data}},
        upsert=True
    )

# ================= USED KEYS =================
def load_used_keys():
    """Load used keys from MongoDB and return as a dictionary"""
    doc = used_keys_collection.find_one({"_id": "used_keys"})
    if doc and "data" in doc:
        return doc["data"]
    return {}

def save_used_keys(data):
    """Save used keys dictionary to MongoDB"""
    used_keys_collection.update_one(
        {"_id": "used_keys"},
        {"$set": {"data": data}},
        upsert=True
    )

# ================= BOT STATS =================
def load_stats():
    """Load bot stats from MongoDB and return as a dictionary"""
    doc = stats_collection.find_one({"_id": "bot_stats"})
    if doc and "data" in doc:
        return doc["data"]
    # Return default structure if no data exists
    return {
        "private_users": {},
        "groups": {},
        "channels": {},
        "verified_today": {}
    }

def save_stats(data):
    """Save bot stats dictionary to MongoDB"""
    stats_collection.update_one(
        {"_id": "bot_stats"},
        {"$set": {"data": data}},
        upsert=True
    )

# ================= DISABLED COMMANDS =================
def load_disabled_commands():
    """Load disabled commands from MongoDB and return as a list"""
    doc = disabled_commands_collection.find_one({"_id": "disabled_commands"})
    if doc and "commands" in doc:
        return doc["commands"]
    return []

def save_disabled_commands(commands_list):
    """Save disabled commands list to MongoDB"""
    disabled_commands_collection.update_one(
        {"_id": "disabled_commands"},
        {"$set": {"commands": commands_list}},
        upsert=True
    )

# ================= TRACKING LINKS (FOR /findip) =================
tracking_links_collection = db["tracking_links"]
findip_requests_collection = db["findip_requests"]

def save_tracking_link(token, user_id, username, request_no, expiry_time, chat_id=None, message_id=None):
    """Save tracking link data to MongoDB"""
    tracking_links_collection.insert_one({
        "token": token,
        "user_id": user_id,
        "username": username,
        "request_no": request_no,
        "expiry_time": expiry_time.isoformat(),
        "chat_id": chat_id,  # Group/chat where command was used
        "message_id": message_id,  # Original message to reply to
        "clicked": False,
        "created_at": datetime.utcnow().isoformat()
    })

def get_tracking_link(token):
    """Get tracking link data by token"""
    return tracking_links_collection.find_one({"token": token})

def mark_link_clicked(token):
    """Mark tracking link as clicked"""
    tracking_links_collection.update_one(
        {"token": token},
        {"$set": {"clicked": True}}
    )

def get_user_request_count(user_id):
    """Get and increment request count for a user"""
    doc = findip_requests_collection.find_one({"user_id": user_id})
    if doc:
        count = doc.get("count", 0) + 1
        findip_requests_collection.update_one(
            {"user_id": user_id},
            {"$set": {"count": count}}
        )
        return count
    else:
        findip_requests_collection.insert_one({"user_id": user_id, "count": 1})
        return 1

def get_global_request_number():
    """Get and increment global request number for all users"""
    global_counter_collection = db["global_counter"]
    doc = global_counter_collection.find_one({"_id": "findip_requests"})
    
    if doc:
        count = doc.get("count", 0) + 1
        global_counter_collection.update_one(
            {"_id": "findip_requests"},
            {"$set": {"count": count}}
        )
        return count
    else:
        global_counter_collection.insert_one({"_id": "findip_requests", "count": 1})
        return 1

def load_bomb_credits():
    """Load bomb credits from MongoDB and return as a dictionary"""
    doc = bomb_credits_collection.find_one({"_id": "bomb_credits"})
    if doc and "data" in doc:
        return doc["data"]
    return {}

def save_bomb_credits(data):
    """Save bomb credits dictionary to MongoDB"""
    bomb_credits_collection.update_one(
        {"_id": "bomb_credits"},
        {"$set": {"data": data}},
        upsert=True
    )

# ===== AVAILABLE KEYS =====
def load_available_keys():
    return db.available_keys.find_one({"_id": "available"}) or {}

def save_available_keys(data):
    db.available_keys.update_one(
        {"_id": "available"},
        {"$set": data},
        upsert=True
    )    