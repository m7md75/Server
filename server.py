"""
WeJZ Client Online Server
User authentication and friend system backend
Ready for cloud deployment with Supabase PostgreSQL
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import Optional, List
import hashlib
import secrets
import time
from datetime import datetime
from contextlib import contextmanager
import uvicorn
import os

# PostgreSQL with Supabase
import psycopg2
from psycopg2.extras import RealDictCursor

# Get port from environment (for cloud hosting)
PORT = int(os.environ.get("PORT", 8000))
# Secret key for extra security (set in environment)
SECRET_KEY = os.environ.get("SECRET_KEY", "wejz-default-key-change-in-production")

# Database URL - Supabase PostgreSQL
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:5tCHmCdfgUViS1i9@db.hlzzwuzjkbkgojwppahz.supabase.co:5432/postgres"
)

app = FastAPI(title="WeJZ Online", version="1.0.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Database Setup (PostgreSQL) ==============
DB_CONNECTED = False

# Health check endpoint (no database needed)
@app.get("/")
async def root():
    return {"status": "ok", "service": "WeJZ Online", "db_connected": DB_CONNECTED}

@app.get("/health")
async def health():
    return {"status": "ok", "db": DB_CONNECTED}

@contextmanager
def get_db():
    """Get PostgreSQL connection"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        yield conn
    except psycopg2.Error as e:
        print(f"[DB ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)[:100]}")
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize database tables in PostgreSQL"""
    global DB_CONNECTED
    try:
        print(f"[DB] Connecting to: {DATABASE_URL[:50]}...")
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_online TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_online INTEGER DEFAULT 0,
                session_token VARCHAR(255)
            )
        """)
        
        # Friends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friends (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                friend_id INTEGER NOT NULL REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, friend_id)
            )
        """)
        
        # Chat messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id),
                receiver_id INTEGER NOT NULL REFERENCES users(id),
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            )
        """)
        
        # Voice call sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_calls (
                id SERIAL PRIMARY KEY,
                caller_id INTEGER NOT NULL REFERENCES users(id),
                receiver_id INTEGER NOT NULL REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        DB_CONNECTED = True
        print("[DB] PostgreSQL connected to Supabase!")
    except Exception as e:
        DB_CONNECTED = False
        print(f"[DB ERROR] Failed to connect: {e}")

# ============== Models ==============

class UserRegister(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class FriendRequest(BaseModel):
    token: str
    target_username: str

class TokenRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    is_online: bool
    last_online: str

class FriendResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    is_online: bool
    status: str

class SendMessage(BaseModel):
    token: str
    to_username: str
    message: str

class GetMessages(BaseModel):
    token: str
    with_username: str
    limit: Optional[int] = 50

class VoiceCallRequest(BaseModel):
    token: str
    target_username: str

# ============== Helper Functions ==============

def hash_password(password: str) -> str:
    """Hash password with salt - more secure version"""
    salt = SECRET_KEY + "wejz_salt_2024"
    # Multiple rounds for better security
    result = password
    for _ in range(1000):
        result = hashlib.sha256(f"{result}{salt}".encode()).hexdigest()
    return result

def generate_token() -> str:
    """Generate secure session token"""
    return secrets.token_hex(32)

def get_user_by_token(token: str):
    """Get user from session token"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE session_token = %s", (token,))
        return cursor.fetchone()

def update_last_online(user_id: int):
    """Update user's last online timestamp"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_online = CURRENT_TIMESTAMP WHERE id = %s",
            (user_id,)
        )
        conn.commit()

# ============== Auth Endpoints ==============

@app.post("/register")
async def register(user: UserRegister):
    """Register a new user"""
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(user.username) > 20:
        raise HTTPException(status_code=400, detail="Username must be 20 characters or less")
    if len(user.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    
    # Check for valid characters
    if not user.username.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, and underscores")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        password_hash = hash_password(user.password)
        display_name = user.display_name or user.username
        token = generate_token()
        
        cursor.execute(
            """INSERT INTO users (username, password_hash, display_name, session_token, is_online)
               VALUES (%s, %s, %s, %s, 1) RETURNING id""",
            (user.username, password_hash, display_name, token)
        )
        user_id = cursor.fetchone()["id"]
        conn.commit()
        
    return {
        "success": True,
        "message": "Account created successfully!",
        "token": token,
        "user": {
            "id": user_id,
            "username": user.username,
            "display_name": display_name
        }
    }

@app.post("/login")
async def login(user: UserLogin):
    """Login and get session token"""
    with get_db() as conn:
        cursor = conn.cursor()
        password_hash = hash_password(user.password)
        
        cursor.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(%s) AND password_hash = %s",
            (user.username, password_hash)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Generate new token and set online
        token = generate_token()
        cursor.execute(
            """UPDATE users SET session_token = %s, is_online = 1, last_online = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (token, row["id"])
        )
        conn.commit()
        
    return {
        "success": True,
        "message": "Login successful!",
        "token": token,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"]
        }
    }

@app.post("/logout")
async def logout(req: TokenRequest):
    """Logout and invalidate token"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET session_token = NULL, is_online = 0 WHERE id = %s",
            (user["id"],)
        )
        conn.commit()
    
    return {"success": True, "message": "Logged out"}

@app.post("/validate")
async def validate_token(req: TokenRequest):
    """Validate session token and get user info"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    update_last_online(user["id"])
    
    return {
        "valid": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"]
        }
    }

@app.post("/heartbeat")
async def heartbeat(req: TokenRequest):
    """Keep-alive to maintain online status"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_online = 1, last_online = CURRENT_TIMESTAMP WHERE id = %s",
            (user["id"],)
        )
        conn.commit()
    
    return {"success": True}

# ============== Friend Endpoints ==============

@app.post("/friends/add")
async def send_friend_request(req: FriendRequest):
    """Send a friend request"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find target user
        cursor.execute(
            "SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        target = cursor.fetchone()
        
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        
        if target["id"] == user["id"]:
            raise HTTPException(status_code=400, detail="Cannot add yourself as friend")
        
        # Check if already friends or pending
        cursor.execute(
            """SELECT * FROM friends 
               WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)""",
            (user["id"], target["id"], target["id"], user["id"])
        )
        existing = cursor.fetchone()
        
        if existing:
            if existing["status"] == "accepted":
                raise HTTPException(status_code=400, detail="Already friends")
            elif existing["user_id"] == user["id"]:
                raise HTTPException(status_code=400, detail="Friend request already sent")
            else:
                raise HTTPException(status_code=400, detail="This user already sent you a request")
        
        # Create friend request
        cursor.execute(
            "INSERT INTO friends (user_id, friend_id, status) VALUES (%s, %s, 'pending')",
            (user["id"], target["id"])
        )
        conn.commit()
    
    return {"success": True, "message": f"Friend request sent to {target['username']}"}

@app.post("/friends/accept")
async def accept_friend_request(req: FriendRequest):
    """Accept a friend request"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find the sender
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        sender = cursor.fetchone()
        
        if not sender:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find pending request FROM them TO us
        cursor.execute(
            """UPDATE friends SET status = 'accepted'
               WHERE user_id = %s AND friend_id = %s AND status = 'pending'""",
            (sender["id"], user["id"])
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="No pending request from this user")
        
        conn.commit()
    
    return {"success": True, "message": f"You are now friends with {req.target_username}"}

@app.post("/friends/decline")
async def decline_friend_request(req: FriendRequest):
    """Decline a friend request"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        sender = cursor.fetchone()
        
        if not sender:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute(
            """DELETE FROM friends
               WHERE user_id = %s AND friend_id = %s AND status = 'pending'""",
            (sender["id"], user["id"])
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="No pending request from this user")
        
        conn.commit()
    
    return {"success": True, "message": "Friend request declined"}

@app.post("/friends/remove")
async def remove_friend(req: FriendRequest):
    """Remove a friend"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        friend = cursor.fetchone()
        
        if not friend:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove friendship (either direction)
        cursor.execute(
            """DELETE FROM friends
               WHERE ((user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s))
               AND status = 'accepted'""",
            (user["id"], friend["id"], friend["id"], user["id"])
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Not friends with this user")
        
        conn.commit()
    
    return {"success": True, "message": f"Removed {req.target_username} from friends"}

@app.post("/friends/cancel")
async def cancel_friend_request(req: FriendRequest):
    """Cancel a sent friend request"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        target = cursor.fetchone()
        
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute(
            """DELETE FROM friends
               WHERE user_id = %s AND friend_id = %s AND status = 'pending'""",
            (user["id"], target["id"])
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="No pending request to this user")
        
        conn.commit()
    
    return {"success": True, "message": "Friend request cancelled"}

@app.post("/friends/list")
async def get_friends(req: TokenRequest):
    """Get all friends"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get accepted friends (both directions)
        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.is_online, u.last_online, 'accepted' as status
            FROM users u
            JOIN friends f ON (
                (f.user_id = %s AND f.friend_id = u.id) OR 
                (f.friend_id = %s AND f.user_id = u.id)
            )
            WHERE f.status = 'accepted'
            ORDER BY u.is_online DESC, u.username ASC
        """, (user["id"], user["id"]))
        
        friends = []
        for row in cursor.fetchall():
            friends.append({
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "is_online": bool(row["is_online"]),
                "last_online": row["last_online"],
                "status": "accepted"
            })
    
    return {"friends": friends}

@app.post("/friends/pending")
async def get_pending_requests(req: TokenRequest):
    """Get pending friend requests (received)"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Requests received (others sent to us)
        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.is_online, f.created_at
            FROM users u
            JOIN friends f ON f.user_id = u.id
            WHERE f.friend_id = %s AND f.status = 'pending'
            ORDER BY f.created_at DESC
        """, (user["id"],))
        
        incoming = []
        for row in cursor.fetchall():
            incoming.append({
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "is_online": bool(row["is_online"]),
                "sent_at": row["created_at"]
            })
        
        # Requests sent (we sent to others)
        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.is_online, f.created_at
            FROM users u
            JOIN friends f ON f.friend_id = u.id
            WHERE f.user_id = %s AND f.status = 'pending'
            ORDER BY f.created_at DESC
        """, (user["id"],))
        
        outgoing = []
        for row in cursor.fetchall():
            outgoing.append({
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "is_online": bool(row["is_online"]),
                "sent_at": row["created_at"]
            })
    
    return {"incoming": incoming, "outgoing": outgoing}

@app.get("/users/search/{query}")
async def search_users(query: str, token: str):
    """Search for users by username"""
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if len(query) < 2:
        return {"users": []}
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, display_name, is_online
            FROM users
            WHERE username LIKE %s AND id != %s
            LIMIT 10
        """, (f"%{query}%", user["id"]))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "is_online": bool(row["is_online"])
            })
    
    return {"users": users}

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as online FROM users WHERE is_online = 1")
        online = cursor.fetchone()["online"]
    
    return {
        "total_users": total,
        "online_users": online,
        "server_version": "1.0.0"
    }

# ============== Chat System ==============

@app.post("/chat/send")
async def send_message(req: SendMessage):
    """Send a message to a friend"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if len(req.message) > 1000:
        raise HTTPException(status_code=400, detail="Message too long (max 1000 chars)")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find target user
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.to_username,)
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if they are friends
        cursor.execute("""
            SELECT * FROM friends 
            WHERE ((user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s))
            AND status = 'accepted'
        """, (user["id"], target["id"], target["id"], user["id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="You can only message friends")
        
        # Insert message
        cursor.execute(
            """INSERT INTO messages (sender_id, receiver_id, message)
               VALUES (%s, %s, %s) RETURNING id, created_at""",
            (user["id"], target["id"], req.message.strip())
        )
        msg = cursor.fetchone()
        conn.commit()
    
    return {
        "success": True,
        "message_id": msg["id"],
        "sent_at": str(msg["created_at"])
    }

@app.post("/chat/history")
async def get_chat_history(req: GetMessages):
    """Get chat history with a friend"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find target user
        cursor.execute(
            "SELECT id, username, display_name FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.with_username,)
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get messages between the two users
        cursor.execute("""
            SELECT m.id, m.sender_id, m.receiver_id, m.message, m.created_at, m.is_read,
                   u.username as sender_username
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = %s AND m.receiver_id = %s) 
               OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.created_at DESC
            LIMIT %s
        """, (user["id"], target["id"], target["id"], user["id"], req.limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row["id"],
                "sender_username": row["sender_username"],
                "message": row["message"],
                "sent_at": str(row["created_at"]),
                "is_mine": row["sender_id"] == user["id"],
                "is_read": bool(row["is_read"])
            })
        
        # Mark messages as read
        cursor.execute("""
            UPDATE messages SET is_read = 1
            WHERE sender_id = %s AND receiver_id = %s AND is_read = 0
        """, (target["id"], user["id"]))
        conn.commit()
    
    # Reverse to show oldest first
    messages.reverse()
    
    return {
        "with_user": {
            "username": target["username"],
            "display_name": target["display_name"]
        },
        "messages": messages
    }

@app.post("/chat/unread")
async def get_unread_count(req: TokenRequest):
    """Get unread message counts"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get unread counts per sender
        cursor.execute("""
            SELECT u.username, COUNT(*) as count
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id = %s AND m.is_read = 0
            GROUP BY u.username
        """, (user["id"],))
        
        unread = {}
        total = 0
        for row in cursor.fetchall():
            unread[row["username"]] = row["count"]
            total += row["count"]
    
    return {"unread": unread, "total": total}

# ============== Voice Call System ==============

@app.post("/voice/call")
async def start_voice_call(req: VoiceCallRequest):
    """Start a voice call with a friend"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find target user
        cursor.execute(
            "SELECT id, username, is_online FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not target["is_online"]:
            raise HTTPException(status_code=400, detail="User is offline")
        
        # Check if they are friends
        cursor.execute("""
            SELECT * FROM friends 
            WHERE ((user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s))
            AND status = 'accepted'
        """, (user["id"], target["id"], target["id"], user["id"]))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="You can only call friends")
        
        # Create call session
        cursor.execute(
            """INSERT INTO voice_calls (caller_id, receiver_id, status)
               VALUES (%s, %s, 'pending') RETURNING id""",
            (user["id"], target["id"])
        )
        call_id = cursor.fetchone()["id"]
        conn.commit()
    
    return {
        "success": True,
        "call_id": call_id,
        "status": "calling",
        "target": target["username"]
    }

@app.post("/voice/answer")
async def answer_voice_call(req: VoiceCallRequest):
    """Answer an incoming voice call"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find caller
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        caller = cursor.fetchone()
        if not caller:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find and update pending call
        cursor.execute("""
            UPDATE voice_calls SET status = 'active'
            WHERE caller_id = %s AND receiver_id = %s AND status = 'pending'
            RETURNING id
        """, (caller["id"], user["id"]))
        
        call = cursor.fetchone()
        if not call:
            raise HTTPException(status_code=404, detail="No pending call from this user")
        
        conn.commit()
    
    return {"success": True, "call_id": call["id"], "status": "connected"}

@app.post("/voice/end")
async def end_voice_call(req: VoiceCallRequest):
    """End a voice call"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find other user
        cursor.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(%s)",
            (req.target_username,)
        )
        other = cursor.fetchone()
        if not other:
            raise HTTPException(status_code=404, detail="User not found")
        
        # End any active call between them
        cursor.execute("""
            UPDATE voice_calls SET status = 'ended', ended_at = CURRENT_TIMESTAMP
            WHERE ((caller_id = %s AND receiver_id = %s) OR (caller_id = %s AND receiver_id = %s))
            AND status IN ('pending', 'active')
        """, (user["id"], other["id"], other["id"], user["id"]))
        
        conn.commit()
    
    return {"success": True, "status": "ended"}

@app.post("/voice/check")
async def check_incoming_call(req: TokenRequest):
    """Check for incoming calls"""
    user = get_user_by_token(req.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check for pending incoming calls
        cursor.execute("""
            SELECT vc.id, vc.status, u.username, u.display_name
            FROM voice_calls vc
            JOIN users u ON vc.caller_id = u.id
            WHERE vc.receiver_id = %s AND vc.status = 'pending'
            ORDER BY vc.created_at DESC
            LIMIT 1
        """, (user["id"],))
        
        call = cursor.fetchone()
        if call:
            return {
                "incoming_call": True,
                "call_id": call["id"],
                "from_username": call["username"],
                "from_display_name": call["display_name"]
            }
    
    return {"incoming_call": False}

# ============== Update System ==============

# Current launcher version - UPDATE THIS when you release new versions!
LAUNCHER_VERSION = "2.6.8"
LAUNCHER_DOWNLOAD_URL = "https://raw.githubusercontent.com/m7md75/Server/main/launcher.py"
UPDATE_NOTES = "New! Chat & Voice with friends. See online players count. Fixed friends online status."

@app.get("/update/check")
async def check_update():
    """Check for launcher updates"""
    return {
        "latest_version": LAUNCHER_VERSION,
        "download_url": LAUNCHER_DOWNLOAD_URL,
        "update_notes": UPDATE_NOTES,
        "required": False
    }

@app.post("/update/check")
async def check_update_post(data: dict = None):
    """Check for launcher updates (POST version)"""
    current_version = data.get("version", "0.0.0") if data else "0.0.0"
    needs_update = current_version != LAUNCHER_VERSION
    
    return {
        "latest_version": LAUNCHER_VERSION,
        "current_version": current_version,
        "update_available": needs_update,
        "download_url": LAUNCHER_DOWNLOAD_URL,
        "update_notes": UPDATE_NOTES,
        "required": False
    }

# ============== Startup ==============

@app.on_event("startup")
async def startup():
    init_db()
    print("[SERVER] WeJZ Online Server started on http://localhost:8000")

if __name__ == "__main__":
    print(f"[SERVER] Starting on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

