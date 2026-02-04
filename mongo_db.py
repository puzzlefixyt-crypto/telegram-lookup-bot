import os
from pymongo import MongoClient
from datetime import datetime

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
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
