"""
WeJZ Client
Minecraft Launcher with Fabric Support, Profiles, and Mods
"""

# ============== VERSION - Update this for new releases ==============
LAUNCHER_VERSION = "2.5.0"
# ====================================================================

# Supported Minecraft versions
MC_VERSIONS = [
    "1.21.4", "1.21.3", "1.21.1", "1.21",
    "1.20.6", "1.20.4", "1.20.2", "1.20.1", "1.20",
    "1.19.4", "1.19.3", "1.19.2", "1.19",
    "1.18.2", "1.18.1", "1.18",
    "1.17.1", "1.17",
    "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1",
    "1.15.2", "1.14.4", "1.12.2", "1.8.9", "1.7.10"
]

# Mod loaders
MOD_LOADERS = ["vanilla", "fabric", "forge"]

# Fabric API - auto-install for Fabric profiles
FABRIC_API_PROJECT = "fabric-api"

import customtkinter as ctk
import os
import json
import threading
import time
import subprocess
from pathlib import Path
import requests
import hashlib
import platform
import zipfile
import uuid
from datetime import datetime
import random
import tkinter as tk
from tkinter import font as tkfont

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# Matrix Colors
COLORS = {
    "bg_dark": "#000000",
    "bg_medium": "#0a0a0a",
    "bg_light": "#0d1a0d",
    "bg_card": "#001100",
    "bg_card_hover": "#002200",
    "accent": "#00ff00",
    "accent_dim": "#00aa00",
    "accent_hover": "#00cc00",
    "accent2": "#00ff66",
    "text": "#00ff00",
    "text2": "#00bb00",
    "text3": "#007700",
    "border": "#003300",
    "success": "#00ff00",
    "error": "#ff0000",
    "warning": "#ff9900",
    "glow": "#00ff00",
    "terminal_green": "#33ff33",
}

# Font Configuration - Load Minecraft Ten from local TTF file
FONT_FALLBACK = "Consolas"
FONT_FAMILY = FONT_FALLBACK  # Will be updated if font loads successfully

def load_custom_font():
    """Load Minecraft Ten font from local TTF file"""
    global FONT_FAMILY
    
    # Try to find the font file in the same directory as the script
    script_dir = Path(__file__).parent
    font_files = [
        script_dir / "Minecraft.ttf",
        script_dir / "mc-ten-lowercase-alt.ttf",
        script_dir / "MinecraftTen-VGORe.ttf",
    ]
    
    font_path = None
    for f in font_files:
        if f.exists():
            font_path = f
            break
    
    if not font_path:
        print("[FONT] Minecraft Ten not found, using Consolas")
        return False
    
    try:
        if platform.system() == "Windows":
            # Windows: Use GDI to load font temporarily
            import ctypes
            from ctypes import wintypes
            
            # AddFontResourceExW flags
            FR_PRIVATE = 0x10
            
            gdi32 = ctypes.windll.gdi32
            # Add font to system temporarily (private to this app)
            result = gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0)
            
            if result > 0:
                # Set font family name based on which file was loaded
                if "Minecraft.ttf" in str(font_path):
                    FONT_FAMILY = "Minecraft"
                else:
                    FONT_FAMILY = "Minecraft Ten"
                print(f"[FONT] Loaded: {font_path.name} as '{FONT_FAMILY}'")
                return True
            else:
                print("[FONT] Failed to load font via GDI")
                return False
        else:
            # Linux/Mac: Try pyglet or just use the font name
            # Font needs to be installed system-wide on these platforms
            FONT_FAMILY = "Minecraft Ten"
            return True
            
    except Exception as e:
        print(f"[FONT] Error loading font: {e}")
        return False

# Try to load the custom font
load_custom_font()

def get_font(size=14, weight="normal"):
    """Get font with fallback support"""
    return (FONT_FAMILY, size, weight)

# API URLs
MODRINTH_API = "https://api.modrinth.com/v2"
CURSEFORGE_API = "https://api.curseforge.com/v1"
CURSEFORGE_KEY = "$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm"  # Public eternal API key
VERSION_MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"
FABRIC_META = "https://meta.fabricmc.net/v2"

# CurseForge constants
CF_GAME_ID = 432  # Minecraft
CF_MOD_CLASS = 6  # Mods class

# Featured mods
MODS_DB = {
    "performance": [
        {"name": "Sodium", "slug": "sodium", "icon": "[>]", "desc": "Modern rendering engine"},
        {"name": "Lithium", "slug": "lithium", "icon": "[+]", "desc": "General optimizations"},
        {"name": "Starlight", "slug": "starlight", "icon": "[*]", "desc": "Light engine rewrite"},
        {"name": "FerriteCore", "slug": "ferrite-core", "icon": "[#]", "desc": "Memory optimization"},
        {"name": "LazyDFU", "slug": "lazydfu", "icon": "[~]", "desc": "Faster startup"},
        {"name": "Krypton", "slug": "krypton", "icon": "[@]", "desc": "Network optimization"},
        {"name": "ImmediatelyFast", "slug": "immediatelyfast", "icon": "[!]", "desc": "Rendering speedup"},
        {"name": "ModernFix", "slug": "modernfix", "icon": "[%]", "desc": "All-in-one fixes"},
    ],
    "visual": [
        {"name": "Iris Shaders", "slug": "iris", "icon": "[=]", "desc": "Shader support"},
        {"name": "LambDynamicLights", "slug": "lambdynamiclights", "icon": "[o]", "desc": "Dynamic lights"},
        {"name": "Continuity", "slug": "continuity", "icon": "[|]", "desc": "Connected textures"},
        {"name": "Falling Leaves", "slug": "fallingleaves", "icon": "[v]", "desc": "Leaf particles"},
        {"name": "Visuality", "slug": "visuality", "icon": "[.]", "desc": "Visual effects"},
        {"name": "NotEnoughAnimations", "slug": "not-enough-animations", "icon": "[^]", "desc": "More animations"},
    ],
    "utility": [
        {"name": "Mod Menu", "slug": "modmenu", "icon": "[M]", "desc": "Mod list menu"},
        {"name": "Fabric API", "slug": "fabric-api", "icon": "[F]", "desc": "Required API"},
        {"name": "Roughly Enough Items", "slug": "roughly-enough-items", "icon": "[R]", "desc": "Recipe viewer"},
        {"name": "AppleSkin", "slug": "appleskin", "icon": "[A]", "desc": "Food info"},
        {"name": "Xaero's Minimap", "slug": "xaeros-minimap", "icon": "[X]", "desc": "Minimap"},
        {"name": "Jade", "slug": "jade", "icon": "[J]", "desc": "Block info"},
        {"name": "Cloth Config", "slug": "cloth-config", "icon": "[C]", "desc": "Config library"},
    ],
    "gameplay": [
        {"name": "Origins", "slug": "origins", "icon": "[O]", "desc": "Choose abilities"},
        {"name": "Traverse", "slug": "traverse", "icon": "[T]", "desc": "New biomes"},
        {"name": "BetterEnd", "slug": "betterend", "icon": "[E]", "desc": "End overhaul"},
        {"name": "BetterNether", "slug": "betternether", "icon": "[N]", "desc": "Nether overhaul"},
        {"name": "Supplementaries", "slug": "supplementaries", "icon": "[S]", "desc": "Decorations"},
    ],
}


class ModrinthAPI:
    @staticmethod
    def search(query, version, limit=20):
        try:
            params = {
                "query": query,
                "limit": limit,
                "facets": json.dumps([["project_type:mod"], [f"versions:{version}"], ["categories:fabric"]])
            }
            r = requests.get(f"{MODRINTH_API}/search", params=params, timeout=10)
            return r.json().get("hits", []) if r.ok else []
        except:
            return []

    @staticmethod
    def get_versions(slug, mc_version):
        try:
            params = {"loaders": '["fabric"]', "game_versions": f'["{mc_version}"]'}
            r = requests.get(f"{MODRINTH_API}/project/{slug}/version", params=params, timeout=10)
            return r.json() if r.ok else []
        except:
            return []

    @staticmethod
    def download(url, path):
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(url, stream=True, timeout=60)
            if r.ok:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                return True
        except:
            pass
        return False


class CurseForgeAPI:
    """CurseForge API for downloading mods"""
    
    @staticmethod
    def _headers():
        return {"x-api-key": CURSEFORGE_KEY, "Accept": "application/json"}
    
    @staticmethod
    def search(query, mc_version, loader="fabric", limit=20):
        """Search for mods on CurseForge"""
        try:
            # Map loader names
            loader_type = 4 if loader == "fabric" else 1  # 1=Forge, 4=Fabric
            
            params = {
                "gameId": CF_GAME_ID,
                "classId": CF_MOD_CLASS,
                "searchFilter": query,
                "gameVersion": mc_version,
                "modLoaderType": loader_type,
                "pageSize": limit,
                "sortField": 2,  # Popularity
                "sortOrder": "desc"
            }
            r = requests.get(f"{CURSEFORGE_API}/mods/search", 
                           params=params, headers=CurseForgeAPI._headers(), timeout=15)
            if r.ok:
                data = r.json().get("data", [])
                # Convert to standard format
                results = []
                for mod in data:
                    results.append({
                        "id": mod.get("id"),
                        "name": mod.get("name"),
                        "slug": mod.get("slug"),
                        "description": mod.get("summary", "")[:100],
                        "downloads": mod.get("downloadCount", 0),
                        "icon_url": mod.get("logo", {}).get("thumbnailUrl", ""),
                        "source": "curseforge"
                    })
                return results
            return []
        except Exception as e:
            print(f"[CF] Search error: {e}")
            return []
    
    @staticmethod
    def get_download_url(mod_id, mc_version, loader="fabric"):
        """Get download URL for a mod"""
        try:
            # Get mod files
            r = requests.get(f"{CURSEFORGE_API}/mods/{mod_id}/files",
                           headers=CurseForgeAPI._headers(), timeout=15)
            if not r.ok:
                return None, None
            
            files = r.json().get("data", [])
            loader_type = 4 if loader == "fabric" else 1
            
            # Find compatible file
            for f in files:
                game_versions = f.get("gameVersions", [])
                if mc_version in game_versions:
                    # Check loader compatibility
                    if loader == "fabric" and "Fabric" in game_versions:
                        return f.get("downloadUrl"), f.get("fileName")
                    elif loader == "forge" and "Forge" in game_versions:
                        return f.get("downloadUrl"), f.get("fileName")
                    elif loader == "vanilla":
                        return f.get("downloadUrl"), f.get("fileName")
            
            # Fallback: get latest file for version
            for f in files:
                if mc_version in f.get("gameVersions", []):
                    return f.get("downloadUrl"), f.get("fileName")
            
            return None, None
        except Exception as e:
            print(f"[CF] Get download error: {e}")
            return None, None
    
    @staticmethod
    def get_popular(mc_version, loader="fabric", limit=20):
        """Get popular mods"""
        return CurseForgeAPI.search("", mc_version, loader, limit)
    
    @staticmethod
    def download(url, path):
        """Download a file"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(url, stream=True, headers=CurseForgeAPI._headers(), timeout=120)
            if r.ok:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                return True
        except Exception as e:
            print(f"[CF] Download error: {e}")
        return False


# Server URL - Change this to your server's address
WEJZ_SERVER = "https://bright-giraffe-wejz-69e0bacd.koyeb.app"


class WeJZOnline:
    """Client for WeJZ Online services - User accounts and friends"""
    
    def __init__(self, server_url=WEJZ_SERVER):
        self.server = server_url
        self.token = None
        self.user = None
        self._session_file = Path.home() / ".wejzclient" / "session.json"
    
    def _request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to server"""
        try:
            url = f"{self.server}{endpoint}"
            if method == "GET":
                r = requests.get(url, params=params, timeout=10)
            else:
                r = requests.post(url, json=data, timeout=10)
            
            if r.ok:
                return {"success": True, "data": r.json()}
            else:
                error = r.json().get("detail", "Unknown error")
                return {"success": False, "error": error}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to server"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_session(self):
        """Save session to file - preserves login across updates"""
        if self.token and self.user:
            try:
                # Ensure directory exists
                session_dir = self._session_file.parent
                session_dir.mkdir(parents=True, exist_ok=True)
                
                session_data = {
                    "token": self.token, 
                    "user": self.user,
                    "version": LAUNCHER_VERSION,
                    "saved_at": time.time()
                }
                
                # Write to temp file first, then rename (atomic)
                temp_file = self._session_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2)
                
                # Replace original file
                if self._session_file.exists():
                    self._session_file.unlink()
                temp_file.rename(self._session_file)
                
                print(f"[SESSION] Saved to: {self._session_file}")
            except Exception as e:
                print(f"[SESSION] Failed to save: {e}")
                import traceback
                traceback.print_exc()
    
    def load_session(self):
        """Load saved session - works across updates"""
        try:
            print(f"[SESSION] Looking for: {self._session_file}")
            if self._session_file.exists():
                with open(self._session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.token = data.get("token")
                    self.user = data.get("user")
                    saved_version = data.get("version", "unknown")
                    if self.token and self.user:
                        print(f"[SESSION] Loaded session for {self.user.get('username', 'unknown')} (saved by v{saved_version})")
                        return True
                    else:
                        print("[SESSION] Session file exists but missing token/user")
            else:
                print("[SESSION] No session file found")
        except Exception as e:
            print(f"[SESSION] Failed to load: {e}")
            import traceback
            traceback.print_exc()
        return False
    
    def clear_session(self):
        """Clear saved session"""
        self.token = None
        self.user = None
        try:
            if self._session_file.exists():
                self._session_file.unlink()
                print("[SESSION] Cleared session")
        except Exception as e:
            print(f"[SESSION] Failed to clear: {e}")
    
    def register(self, username, password, display_name=None):
        """Register new account"""
        result = self._request("POST", "/register", {
            "username": username,
            "password": password,
            "display_name": display_name
        })
        
        if result["success"]:
            data = result["data"]
            self.token = data["token"]
            self.user = data["user"]
            self.save_session()
        
        return result
    
    def login(self, username, password):
        """Login to account"""
        result = self._request("POST", "/login", {
            "username": username,
            "password": password
        })
        
        if result["success"]:
            data = result["data"]
            self.token = data["token"]
            self.user = data["user"]
            self.save_session()
        
        return result
    
    def logout(self):
        """Logout and clear session"""
        if self.token:
            self._request("POST", "/logout", {"token": self.token})
        self.clear_session()
    
    def validate_session(self):
        """Check if current session is valid - doesn't clear on failure"""
        if not self.token:
            return False
        
        result = self._request("POST", "/validate", {"token": self.token})
        if result["success"]:
            self.user = result["data"]["user"]
            # Re-save session to ensure it's up to date
            self.save_session()
            return True
        else:
            # Don't clear session - might be network issue
            # User can manually logout if needed
            print(f"[SESSION] Validation failed: {result.get('error', 'unknown')}")
            return False
    
    def heartbeat(self):
        """Send heartbeat to maintain online status"""
        if self.token:
            self._request("POST", "/heartbeat", {"token": self.token})
    
    def get_friends(self):
        """Get friends list"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/list", {"token": self.token})
    
    def get_pending_requests(self):
        """Get pending friend requests"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/pending", {"token": self.token})
    
    def add_friend(self, username):
        """Send friend request"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/add", {
            "token": self.token,
            "target_username": username
        })
    
    def accept_friend(self, username):
        """Accept friend request"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/accept", {
            "token": self.token,
            "target_username": username
        })
    
    def decline_friend(self, username):
        """Decline friend request"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/decline", {
            "token": self.token,
            "target_username": username
        })
    
    def remove_friend(self, username):
        """Remove friend"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/remove", {
            "token": self.token,
            "target_username": username
        })
    
    def cancel_request(self, username):
        """Cancel sent friend request"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("POST", "/friends/cancel", {
            "token": self.token,
            "target_username": username
        })
    
    def search_users(self, query):
        """Search for users"""
        if not self.token:
            return {"success": False, "error": "Not logged in"}
        return self._request("GET", f"/users/search/{query}", params={"token": self.token})
    
    def get_stats(self):
        """Get server stats"""
        return self._request("GET", "/stats")
    
    def check_update(self, current_version):
        """Check if launcher update is available"""
        result = self._request("POST", "/update/check", {"version": current_version})
        return result
    
    def download_update(self, url):
        """Download new launcher version"""
        try:
            r = requests.get(url, timeout=30)
            if r.ok:
                return {"success": True, "content": r.text}
            return {"success": False, "error": "Download failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class GameDownloader:
    def __init__(self, game_dir, callback=None):
        self.game_dir = Path(game_dir)
        self.callback = callback
        self.versions_dir = self.game_dir / "versions"
        self.libs_dir = self.game_dir / "libraries"
        self.assets_dir = self.game_dir / "assets"
        self.natives_dir = self.game_dir / "natives"
        self.mods_dir = self.game_dir / "mods"
        
        for d in [self.versions_dir, self.libs_dir, self.assets_dir, self.natives_dir, self.mods_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def progress(self, msg, val=None):
        if self.callback:
            self.callback(msg, val)

    def download_file(self, url, path, sha1=None):
        path = Path(path)
        if path.exists() and sha1:
            with open(path, 'rb') as f:
                if hashlib.sha1(f.read()).hexdigest() == sha1:
                    return True
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = requests.get(url, stream=True, timeout=30)
            if r.ok:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                return True
        except Exception as e:
            print(f"Download failed: {url} - {e}")
        return False

    def get_os(self):
        s = platform.system().lower()
        return 'windows' if s == 'windows' else 'osx' if s == 'darwin' else 'linux'

    def check_lib_rules(self, lib):
        if 'rules' not in lib:
            return True
        os_name = self.get_os()
        action = 'disallow'
        for rule in lib['rules']:
            if 'os' in rule:
                if rule['os'].get('name') == os_name:
                    action = rule['action']
            else:
                action = rule['action']
        return action == 'allow'

    def download_vanilla(self, version_id):
        self.progress("[INIT] Fetching manifest...", 0.02)
        try:
            r = requests.get(VERSION_MANIFEST, timeout=10)
            manifest = r.json()
        except:
            return None

        version_url = None
        for v in manifest['versions']:
            if v['id'] == version_id:
                version_url = v['url']
                break
        
        if not version_url:
            return None

        self.progress("[DOWNLOAD] Version data...", 0.05)
        try:
            r = requests.get(version_url, timeout=10)
            version_info = r.json()
        except:
            return None

        ver_dir = self.versions_dir / version_id
        ver_dir.mkdir(parents=True, exist_ok=True)
        with open(ver_dir / f"{version_id}.json", 'w') as f:
            json.dump(version_info, f)

        self.progress("[DOWNLOAD] Client JAR...", 0.1)
        client = version_info['downloads']['client']
        if not self.download_file(client['url'], ver_dir / f"{version_id}.jar", client.get('sha1')):
            return None

        libs = version_info.get('libraries', [])
        for i, lib in enumerate(libs):
            if not self.check_lib_rules(lib):
                continue
            
            prog = 0.1 + 0.5 * (i / len(libs))
            name = lib.get('name', '').split(':')[-1][:25]
            self.progress(f"[LIB] {name}", prog)

            if 'downloads' in lib:
                art = lib['downloads'].get('artifact')
                if art:
                    self.download_file(art['url'], self.libs_dir / art['path'], art.get('sha1'))

                classifiers = lib['downloads'].get('classifiers', {})
                native_key = f"natives-{self.get_os()}"
                if native_key in classifiers:
                    nat = classifiers[native_key]
                    nat_path = self.libs_dir / nat['path']
                    if self.download_file(nat['url'], nat_path, nat.get('sha1')):
                        self.extract_natives(nat_path, version_id)

        self.progress("[ASSETS] Downloading...", 0.65)
        asset_index = version_info.get('assetIndex', {})
        if asset_index:
            idx_path = self.assets_dir / "indexes" / f"{asset_index['id']}.json"
            self.download_file(asset_index['url'], idx_path, asset_index.get('sha1'))
            self.download_assets(idx_path)

        self.progress("[OK] Vanilla ready!", 0.7)
        return version_info

    def extract_natives(self, jar_path, version_id):
        nat_dir = self.natives_dir / version_id
        nat_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(jar_path) as z:
                for f in z.namelist():
                    if f.endswith(('.dll', '.so', '.dylib')):
                        z.extract(f, nat_dir)
        except:
            pass

    def download_assets(self, idx_path):
        if not Path(idx_path).exists():
            return
        try:
            with open(idx_path) as f:
                idx = json.load(f)
            objs = idx.get('objects', {})
            count = 0
            for name, info in objs.items():
                if count > 100:
                    break
                h = info['hash']
                p = h[:2]
                asset_path = self.assets_dir / "objects" / p / h
                if not asset_path.exists():
                    self.download_file(f"https://resources.download.minecraft.net/{p}/{h}", asset_path)
                count += 1
        except:
            pass

    def install_fabric(self, mc_version):
        self.progress("[FABRIC] Installing loader...", 0.72)
        try:
            r = requests.get(f"{FABRIC_META}/versions/loader", timeout=10)
            loaders = r.json()
            loader_ver = loaders[0]['version']

            r = requests.get(f"{FABRIC_META}/versions/loader/{mc_version}/{loader_ver}/profile/json", timeout=10)
            if not r.ok:
                return None
            profile = r.json()

            ver_id = profile['id']
            ver_dir = self.versions_dir / ver_id
            ver_dir.mkdir(parents=True, exist_ok=True)
            with open(ver_dir / f"{ver_id}.json", 'w') as f:
                json.dump(profile, f)

            libs = profile.get('libraries', [])
            for i, lib in enumerate(libs):
                prog = 0.72 + 0.18 * (i / len(libs))
                name = lib.get('name', '').split(':')[-1][:20]
                self.progress(f"[FABRIC] {name}", prog)

                if 'url' in lib:
                    parts = lib['name'].split(':')
                    if len(parts) >= 3:
                        group = parts[0].replace('.', '/')
                        artifact = parts[1]
                        version = parts[2]
                        jar = f"{artifact}-{version}.jar"
                        jar_path = f"{group}/{artifact}/{version}/{jar}"
                        url = lib['url'] + jar_path
                        dest = self.libs_dir / jar_path
                        if not dest.exists():
                            self.download_file(url, dest)

            self.progress("[OK] Fabric installed!", 0.9)
            return profile
        except Exception as e:
            print(f"Fabric install error: {e}")
            return None

    def install_fabric_api(self, mc_version):
        """Download and install Fabric API for the given MC version"""
        self.progress("[FABRIC API] Downloading...", 0.91)
        try:
            # Get Fabric API versions from Modrinth
            url = f"{MODRINTH_API}/project/{FABRIC_API_PROJECT}/version"
            r = requests.get(url, timeout=15)
            if not r.ok:
                print(f"[FABRIC API] Failed to fetch versions: {r.status_code}")
                return False
            
            versions = r.json()
            
            # Find version compatible with our MC version
            for ver in versions:
                game_versions = ver.get('game_versions', [])
                loaders = ver.get('loaders', [])
                
                if mc_version in game_versions and 'fabric' in loaders:
                    # Found compatible version
                    files = ver.get('files', [])
                    if files:
                        file_info = files[0]
                        file_url = file_info['url']
                        file_name = file_info['filename']
                        
                        # Download to mods folder
                        dest = self.mods_dir / file_name
                        if not dest.exists():
                            self.progress(f"[FABRIC API] {file_name[:30]}...", 0.93)
                            if self.download_file(file_url, dest):
                                self.progress("[OK] Fabric API installed!", 0.95)
                                return True
                        else:
                            self.progress("[OK] Fabric API already installed!", 0.95)
                            return True
            
            print(f"[FABRIC API] No compatible version found for MC {mc_version}")
            return False
        except Exception as e:
            print(f"[FABRIC API] Error: {e}")
            return False

    def build_classpath(self, version_info, fabric_profile=None):
        cp = []
        
        if fabric_profile:
            for lib in fabric_profile.get('libraries', []):
                parts = lib['name'].split(':')
                if len(parts) >= 3:
                    group = parts[0].replace('.', '/')
                    artifact = parts[1]
                    version = parts[2]
                    jar_path = self.libs_dir / group / artifact / version / f"{artifact}-{version}.jar"
                    if jar_path.exists():
                        cp.append(str(jar_path))

        for lib in version_info.get('libraries', []):
            if not self.check_lib_rules(lib):
                continue
            if 'downloads' in lib:
                art = lib['downloads'].get('artifact')
                if art:
                    path = self.libs_dir / art['path']
                    if path.exists():
                        cp.append(str(path))

        ver_id = version_info['id']
        client = self.versions_dir / ver_id / f"{ver_id}.jar"
        if client.exists():
            cp.append(str(client))

        return ';'.join(cp) if platform.system() == 'Windows' else ':'.join(cp)

    def get_launch_cmd(self, version_info, username, ram, java_path, fabric_profile=None):
        ver_id = version_info['id']
        natives = self.natives_dir / ver_id
        natives.mkdir(parents=True, exist_ok=True)
        
        cp = self.build_classpath(version_info, fabric_profile)
        
        if fabric_profile:
            main_class = fabric_profile.get('mainClass', 'net.fabricmc.loader.impl.launch.knot.KnotClient')
        else:
            main_class = version_info.get('mainClass', 'net.minecraft.client.main.Main')

        asset_id = version_info.get('assetIndex', {}).get('id', ver_id)

        cmd = [
            java_path,
            f"-Xmx{ram}G",
            f"-Xms{ram // 2}G",
            f"-Djava.library.path={natives}",
            "-Dminecraft.launcher.brand=WeJZClient",
            "-cp", cp,
            main_class,
            "--username", username,
            "--version", ver_id,
            "--gameDir", str(self.game_dir),
            "--assetsDir", str(self.assets_dir),
            "--assetIndex", asset_id,
            "--uuid", str(uuid.uuid4()).replace('-', ''),
            "--accessToken", "0",
            "--userType", "legacy",
        ]
        return cmd


class ProfileManager:
    def __init__(self, data_dir):
        self.file = Path(data_dir) / "profiles.json"
        self.profiles = {}
        self.load()

    def load(self):
        if self.file.exists():
            try:
                with open(self.file) as f:
                    self.profiles = json.load(f)
            except:
                pass
        if not self.profiles:
            self.profiles = {"Default": {"name": "Default", "version": "1.20.4", "loader": "fabric", "mods": [], "ram": 4}}
            self.save()

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file, 'w') as f:
            json.dump(self.profiles, f, indent=2)

    def create(self, name, version, loader):
        if name in self.profiles:
            return False
        self.profiles[name] = {"name": name, "version": version, "loader": loader, "mods": [], "ram": 4}
        self.save()
        return True

    def delete(self, name):
        if name != "Default" and name in self.profiles:
            del self.profiles[name]
            self.save()
            return True
        return False

    def get(self, name):
        return self.profiles.get(name)

    def get_all(self):
        return self.profiles

    def add_mod(self, profile, mod):
        if profile in self.profiles:
            mods = self.profiles[profile]["mods"]
            if not any(m["name"] == mod["name"] for m in mods):
                mods.append(mod)
                self.save()
                return True
        return False

    def remove_mod(self, profile, mod_name):
        if profile in self.profiles:
            self.profiles[profile]["mods"] = [m for m in self.profiles[profile]["mods"] if m["name"] != mod_name]
            self.save()

    def update(self, name, **kwargs):
        if name in self.profiles:
            for k, v in kwargs.items():
                self.profiles[name][k] = v  # Allow adding new keys
            self.save()


# Simple button - no animations for performance
class AnimatedButton(ctk.CTkButton):
    """Simple button (animations removed for performance)"""
    def __init__(self, parent, **kwargs):
        kwargs.pop('glow_color', None)  # Remove unused param
        super().__init__(parent, **kwargs)


# Simple card - no animations for performance  
class AnimatedCard(ctk.CTkFrame):
    """Simple card frame (animations removed for performance)"""
    def __init__(self, parent, **kwargs):
        kwargs.pop('hover_border', None)
        kwargs.pop('hover_fg', None)
        super().__init__(parent, **kwargs)


class TransitionManager:
    """Transitions disabled for performance"""
    
    @staticmethod
    def fade_in_widget(widget, duration=300, delay=0, start_alpha=0.0):
        pass
    
    @staticmethod
    def slide_in_from_right(widget, parent, final_x, duration=300, delay=0):
        pass
    
    @staticmethod
    def slide_in_from_bottom(widget, final_y, start_y_offset=50, duration=250, delay=0):
        pass
    
    @staticmethod
    def stagger_fade_children(parent, delay_between=50, initial_delay=0):
        pass
    
    @staticmethod
    def typing_effect(label, text, delay_per_char=30, callback=None):
        label.configure(text=text)
        if callback:
            callback()
    
    @staticmethod
    def pulse_widget(widget, color1, color2, duration=500, cycles=2):
        pass


class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("[ WEJZ CLIENT ]")
        self.geometry("1300x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1300) // 2
        y = (self.winfo_screenheight() - 800) // 2
        self.geometry(f"1300x800+{x}+{y}")

        # State
        self.current_page = "home"
        self.settings = self.load_settings()
        self.username = self.load_username()
        self.profiles = ProfileManager(self.settings["game_dir"])
        self.current_profile = "Default"
        self.is_launching = False
        self.mod_category = "performance"
        self.search_results = []
        self.transition_alpha = 1.0
        
        # Online features
        self.online = WeJZOnline()
        self.is_logged_in = False
        self.friends_list = []
        self.pending_requests = {"incoming": [], "outgoing": []}
        self.friends_tab = "friends"  # friends, pending, add

        self.build_ui()
        
        # Try to restore session
        self._try_restore_session()
        
        # Start heartbeat timer for online status
        self._start_heartbeat()
        
        # Check for updates
        self._check_for_updates()

    def load_settings(self):
        path = Path("launcher_settings.json")
        default = {"ram": 4, "java": "java", "game_dir": str(Path.home() / ".wejzclient")}
        if path.exists():
            try:
                with open(path) as f:
                    return {**default, **json.load(f)}
            except:
                pass
        return default

    def save_settings(self):
        with open("launcher_settings.json", 'w') as f:
            json.dump(self.settings, f, indent=2)

    def load_username(self):
        path = Path(self.settings["game_dir"]) / "username.txt"
        if path.exists():
            try:
                return path.read_text().strip() or "Player"
            except:
                pass
        return "Player"

    def save_username(self):
        path = Path(self.settings["game_dir"])
        path.mkdir(parents=True, exist_ok=True)
        (path / "username.txt").write_text(self.username)

    def build_ui(self):
        # Main container
        self.container = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.container.pack(fill="both", expand=True)
        
        # Simple dark background (no animation for performance)
        self.overlay = ctk.CTkFrame(self.container, fg_color=COLORS["bg_dark"])
        self.overlay.pack(fill="both", expand=True)

        # Sidebar with terminal style
        sidebar = ctk.CTkFrame(self.overlay, width=100, fg_color=COLORS["bg_medium"], corner_radius=0,
                              border_width=2, border_color=COLORS["border"])
        sidebar.pack(side="left", fill="y", padx=(10, 0), pady=10)
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(pady=20)
        ctk.CTkLabel(logo_frame, text="[W]", font=get_font(24, "bold"), 
                    text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(logo_frame, text="WEJZ", font=get_font(10, "bold"), 
                    text_color=COLORS["text2"]).pack()
        
        # Separator
        ctk.CTkFrame(sidebar, fg_color=COLORS["accent"], height=2).pack(fill="x", padx=15, pady=10)

        # Navigation buttons with terminal style
        self.nav_btns = {}
        nav_items = [
            ("home", "[H]", "HOME"),
            ("profiles", "[P]", "PROFILES"),
            ("play", "[>]", "PLAY"),
            ("mods", "[M]", "MODS"),
            ("friends", "[F]", "FRIENDS"),
            ("settings", "[S]", "SETTINGS")
        ]
        
        for key, icon, label in nav_items:
            btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
            btn_frame.pack(pady=5, padx=5, fill="x")
            
            btn = AnimatedButton(btn_frame, text=f"{icon}\n{label}", font=get_font(11, "bold"),
                fg_color="transparent", hover_color=COLORS["bg_light"], 
                text_color=COLORS["text3"], height=60, corner_radius=8,
                glow_color=COLORS["accent"], command=lambda k=key: self.nav(k))
            btn.pack(fill="x")
            self.nav_btns[key] = btn

        # Account button at bottom
        account_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        account_frame.pack(side="bottom", pady=(0, 5), fill="x", padx=5)
        
        self.account_btn = AnimatedButton(account_frame, text="[?]\nLOGIN", font=get_font(10, "bold"),
            fg_color="transparent", hover_color=COLORS["bg_light"], 
            text_color=COLORS["text3"], height=50, corner_radius=8,
            glow_color=COLORS["accent"], command=lambda: self.nav("account"))
        self.account_btn.pack(fill="x")
        self.nav_btns["account"] = self.account_btn
        
        # Status indicator at bottom with pulse animation
        status_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", pady=(5, 20), fill="x")
        ctk.CTkLabel(status_frame, text="STATUS:", font=get_font(8), 
                    text_color=COLORS["text3"]).pack()
        self.status_indicator = ctk.CTkLabel(status_frame, text="● OFFLINE", 
                    font=get_font(9, "bold"), text_color=COLORS["error"])
        self.status_indicator.pack()
        
        # Start status pulse animation
        self._pulse_status()

        # Content area
        self.content = ctk.CTkFrame(self.overlay, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Top bar - terminal style header
        top = ctk.CTkFrame(self.content, fg_color=COLORS["bg_card"], height=70, 
                          corner_radius=10, border_width=1, border_color=COLORS["border"])
        top.pack(fill="x", pady=(0, 10))
        top.pack_propagate(False)

        top_inner = ctk.CTkFrame(top, fg_color="transparent")
        top_inner.pack(fill="both", expand=True, padx=20)

        # Title with terminal prefix
        title_frame = ctk.CTkFrame(top_inner, fg_color="transparent")
        title_frame.pack(side="left", fill="y", pady=15)
        
        ctk.CTkLabel(title_frame, text="root@wejz:~$", font=get_font(11), 
                    text_color=COLORS["text3"]).pack(side="left")
        self.title_label = ctk.CTkLabel(title_frame, text=" ./home", font=get_font(16, "bold"), 
                    text_color=COLORS["accent"])
        self.title_label.pack(side="left")
        
        # Blinking cursor
        self.cursor_label = ctk.CTkLabel(title_frame, text="█", font=get_font(16, "bold"), 
                    text_color=COLORS["accent"])
        self.cursor_label.pack(side="left")
        self.blink_cursor()

        # Profile selector
        prof_frame = ctk.CTkFrame(top_inner, fg_color=COLORS["bg_light"], corner_radius=8,
                                 border_width=1, border_color=COLORS["border"])
        prof_frame.pack(side="right", pady=15)
        ctk.CTkLabel(prof_frame, text="[PROFILE]", font=get_font(9), 
                    text_color=COLORS["text3"]).pack(side="left", padx=(10, 5))
        self.profile_menu = ctk.CTkOptionMenu(prof_frame, values=list(self.profiles.get_all().keys()),
            command=self.on_profile_change, font=get_font(11), fg_color=COLORS["bg_medium"],
            button_color=COLORS["accent_dim"], dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"], width=130, height=30,
            text_color=COLORS["text"])
        self.profile_menu.set(self.current_profile)
        self.profile_menu.pack(side="left", padx=(0, 10), pady=6)

        # User display
        user_frame = ctk.CTkFrame(top_inner, fg_color=COLORS["bg_light"], corner_radius=8,
                                 border_width=1, border_color=COLORS["border"])
        user_frame.pack(side="right", padx=(0, 10), pady=15)
        ctk.CTkLabel(user_frame, text="[USER]", font=get_font(9), 
                    text_color=COLORS["text3"]).pack(side="left", padx=(10, 5))
        self.user_label = ctk.CTkLabel(user_frame, text=self.username, font=get_font(11, "bold"), 
                    text_color=COLORS["accent"])
        self.user_label.pack(side="left", padx=(0, 10), pady=6)

        # Main frame with border
        self.main = ctk.CTkFrame(self.content, fg_color=COLORS["bg_card"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
        self.main.pack(fill="both", expand=True)

    def blink_cursor(self):
        """Static cursor - no blink for performance"""
        self.cursor_label.configure(text="█")
    
    def _pulse_status(self):
        """Update status indicator - no animation"""
        try:
            if self.is_logged_in:
                self.status_indicator.configure(text="● ONLINE", text_color=COLORS["success"])
            else:
                self.status_indicator.configure(text="● OFFLINE", text_color=COLORS["error"])
        except:
            pass

    def on_profile_change(self, name):
        self.current_profile = name
        if self.current_page == "home":
            self.show_home()

    def refresh_profiles(self):
        names = list(self.profiles.get_all().keys())
        self.profile_menu.configure(values=names)
        if self.current_profile not in names:
            self.current_profile = names[0] if names else "Default"
        self.profile_menu.set(self.current_profile)

    def transition_to(self, page_func):
        """Smooth fade transition between pages with sliding content"""
        self._transition_step = 0
        self._page_func = page_func
        self._do_fade_out()
    
    def _do_fade_out(self):
        """Fade out current content"""
        steps = 6
        if self._transition_step < steps:
            # Darken the main frame progressively
            alpha = self._transition_step / steps
            # Interpolate between card color and dark
            self.main.configure(fg_color=COLORS["bg_dark"])
            self._transition_step += 1
            self.after(25, self._do_fade_out)
        else:
            self._complete_transition()
    
    def _complete_transition(self):
        """Complete the transition and fade in new content"""
        self._page_func()
        self.main.configure(fg_color=COLORS["bg_card"])
        # Animate children sliding in
        self._animate_page_in()
    
    def _animate_page_in(self):
        """No animation for performance"""
        pass
    
    def _animate_card_in(self, card, delay=0):
        """No animation for performance"""
        pass

    def nav(self, page):
        self.current_page = page
        
        # Animate nav button transitions
        for k, b in self.nav_btns.items():
            if k == page:
                self._animate_nav_select(b)
            else:
                b.configure(fg_color="transparent", text_color=COLORS["text3"])
        
        page_map = {
            "home": self.show_home,
            "profiles": self.show_profiles,
            "play": self.show_play,
            "mods": self.show_mods,
            "friends": self.show_friends,
            "settings": self.show_settings,
            "account": self.show_account
        }
        self.transition_to(page_map.get(page, self.show_home))
    
    def _animate_nav_select(self, btn):
        """No animation for performance"""
        btn.configure(fg_color=COLORS["accent"], text_color=COLORS["bg_dark"])
    
    def _type_title(self, text, speed=25):
        """Terminal typing effect for title label"""
        self._typing_text = text
        self._typing_index = 0
        self._type_next_char(speed)
    
    def _type_next_char(self, speed):
        """Type next character in title"""
        if self._typing_index <= len(self._typing_text):
            displayed = self._typing_text[:self._typing_index]
            self.title_label.configure(text=displayed + "█")
            self._typing_index += 1
            self.after(speed, lambda: self._type_next_char(speed))
        else:
            self.title_label.configure(text=self._typing_text)
    
    def _pulse_launch_btn(self):
        """No animation for performance"""
        pass
    
    def _animate_hero_glow(self, hero):
        """No animation for performance"""
        pass
    
    def _on_search_focus(self, frame, focused):
        """Simple border change - no animation"""
        if focused:
            frame.configure(border_color=COLORS["accent"], border_width=2)
        else:
            frame.configure(border_color=COLORS["border"], border_width=1)

    def clear(self):
        for w in self.main.winfo_children():
            w.destroy()

    def show_home(self):
        self.clear()
        self._type_title(" ./welcome")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "home" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "home" else COLORS["text3"])

        prof = self.profiles.get(self.current_profile) or {"version": "1.20.4", "mods": [], "ram": 4, "loader": "fabric"}

        # Inner padding frame
        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        # Hero section - terminal style with entrance animation
        hero = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=15, 
                           border_width=1, border_color=COLORS["accent"], height=200)
        hero.pack(fill="x", pady=(0, 20))
        hero.pack_propagate(False)
        
        # Animate hero border glow
        self._animate_hero_glow(hero)

        hero_inner = ctk.CTkFrame(hero, fg_color="transparent")
        hero_inner.pack(fill="both", expand=True, padx=30, pady=25)

        # ASCII art style title
        title_art = """
 ╔═══════════════════════════════════╗
 ║   SYSTEM READY FOR EXECUTION      ║
 ╚═══════════════════════════════════╝"""
        
        ctk.CTkLabel(hero_inner, text=title_art, font=(FONT_FALLBACK, 12), 
                    text_color=COLORS["accent"], justify="left").pack(anchor="w")

        # System info
        info_frame = ctk.CTkFrame(hero_inner, fg_color="transparent")
        info_frame.pack(anchor="w", pady=(15, 0))
        
        info_text = f"> Profile: {self.current_profile}\n> Version: {prof['version']}\n> Mods: {len(prof['mods'])} loaded\n> Memory: {prof['ram']}GB allocated"
        ctk.CTkLabel(info_frame, text=info_text, font=get_font(12), 
                    text_color=COLORS["text2"], justify="left").pack(anchor="w")

        # Progress section
        self.home_prog_frame = ctk.CTkFrame(hero_inner, fg_color="transparent")
        self.home_prog_label = ctk.CTkLabel(self.home_prog_frame, text="", font=get_font(11), 
                    text_color=COLORS["accent"])
        self.home_prog_label.pack(anchor="w")
        self.home_prog_bar = ctk.CTkProgressBar(self.home_prog_frame, fg_color=COLORS["bg_dark"],
            progress_color=COLORS["accent"], height=8, width=400)
        self.home_prog_bar.pack(anchor="w", pady=(5, 0))
        self.home_prog_bar.set(0)

        # Launch button - big and prominent with pulse effect
        btn_frame = ctk.CTkFrame(hero, fg_color="transparent")
        btn_frame.pack(side="right", padx=30)
        
        self.home_launch_btn = AnimatedButton(btn_frame, text="[ EXECUTE ]", font=get_font(18, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            width=180, height=70, corner_radius=10, glow_color=COLORS["terminal_green"],
            command=self.launch)
        self.home_launch_btn.pack()
        
        ctk.CTkLabel(btn_frame, text="Press to launch game", font=get_font(9), 
                    text_color=COLORS["text3"]).pack(pady=(5, 0))
        
        # Start subtle pulse animation on launch button
        self._pulse_launch_btn()

        # Stats grid with staggered animation
        stats = ctk.CTkFrame(inner, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 20))
        
        stats_data = [
            ("[PROFILE]", self.current_profile, COLORS["accent"]),
            ("[MODS]", f"{len(prof['mods'])} active", COLORS["accent2"]),
            ("[VERSION]", prof['version'], COLORS["success"]),
            ("[LOADER]", prof.get('loader', 'fabric').upper(), COLORS["text2"]),
        ]
        
        for idx, (title, value, color) in enumerate(stats_data):
            card = AnimatedCard(stats, fg_color=COLORS["bg_medium"], corner_radius=10,
                               border_width=1, border_color=COLORS["border"], height=90,
                               hover_border=color, hover_fg=COLORS["bg_light"])
            card.pack(side="left", expand=True, fill="x", padx=(0, 10))
            card.pack_propagate(False)
            
            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=15, pady=15)
            
            ctk.CTkLabel(card_inner, text=title, font=get_font(10), 
                        text_color=COLORS["text3"]).pack(anchor="w")
            ctk.CTkLabel(card_inner, text=value, font=get_font(14, "bold"), 
                        text_color=color).pack(anchor="w", pady=(5, 0))
            
            # Stagger entrance animation
            self._animate_card_in(card, idx * 80)

        # Quick actions
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(fill="x")
        
        ctk.CTkLabel(actions, text="> QUICK_ACTIONS:", font=get_font(11), 
                    text_color=COLORS["text3"]).pack(anchor="w", pady=(0, 10))
        
        btn_row = ctk.CTkFrame(actions, fg_color="transparent")
        btn_row.pack(fill="x")
        
        for text, cmd in [("[ ADD MODS ]", lambda: self.nav("mods")), 
                         ("[ SETTINGS ]", lambda: self.nav("settings")),
                         ("[ PROFILES ]", lambda: self.nav("profiles"))]:
            AnimatedButton(btn_row, text=text, font=get_font(11, "bold"),
                fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], 
                text_color=COLORS["text"], height=45, corner_radius=8,
                border_width=1, border_color=COLORS["border"],
                glow_color=COLORS["accent"], command=cmd).pack(side="left", padx=(0, 10))

    def show_profiles(self):
        self.clear()
        self._type_title(" ./profiles")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "profiles" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "profiles" else COLORS["text3"])

        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        # Create new profile section
        create = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10,
                             border_width=1, border_color=COLORS["border"])
        create.pack(fill="x", pady=(0, 20))
        create_inner = ctk.CTkFrame(create, fg_color="transparent")
        create_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(create_inner, text="> CREATE_NEW_PROFILE", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 15))

        row1 = ctk.CTkFrame(create_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(row1, text="NAME:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.new_name = ctk.CTkEntry(row1, fg_color=COLORS["bg_dark"], border_color=COLORS["border"],
            text_color=COLORS["text"], width=150, height=38, font=get_font(12))
        self.new_name.pack(side="left", padx=(10, 15))

        ctk.CTkLabel(row1, text="VERSION:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.new_ver = ctk.CTkOptionMenu(row1, values=MC_VERSIONS,
            fg_color=COLORS["bg_dark"], button_color=COLORS["accent_dim"], 
            dropdown_fg_color=COLORS["bg_card"], width=100, height=38, font=get_font(11),
            text_color=COLORS["text"])
        self.new_ver.pack(side="left", padx=(10, 15))

        ctk.CTkLabel(row1, text="LOADER:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.new_loader = ctk.CTkOptionMenu(row1, values=["VANILLA", "FABRIC", "FORGE"],
            fg_color=COLORS["bg_dark"], button_color=COLORS["accent_dim"], 
            dropdown_fg_color=COLORS["bg_card"], width=100, height=38, font=get_font(11),
            text_color=COLORS["text"])
        self.new_loader.set("FABRIC")
        self.new_loader.pack(side="left", padx=(10, 15))

        AnimatedButton(row1, text="[ CREATE ]", font=get_font(12, "bold"), fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"], width=100, height=38,
            glow_color=COLORS["terminal_green"], command=self.create_profile).pack(side="left")

        # Profile list
        ctk.CTkLabel(inner, text="> PROFILE_LIST:", font=get_font(12, "bold"), 
                    text_color=COLORS["text2"]).pack(anchor="w", pady=(10, 15))

        scroll = ctk.CTkScrollableFrame(inner, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for name, prof in self.profiles.get_all().items():
            self.profile_card(scroll, name, prof)

    def profile_card(self, parent, name, prof):
        is_sel = name == self.current_profile
        card = AnimatedCard(parent, fg_color=COLORS["bg_medium"], corner_radius=10, height=85,
                           border_width=2 if is_sel else 1, 
                           border_color=COLORS["accent"] if is_sel else COLORS["border"],
                           hover_border=COLORS["terminal_green"] if not is_sel else COLORS["accent"],
                           hover_fg=COLORS["bg_light"])
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=12)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        header = ctk.CTkFrame(left, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text=f"[{name[:1].upper()}]", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(header, text=name, font=get_font(14, "bold"), 
                    text_color=COLORS["text"]).pack(side="left", padx=10)
        
        if is_sel:
            ctk.CTkLabel(header, text="< ACTIVE >", font=get_font(10, "bold"), 
                        text_color=COLORS["success"]).pack(side="left")

        info = f"v{prof['version']} | {prof.get('loader', 'fabric').upper()} | {len(prof['mods'])} mods | {prof['ram']}GB"
        ctk.CTkLabel(left, text=info, font=get_font(11), 
                    text_color=COLORS["text3"]).pack(anchor="w", pady=(8, 0))

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        if not is_sel:
            AnimatedButton(right, text="[SELECT]", font=get_font(10, "bold"), fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"], width=80, height=35,
                glow_color=COLORS["terminal_green"],
                command=lambda n=name: self.select_profile(n)).pack(side="left", padx=5)

        AnimatedButton(right, text="[EDIT]", font=get_font(10, "bold"), fg_color=COLORS["bg_light"],
            hover_color=COLORS["bg_card_hover"], text_color=COLORS["text"], width=70, height=35,
            glow_color=COLORS["accent"],
            command=lambda n=name: self.edit_profile(n)).pack(side="left", padx=5)

        if name != "Default":
            AnimatedButton(right, text="[X]", font=get_font(12, "bold"), fg_color=COLORS["error"],
                hover_color="#cc0000", text_color=COLORS["bg_dark"], width=40, height=35,
                glow_color=COLORS["error"],
                command=lambda n=name: self.delete_profile(n)).pack(side="left", padx=5)

    def create_profile(self):
        name = self.new_name.get().strip()
        if not name:
            self.notify("ERROR: Enter profile name!", True)
            return
        loader = self.new_loader.get().lower()
        if self.profiles.create(name, self.new_ver.get(), loader):
            self.notify(f"CREATED: '{name}' ({self.new_ver.get()} {loader})")
            self.refresh_profiles()
            self.show_profiles()
        else:
            self.notify("ERROR: Profile exists!", True)

    def select_profile(self, name):
        self.current_profile = name
        self.profile_menu.set(name)
        self.show_profiles()

    def delete_profile(self, name):
        if self.profiles.delete(name):
            self.notify(f"DELETED: '{name}'")
            self.refresh_profiles()
            self.show_profiles()

    def edit_profile(self, name):
        self.clear()
        self._type_title(f" ./edit/{name}")

        prof = self.profiles.get(name)
        if not prof:
            return

        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        AnimatedButton(inner, text="[ < BACK ]", font=get_font(11, "bold"), fg_color="transparent",
            hover_color=COLORS["bg_medium"], text_color=COLORS["text2"],
            glow_color=COLORS["accent"],
            command=lambda: self.nav("profiles")).pack(anchor="w", pady=(0, 15))

        # Settings card
        card = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10,
                           border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=(0, 20))
        card_inner = ctk.CTkFrame(card, fg_color="transparent")
        card_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(card_inner, text="> PROFILE_CONFIG", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 15))

        # Version
        row1 = ctk.CTkFrame(card_inner, fg_color="transparent")
        row1.pack(fill="x", pady=8)
        ctk.CTkLabel(row1, text="VERSION:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.edit_ver = ctk.CTkOptionMenu(row1, values=MC_VERSIONS,
            fg_color=COLORS["bg_dark"], button_color=COLORS["accent_dim"], width=120, height=38,
            font=get_font(11), text_color=COLORS["text"])
        self.edit_ver.set(prof.get("version", "1.20.4"))
        self.edit_ver.pack(side="right")

        # Loader (Vanilla/Fabric/Forge)
        row_loader = ctk.CTkFrame(card_inner, fg_color="transparent")
        row_loader.pack(fill="x", pady=8)
        ctk.CTkLabel(row_loader, text="LOADER:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.edit_loader = ctk.CTkOptionMenu(row_loader, 
            values=["VANILLA", "FABRIC", "FORGE"],
            fg_color=COLORS["bg_dark"], button_color=COLORS["accent_dim"], width=120, height=38,
            font=get_font(11), text_color=COLORS["text"])
        self.edit_loader.set(prof.get("loader", "fabric").upper())
        self.edit_loader.pack(side="right")

        # Fabric API auto-install checkbox
        row_api = ctk.CTkFrame(card_inner, fg_color="transparent")
        row_api.pack(fill="x", pady=8)
        ctk.CTkLabel(row_api, text="FABRIC API:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.edit_fabric_api = ctk.CTkCheckBox(row_api, text="Auto-install (required for most mods)",
            font=get_font(10), fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["text3"], checkbox_height=20, checkbox_width=20)
        if prof.get("fabric_api", True):
            self.edit_fabric_api.select()
        self.edit_fabric_api.pack(side="right")

        # RAM
        row2 = ctk.CTkFrame(card_inner, fg_color="transparent")
        row2.pack(fill="x", pady=8)
        ctk.CTkLabel(row2, text="MEMORY:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        ram_f = ctk.CTkFrame(row2, fg_color="transparent")
        ram_f.pack(side="right")
        self.edit_ram_lbl = ctk.CTkLabel(ram_f, text=f"{prof['ram']}GB", font=get_font(12, "bold"), 
                    text_color=COLORS["accent"])
        self.edit_ram_lbl.pack(side="right")
        self.edit_ram = ctk.CTkSlider(ram_f, from_=2, to=16, number_of_steps=14,
            fg_color=COLORS["bg_dark"], progress_color=COLORS["accent"],
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"], width=200,
            command=lambda v: self.edit_ram_lbl.configure(text=f"{int(v)}GB"))
        self.edit_ram.set(prof["ram"])
        self.edit_ram.pack(side="right", padx=15)

        AnimatedButton(card_inner, text="[ SAVE ]", font=get_font(12, "bold"), fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"], height=42, width=120,
            glow_color=COLORS["terminal_green"],
            command=lambda: self.save_profile(name)).pack(anchor="w", pady=(15, 0))

        # Mods list
        ctk.CTkLabel(inner, text=f"> INSTALLED_MODS ({len(prof['mods'])})", font=get_font(12, "bold"),
            text_color=COLORS["text2"]).pack(anchor="w", pady=(10, 15))

        scroll = ctk.CTkScrollableFrame(inner, fg_color="transparent", height=250)
        scroll.pack(fill="both", expand=True)

        if prof["mods"]:
            for mod in prof["mods"]:
                row = ctk.CTkFrame(scroll, fg_color=COLORS["bg_medium"], corner_radius=8, height=50,
                                  border_width=1, border_color=COLORS["border"])
                row.pack(fill="x", pady=3)
                row.pack_propagate(False)
                ri = ctk.CTkFrame(row, fg_color="transparent")
                ri.pack(fill="both", expand=True, padx=15, pady=10)
                ctk.CTkLabel(ri, text=mod.get("icon", "[?]"), font=get_font(12, "bold"), 
                            text_color=COLORS["accent"]).pack(side="left")
                ctk.CTkLabel(ri, text=mod["name"], font=get_font(12, "bold"), 
                            text_color=COLORS["text"]).pack(side="left", padx=10)
                AnimatedButton(ri, text="[REMOVE]", font=get_font(10), fg_color=COLORS["error"],
                    hover_color="#cc0000", text_color=COLORS["bg_dark"], width=80, height=30,
                    glow_color=COLORS["error"],
                    command=lambda m=mod["name"], n=name: self.remove_mod(n, m)).pack(side="right")
        else:
            ctk.CTkLabel(scroll, text="No mods installed. Visit MODS to add some!",
                font=get_font(11), text_color=COLORS["text3"]).pack(pady=30)

    def save_profile(self, name):
        loader = self.edit_loader.get().lower()
        fabric_api = self.edit_fabric_api.get() == 1
        self.profiles.update(name, 
            version=self.edit_ver.get(), 
            loader=loader,
            fabric_api=fabric_api,
            ram=int(self.edit_ram.get()))
        self.notify("SAVED: Profile updated!")

    def remove_mod(self, profile, mod_name):
        self.profiles.remove_mod(profile, mod_name)
        self.notify(f"REMOVED: {mod_name}")
        self.edit_profile(profile)

    def show_play(self):
        self.clear()
        self._type_title(" ./execute")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "play" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "play" else COLORS["text3"])

        prof = self.profiles.get(self.current_profile) or {"version": "1.20.4", "mods": [], "ram": 4, "loader": "fabric"}

        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        # Username section
        card1 = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10,
                            border_width=1, border_color=COLORS["border"])
        card1.pack(fill="x", pady=(0, 15))
        inner1 = ctk.CTkFrame(card1, fg_color="transparent")
        inner1.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(inner1, text="> SET_USERNAME", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 15))

        row = ctk.CTkFrame(inner1, fg_color="transparent")
        row.pack(fill="x")
        self.play_username = ctk.CTkEntry(row, fg_color=COLORS["bg_dark"], border_color=COLORS["border"],
            text_color=COLORS["text"], width=280, height=45, font=get_font(14))
        self.play_username.insert(0, self.username)
        self.play_username.pack(side="left")

        AnimatedButton(row, text="[ SAVE ]", font=get_font(11, "bold"), fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"], width=90, height=45,
            glow_color=COLORS["terminal_green"],
            command=self.save_play_username).pack(side="left", padx=15)

        ctk.CTkLabel(inner1, text="// Offline mode - any username accepted",
            font=get_font(10), text_color=COLORS["text3"]).pack(anchor="w", pady=(10, 0))

        # System info
        card2 = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10,
                            border_width=1, border_color=COLORS["border"])
        card2.pack(fill="x", pady=(0, 15))
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(inner2, text="> SYSTEM_STATUS", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 15))

        for lbl, val in [("PROFILE", self.current_profile), ("VERSION", prof["version"]),
                         ("LOADER", prof.get("loader", "fabric").upper()), 
                         ("MODS", f"{len(prof['mods'])} loaded"),
                         ("MEMORY", f"{prof['ram']}GB")]:
            r = ctk.CTkFrame(inner2, fg_color="transparent")
            r.pack(fill="x", pady=3)
            ctk.CTkLabel(r, text=f"  {lbl}:", font=get_font(11), 
                        text_color=COLORS["text3"]).pack(side="left")
            ctk.CTkLabel(r, text=val, font=get_font(11, "bold"), 
                        text_color=COLORS["text"]).pack(side="right")

        # Launch section
        card3 = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=15,
                            border_width=2, border_color=COLORS["accent"])
        card3.pack(fill="both", expand=True, pady=(0, 0))
        inner3 = ctk.CTkFrame(card3, fg_color="transparent")
        inner3.pack(fill="both", expand=True, padx=25, pady=25)

        # ASCII launch graphic
        launch_art = """
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║     █▀▀ ▀▄▀ █▀▀ █▀▀ █ █ ▀█▀ █▀▀      ║
    ║     ██▄ █ █ ██▄ █▄▄ █▄█  █  ██▄      ║
    ║                                      ║
    ╚══════════════════════════════════════╝"""
        
        ctk.CTkLabel(inner3, text=launch_art, font=(FONT_FALLBACK, 11), 
                    text_color=COLORS["accent"], justify="center").pack(pady=(10, 5))

        ctk.CTkLabel(inner3, text=f"// MINECRAFT {prof['version']} + {prof.get('loader', 'fabric').upper()}",
            font=get_font(12), text_color=COLORS["text2"]).pack(pady=(5, 15))

        self.play_prog_frame = ctk.CTkFrame(inner3, fg_color="transparent")
        self.play_prog_label = ctk.CTkLabel(self.play_prog_frame, text="", font=get_font(11), 
                    text_color=COLORS["accent"])
        self.play_prog_label.pack()
        self.play_prog_bar = ctk.CTkProgressBar(self.play_prog_frame, fg_color=COLORS["bg_dark"],
            progress_color=COLORS["accent"], height=8, width=350)
        self.play_prog_bar.pack(pady=(5, 0))
        self.play_prog_bar.set(0)

        self.play_launch_btn = AnimatedButton(inner3, text="[ EXECUTE MINECRAFT ]", font=get_font(18, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            width=300, height=65, corner_radius=10, glow_color=COLORS["terminal_green"],
            command=self.launch)
        self.play_launch_btn.pack(pady=15)

    def save_play_username(self):
        new = self.play_username.get().strip()
        if new:
            self.username = new
            self.save_username()
            self.user_label.configure(text=self.username)
            self.notify("SAVED: Username updated!")

    def show_mods(self):
        self.clear()
        self._type_title(" ./mods")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "mods" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "mods" else COLORS["text3"])

        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        # Search bar with source selector
        search_frame = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10, height=55,
                                   border_width=1, border_color=COLORS["border"])
        search_frame.pack(fill="x", pady=(0, 15))
        search_frame.pack_propagate(False)
        si = ctk.CTkFrame(search_frame, fg_color="transparent")
        si.pack(fill="both", expand=True, padx=15)
        
        self._search_cursor = ctk.CTkLabel(si, text=">", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"])
        self._search_cursor.pack(side="left")
        
        # Source selector (Modrinth/CurseForge)
        self.mod_source = ctk.CTkOptionMenu(si, values=["MODRINTH", "CURSEFORGE"],
            fg_color=COLORS["bg_dark"], button_color=COLORS["accent_dim"], 
            width=110, height=38, font=get_font(10, "bold"), text_color=COLORS["text"])
        self.mod_source.set("CURSEFORGE")
        self.mod_source.pack(side="left", padx=(10, 5))
        
        self.mod_search = ctk.CTkEntry(si, placeholder_text="search mods...", font=get_font(12),
            fg_color="transparent", border_width=0, text_color=COLORS["text"], height=45, width=250)
        self.mod_search.pack(side="left", fill="x", expand=True, padx=10)
        self.mod_search.bind("<Return>", lambda e: self.search_mods())
        self.mod_search.bind("<FocusIn>", lambda e: self._on_search_focus(search_frame, True))
        self.mod_search.bind("<FocusOut>", lambda e: self._on_search_focus(search_frame, False))
        
        AnimatedButton(si, text="[SEARCH]", font=get_font(11, "bold"), fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"], width=90, height=38,
            glow_color=COLORS["terminal_green"],
            command=self.search_mods).pack(side="right", padx=(0, 5))
        
        AnimatedButton(si, text="[POPULAR]", font=get_font(11, "bold"), fg_color=COLORS["bg_dark"],
            hover_color=COLORS["bg_light"], text_color=COLORS["text2"], width=90, height=38,
            glow_color=COLORS["accent"],
            command=self.load_popular_mods).pack(side="right", padx=(0, 5))

        # Category tabs
        cats = ctk.CTkFrame(inner, fg_color="transparent")
        cats.pack(fill="x", pady=(0, 15))

        self.cat_btns = {}
        for cat, txt in [("performance", "[PERFORMANCE]"), ("visual", "[VISUAL]"),
                         ("utility", "[UTILITY]"), ("gameplay", "[GAMEPLAY]"), ("browse", "[BROWSE ALL]")]:
            is_sel = cat == self.mod_category
            btn = AnimatedButton(cats, text=txt, font=get_font(10, "bold" if is_sel else "normal"),
                fg_color=COLORS["accent"] if is_sel else COLORS["bg_medium"],
                hover_color=COLORS["accent_hover"] if is_sel else COLORS["bg_light"],
                text_color=COLORS["bg_dark"] if is_sel else COLORS["text2"],
                height=38, corner_radius=8, border_width=1, 
                border_color=COLORS["accent"] if is_sel else COLORS["border"],
                glow_color=COLORS["accent"],
                command=lambda c=cat: self.select_cat(c))
            btn.pack(side="left", padx=(0, 8))
            self.cat_btns[cat] = btn

        prof = self.profiles.get(self.current_profile) or {}
        loader = prof.get("loader", "fabric").upper()
        ctk.CTkLabel(cats, text=f"// {self.current_profile} • {prof.get('version', '1.20.4')} • {loader}",
            font=get_font(10), text_color=COLORS["text3"]).pack(side="right")

        # Mods list
        self.mods_scroll = ctk.CTkScrollableFrame(inner, fg_color="transparent")
        self.mods_scroll.pack(fill="both", expand=True)
        self.display_mods()

    def select_cat(self, cat):
        self.mod_category = cat
        self.search_results = []
        
        # Animate category button transitions
        for c, b in self.cat_btns.items():
            is_sel = c == cat
            if is_sel:
                # Pulse effect on selected category
                b.configure(fg_color=COLORS["terminal_green"], text_color=COLORS["bg_dark"])
                self.after(60, lambda btn=b: btn.configure(fg_color=COLORS["accent"]))
            else:
                b.configure(fg_color=COLORS["bg_medium"],
                           text_color=COLORS["text2"],
                           border_color=COLORS["border"],
                           font=get_font(10, "normal"))
        
        # If "browse" selected, load popular mods
        if cat == "browse":
            self.after(100, self.load_popular_mods)
        else:
            # Slight delay before showing mods for smoother transition
            self.after(100, self.display_mods)

    def display_mods(self):
        for w in self.mods_scroll.winfo_children():
            w.destroy()

        prof = self.profiles.get(self.current_profile)
        installed = [m["name"] for m in prof["mods"]] if prof else []

        mods = self.search_results if self.search_results else MODS_DB.get(self.mod_category, [])

        if not mods:
            ctk.CTkLabel(self.mods_scroll, text="No mods found. Try searching or click [POPULAR]",
                font=get_font(12), text_color=COLORS["text3"]).pack(pady=50)
            return

        for idx, mod in enumerate(mods):
            is_inst = mod["name"] in installed
            source = mod.get("source", "featured")
            source_color = COLORS["warning"] if source == "curseforge" else COLORS["accent"]
            
            card = AnimatedCard(self.mods_scroll, fg_color=COLORS["bg_medium"], corner_radius=10, 
                               height=90, border_width=1, 
                               border_color=COLORS["success"] if is_inst else COLORS["border"],
                               hover_border=COLORS["terminal_green"],
                               hover_fg=COLORS["bg_light"])
            card.pack(fill="x", pady=4)
            card.pack_propagate(False)
            
            # Stagger animation for cards appearing
            self._animate_card_in(card, idx * 30)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=12)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            header = ctk.CTkFrame(left, fg_color="transparent")
            header.pack(fill="x")
            
            # Source icon
            icon_text = mod.get("icon", "[?]")
            ctk.CTkLabel(header, text=icon_text, font=get_font(12, "bold"), 
                        text_color=source_color).pack(side="left")
            ctk.CTkLabel(header, text=mod["name"][:35], font=get_font(13, "bold"), 
                        text_color=COLORS["text"]).pack(side="left", padx=10)
            
            # Downloads count
            downloads = mod.get("downloads", 0)
            if downloads > 0:
                dl_text = f"{downloads:,}" if downloads < 1000000 else f"{downloads/1000000:.1f}M"
                ctk.CTkLabel(header, text=f"↓{dl_text}", font=get_font(9), 
                            text_color=COLORS["text3"]).pack(side="left", padx=5)

            ctk.CTkLabel(left, text=mod.get("desc", "")[:80], font=get_font(10), 
                        text_color=COLORS["text3"]).pack(anchor="w", pady=(5, 0))

            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            if is_inst:
                AnimatedButton(right, text="[INSTALLED]", font=get_font(11, "bold"), 
                    fg_color=COLORS["success"], hover_color=COLORS["error"], 
                    text_color=COLORS["bg_dark"], width=110, height=40,
                    glow_color=COLORS["error"],
                    command=lambda m=mod: self.unadd_mod(m)).pack()
            else:
                AnimatedButton(right, text="[+ ADD]", font=get_font(11, "bold"), 
                    fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], 
                    text_color=COLORS["bg_dark"], width=100, height=40,
                    glow_color=COLORS["terminal_green"],
                    command=lambda m=mod: self.add_mod(m)).pack()

    def search_mods(self):
        query = self.mod_search.get().strip()
        if not query:
            self.search_results = []
            self.display_mods()
            return

        prof = self.profiles.get(self.current_profile) or {}
        ver = prof.get("version", "1.20.4")
        loader = prof.get("loader", "fabric")
        source = self.mod_source.get()

        def do_search():
            if source == "CURSEFORGE":
                results = CurseForgeAPI.search(query, ver, loader, 25)
                formatted = []
                for r in results:
                    formatted.append({
                        "name": r.get("name", "?"),
                        "slug": r.get("slug", ""),
                        "id": r.get("id"),
                        "icon": "[CF]",
                        "desc": r.get("description", "")[:80],
                        "downloads": r.get("downloads", 0),
                        "source": "curseforge"
                    })
                self.search_results = formatted
            else:
                results = ModrinthAPI.search(query, ver, 25)
                formatted = []
                for r in results:
                    formatted.append({
                        "name": r.get("title", "?"),
                        "slug": r.get("slug", ""),
                        "icon": "[MR]",
                        "desc": r.get("description", "")[:80],
                        "downloads": r.get("downloads", 0),
                        "source": "modrinth"
                    })
                self.search_results = formatted
            self.after(0, self.display_mods)

        self.notify(f"SEARCHING {source}...")
        threading.Thread(target=do_search, daemon=True).start()

    def load_popular_mods(self):
        """Load popular mods from selected source"""
        prof = self.profiles.get(self.current_profile) or {}
        ver = prof.get("version", "1.20.4")
        loader = prof.get("loader", "fabric")
        source = self.mod_source.get()

        def do_load():
            if source == "CURSEFORGE":
                results = CurseForgeAPI.get_popular(ver, loader, 30)
                self.search_results = results
            else:
                # Modrinth popular
                try:
                    params = {
                        "facets": json.dumps([["project_type:mod"], [f"versions:{ver}"], [f"categories:{loader}"]]),
                        "limit": 30,
                        "index": "downloads"
                    }
                    r = requests.get(f"{MODRINTH_API}/search", params=params, timeout=15)
                    if r.ok:
                        hits = r.json().get("hits", [])
                        self.search_results = [{
                            "name": h.get("title", "?"),
                            "slug": h.get("slug", ""),
                            "icon": "[MR]",
                            "desc": h.get("description", "")[:80],
                            "downloads": h.get("downloads", 0),
                            "source": "modrinth"
                        } for h in hits]
                except:
                    self.search_results = []
            self.after(0, self.display_mods)

        self.notify(f"LOADING POPULAR FROM {source}...")
        threading.Thread(target=do_load, daemon=True).start()

    def add_mod(self, mod):
        def do_add():
            self.after(0, lambda: self.notify(f"DOWNLOADING: {mod['name']}"))
            
            prof = self.profiles.get(self.current_profile) or {}
            ver = prof.get("version", "1.20.4")
            loader = prof.get("loader", "fabric")
            source = mod.get("source", "featured")
            slug = mod.get("slug", "")
            mod_id = mod.get("id")

            filename = None
            url = None
            
            try:
                if source == "curseforge" and mod_id:
                    # Download from CurseForge
                    url, filename = CurseForgeAPI.get_download_url(mod_id, ver, loader)
                    if url and filename:
                        dest = Path(self.settings["game_dir"]) / "mods" / filename
                        if not dest.exists():
                            CurseForgeAPI.download(url, dest)
                elif slug:
                    # Download from Modrinth
                    versions = ModrinthAPI.get_versions(slug, ver)
                    if versions:
                        files = versions[0].get("files", [])
                        if files:
                            url = files[0].get("url")
                            filename = files[0].get("filename")
                            if url and filename:
                                dest = Path(self.settings["game_dir"]) / "mods" / filename
                                if not dest.exists():
                                    ModrinthAPI.download(url, dest)

                mod_data = {
                    "name": mod["name"], 
                    "slug": slug, 
                    "id": mod_id,
                    "icon": mod.get("icon", "[?]"),
                    "desc": mod.get("desc", ""), 
                    "filename": filename,
                    "source": source
                }
                self.profiles.add_mod(self.current_profile, mod_data)
                self.after(0, lambda: self.notify(f"INSTALLED: {mod['name']}"))
            except Exception as e:
                print(f"[MOD] Error downloading {mod['name']}: {e}")
                self.after(0, lambda: self.notify(f"ERROR: Failed to download {mod['name']}", True))
            
            self.after(0, self.display_mods)

        threading.Thread(target=do_add, daemon=True).start()

    def unadd_mod(self, mod):
        self.profiles.remove_mod(self.current_profile, mod["name"])
        self.notify(f"REMOVED: {mod['name']}")
        self.display_mods()

    def show_settings(self):
        self.clear()
        self._type_title(" ./config")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "settings" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "settings" else COLORS["text3"])

        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        card = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10,
                           border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=(0, 20))
        card_inner = ctk.CTkFrame(card, fg_color="transparent")
        card_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(card_inner, text="> SYSTEM_CONFIG", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 15))

        # Java path
        row1 = ctk.CTkFrame(card_inner, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        ctk.CTkLabel(row1, text="JAVA_PATH:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.java_entry = ctk.CTkEntry(row1, fg_color=COLORS["bg_dark"], border_color=COLORS["border"],
            text_color=COLORS["text"], width=350, height=42, font=get_font(11))
        self.java_entry.insert(0, self.settings["java"])
        self.java_entry.pack(side="right")

        # Game dir
        row2 = ctk.CTkFrame(card_inner, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        ctk.CTkLabel(row2, text="GAME_DIR:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(side="left")
        self.dir_entry = ctk.CTkEntry(row2, fg_color=COLORS["bg_dark"], border_color=COLORS["border"],
            text_color=COLORS["text"], width=400, height=42, font=get_font(11))
        self.dir_entry.insert(0, self.settings["game_dir"])
        self.dir_entry.pack(side="right")

        ctk.CTkLabel(card_inner, text="// Java 17+ required for Minecraft 1.18+",
            font=get_font(10), text_color=COLORS["text3"]).pack(anchor="w", pady=(15, 0))

        AnimatedButton(inner, text="[ SAVE CONFIG ]", font=get_font(14, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=55, width=200, corner_radius=10, glow_color=COLORS["terminal_green"],
            command=self.save_all_settings).pack(anchor="w", pady=20)

        # Info section
        info_card = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
        info_card.pack(fill="x")
        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(info_inner, text="> ABOUT", font=get_font(14, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 10))
        
        about_text = f"""
WEJZ CLIENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: {LAUNCHER_VERSION}

Features:
  • Fabric mod loader support
  • Modrinth mod integration
  • Multi-profile management
  • Online friend system
  • Auto-update system
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        ctk.CTkLabel(info_inner, text=about_text, font=(FONT_FALLBACK, 10), 
                    text_color=COLORS["text2"], justify="left").pack(anchor="w")

    def save_all_settings(self):
        self.settings["java"] = self.java_entry.get()
        self.settings["game_dir"] = self.dir_entry.get()
        self.save_settings()
        self.notify("SAVED: Config updated!")

    # ============== Online Features ==============
    
    def _try_restore_session(self):
        """Try to restore saved session on startup - works across updates"""
        def do_restore():
            try:
                print("[STARTUP] Attempting to restore session...")
                if self.online.load_session():
                    print("[STARTUP] Session file found, validating...")
                    # Try to validate with server
                    if self.online.validate_session():
                        self.is_logged_in = True
                        username = self.online.user.get('username', 'User')
                        print(f"[STARTUP] Session valid for {username}")
                        self.after(0, self._update_account_ui)
                        self.after(0, lambda: self.notify(f"Welcome back, {username}!"))
                        self._refresh_friends_data()
                    else:
                        # Session invalid but we have saved data - keep user info for display
                        print("[STARTUP] Session expired, need to re-login")
                        # Don't clear - let user see they need to re-login
                        self.after(0, self._update_account_ui)
                else:
                    print("[STARTUP] No saved session found")
            except Exception as e:
                print(f"[STARTUP] Session restore error: {e}")
        
        # Delay slightly to ensure UI is ready
        self.after(500, lambda: threading.Thread(target=do_restore, daemon=True).start())
    
    def _check_for_updates(self):
        """Check for launcher updates on startup"""
        def do_check():
            result = self.online.check_update(LAUNCHER_VERSION)
            if result["success"]:
                data = result["data"]
                server_version = data.get("latest_version", "0.0.0")
                # Only show update if server version is actually newer
                if data.get("update_available") and self._is_newer_version(server_version, LAUNCHER_VERSION):
                    self.after(0, lambda: self._show_update_notification(data))
        
        # Check after 2 seconds delay
        self.after(2000, lambda: threading.Thread(target=do_check, daemon=True).start())
    
    def _is_newer_version(self, server_ver, local_ver):
        """Compare version strings (e.g., '2.1.1' > '2.1.0')"""
        try:
            server_parts = [int(x) for x in server_ver.split('.')]
            local_parts = [int(x) for x in local_ver.split('.')]
            return server_parts > local_parts
        except:
            return False
    
    def _show_update_notification(self, update_data):
        """Show update available notification"""
        self.update_data = update_data
        
        # Create update notification bar at top
        self.update_bar = ctk.CTkFrame(self, fg_color="#004400", height=45)
        self.update_bar.place(relx=0, rely=0, relwidth=1)
        
        inner = ctk.CTkFrame(self.update_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20)
        
        ctk.CTkLabel(inner, text=f"🔄 Update available! v{update_data['latest_version']}", 
                    font=get_font(12, "bold"), text_color=COLORS["accent"]).pack(side="left", pady=10)
        
        if update_data.get("update_notes"):
            ctk.CTkLabel(inner, text=f" - {update_data['update_notes']}", 
                        font=get_font(10), text_color=COLORS["text2"]).pack(side="left", pady=10)
        
        AnimatedButton(inner, text="[ UPDATE NOW ]", font=get_font(11, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=30, width=120, corner_radius=6, glow_color=COLORS["terminal_green"],
            command=self._do_update).pack(side="right", pady=7)
        
        AnimatedButton(inner, text="[×]", font=get_font(12, "bold"),
            fg_color="transparent", hover_color=COLORS["error"], text_color=COLORS["text2"],
            height=30, width=30, corner_radius=6, glow_color=COLORS["error"],
            command=self._dismiss_update).pack(side="right", padx=(0, 10), pady=7)
    
    def _dismiss_update(self):
        """Dismiss update notification"""
        if hasattr(self, 'update_bar'):
            self.update_bar.destroy()
    
    def _do_update(self):
        """Download and apply update"""
        if not hasattr(self, 'update_data'):
            return
        
        self.notify("Downloading update...")
        
        def download():
            result = self.online.download_update(self.update_data["download_url"])
            if result["success"]:
                # Save new launcher
                try:
                    launcher_path = Path(__file__).resolve()
                    backup_path = launcher_path.with_suffix('.py.backup')
                    
                    # Create backup
                    import shutil
                    shutil.copy(launcher_path, backup_path)
                    
                    # Write new version
                    with open(launcher_path, 'w', encoding='utf-8') as f:
                        f.write(result["content"])
                    
                    self.after(0, lambda: self._update_complete())
                except Exception as e:
                    self.after(0, lambda: self.notify(f"Update failed: {str(e)[:30]}", True))
            else:
                self.after(0, lambda: self.notify(result.get("error", "Download failed"), True))
        
        threading.Thread(target=download, daemon=True).start()
    
    def _update_complete(self):
        """Show update complete message"""
        self._dismiss_update()
        
        # Show restart dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Update Complete")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS["bg_card"])
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 350) // 2
        y = self.winfo_y() + (self.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="✅ Update Downloaded!", font=get_font(16, "bold"),
                    text_color=COLORS["accent"]).pack(pady=(25, 10))
        ctk.CTkLabel(dialog, text="Restart the launcher to apply changes",
                    font=get_font(11), text_color=COLORS["text2"]).pack(pady=(0, 20))
        
        AnimatedButton(dialog, text="[ RESTART NOW ]", font=get_font(12, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=40, width=150, corner_radius=8, glow_color=COLORS["terminal_green"],
            command=lambda: self._restart_launcher()).pack()
    
    def _restart_launcher(self):
        """Restart the launcher"""
        import sys
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def _start_heartbeat(self):
        """Send periodic heartbeat to maintain online status"""
        def heartbeat():
            if self.is_logged_in:
                self.online.heartbeat()
            self.after(30000, heartbeat)  # Every 30 seconds
        
        self.after(5000, heartbeat)  # Start after 5 seconds
    
    def _update_account_ui(self):
        """Update account button and status indicator based on login state"""
        if self.is_logged_in and self.online.user:
            username = self.online.user.get("username", "User")
            self.account_btn.configure(text=f"[@]\n{username[:8]}")
            self.status_indicator.configure(text="● ONLINE", text_color=COLORS["success"])
        else:
            self.account_btn.configure(text="[?]\nLOGIN")
            self.status_indicator.configure(text="● OFFLINE", text_color=COLORS["error"])
    
    def _refresh_friends_data(self):
        """Refresh friends list and pending requests"""
        def do_refresh():
            if not self.is_logged_in:
                return
            
            # Get friends
            result = self.online.get_friends()
            if result["success"]:
                self.friends_list = result["data"].get("friends", [])
            
            # Get pending requests
            result = self.online.get_pending_requests()
            if result["success"]:
                self.pending_requests = {
                    "incoming": result["data"].get("incoming", []),
                    "outgoing": result["data"].get("outgoing", [])
                }
            
            # Update UI if on friends page
            if self.current_page == "friends":
                self.after(0, self.show_friends)
        
        threading.Thread(target=do_refresh, daemon=True).start()
    
    def show_account(self):
        """Show login/register or account page"""
        self.clear()
        
        if self.is_logged_in:
            self._show_account_logged_in()
        else:
            self._show_login_register()
    
    def _show_login_register(self):
        """Show login/register screen"""
        self._type_title(" ./authenticate")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "account" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "account" else COLORS["text3"])
        
        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 30))
        
        ascii_art = """
 ╔═══════════════════════════════════════════╗
 ║    WEJZ ONLINE AUTHENTICATION SYSTEM      ║
 ╚═══════════════════════════════════════════╝"""
        ctk.CTkLabel(header, text=ascii_art, font=(FONT_FALLBACK, 11), 
                    text_color=COLORS["accent"], justify="left").pack()
        
        # Main content - two columns
        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        # Login card
        login_card = ctk.CTkFrame(content, fg_color=COLORS["bg_medium"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"], width=400)
        login_card.pack(side="left", fill="y", padx=(0, 15), expand=True)
        login_inner = ctk.CTkFrame(login_card, fg_color="transparent")
        login_inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(login_inner, text="> LOGIN", font=get_font(16, "bold"), 
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(login_inner, text="USERNAME:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(anchor="w")
        self.login_username = ctk.CTkEntry(login_inner, fg_color=COLORS["bg_dark"], 
            border_color=COLORS["border"], text_color=COLORS["text"], height=42, font=get_font(12))
        self.login_username.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(login_inner, text="PASSWORD:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(anchor="w")
        self.login_password = ctk.CTkEntry(login_inner, fg_color=COLORS["bg_dark"], 
            border_color=COLORS["border"], text_color=COLORS["text"], height=42, font=get_font(12), show="•")
        self.login_password.pack(fill="x", pady=(5, 20))
        self.login_password.bind("<Return>", lambda e: self._do_login())
        
        AnimatedButton(login_inner, text="[ LOGIN ]", font=get_font(14, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=50, corner_radius=8, glow_color=COLORS["terminal_green"],
            command=self._do_login).pack(fill="x")
        
        # Register card
        reg_card = ctk.CTkFrame(content, fg_color=COLORS["bg_medium"], corner_radius=10,
                               border_width=1, border_color=COLORS["border"], width=400)
        reg_card.pack(side="right", fill="y", padx=(15, 0), expand=True)
        reg_inner = ctk.CTkFrame(reg_card, fg_color="transparent")
        reg_inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(reg_inner, text="> REGISTER", font=get_font(16, "bold"), 
                    text_color=COLORS["accent2"]).pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(reg_inner, text="USERNAME:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(anchor="w")
        self.reg_username = ctk.CTkEntry(reg_inner, fg_color=COLORS["bg_dark"], 
            border_color=COLORS["border"], text_color=COLORS["text"], height=42, font=get_font(12))
        self.reg_username.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(reg_inner, text="PASSWORD:", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(anchor="w")
        self.reg_password = ctk.CTkEntry(reg_inner, fg_color=COLORS["bg_dark"], 
            border_color=COLORS["border"], text_color=COLORS["text"], height=42, font=get_font(12), show="•")
        self.reg_password.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(reg_inner, text="DISPLAY NAME (optional):", font=get_font(11), 
                    text_color=COLORS["text2"]).pack(anchor="w")
        self.reg_display = ctk.CTkEntry(reg_inner, fg_color=COLORS["bg_dark"], 
            border_color=COLORS["border"], text_color=COLORS["text"], height=42, font=get_font(12))
        self.reg_display.pack(fill="x", pady=(5, 20))
        self.reg_display.bind("<Return>", lambda e: self._do_register())
        
        AnimatedButton(reg_inner, text="[ CREATE ACCOUNT ]", font=get_font(14, "bold"),
            fg_color=COLORS["accent2"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=50, corner_radius=8, glow_color=COLORS["accent2"],
            command=self._do_register).pack(fill="x")
        
        # Info
        ctk.CTkLabel(inner, text="// Unique username required • 3-20 characters • Letters, numbers, underscores only",
            font=get_font(10), text_color=COLORS["text3"]).pack(pady=(20, 0))
    
    def _do_login(self):
        """Handle login"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            self.notify("Enter username and password!", True)
            return
        
        def do_login():
            result = self.online.login(username, password)
            if result["success"]:
                self.is_logged_in = True
                self.after(0, self._update_account_ui)
                self.after(0, lambda: self.notify(f"Welcome, {username}!"))
                self.after(0, lambda: self.nav("home"))
                self._refresh_friends_data()
            else:
                self.after(0, lambda: self.notify(result.get("error", "Login failed"), True))
        
        self.notify("Logging in...")
        threading.Thread(target=do_login, daemon=True).start()
    
    def _do_register(self):
        """Handle registration"""
        username = self.reg_username.get().strip()
        password = self.reg_password.get()
        display = self.reg_display.get().strip() or None
        
        if not username or not password:
            self.notify("Enter username and password!", True)
            return
        
        def do_register():
            result = self.online.register(username, password, display)
            if result["success"]:
                self.is_logged_in = True
                self.after(0, self._update_account_ui)
                self.after(0, lambda: self.notify(f"Account created! Welcome, {username}!"))
                self.after(0, lambda: self.nav("home"))
            else:
                self.after(0, lambda: self.notify(result.get("error", "Registration failed"), True))
        
        self.notify("Creating account...")
        threading.Thread(target=do_register, daemon=True).start()
    
    def _show_account_logged_in(self):
        """Show account page when logged in"""
        self._type_title(" ./account")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "account" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "account" else COLORS["text3"])
        
        user = self.online.user
        
        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        # User card
        card = ctk.CTkFrame(inner, fg_color=COLORS["bg_medium"], corner_radius=15,
                           border_width=2, border_color=COLORS["accent"])
        card.pack(fill="x", pady=(0, 25))
        card_inner = ctk.CTkFrame(card, fg_color="transparent")
        card_inner.pack(fill="x", padx=30, pady=30)
        
        # Avatar placeholder and info
        left = ctk.CTkFrame(card_inner, fg_color="transparent")
        left.pack(side="left", fill="y")
        
        avatar = ctk.CTkFrame(left, fg_color=COLORS["accent"], width=80, height=80, corner_radius=40)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=user["username"][0].upper(), font=get_font(32, "bold"),
                    text_color=COLORS["bg_dark"]).place(relx=0.5, rely=0.5, anchor="center")
        
        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left", padx=20)
        
        ctk.CTkLabel(info, text=user.get("display_name", user["username"]), 
                    font=get_font(20, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"@{user['username']}", 
                    font=get_font(12), text_color=COLORS["text3"]).pack(anchor="w")
        ctk.CTkLabel(info, text="● Online", 
                    font=get_font(11, "bold"), text_color=COLORS["success"]).pack(anchor="w", pady=(5, 0))
        
        # Logout button
        AnimatedButton(card_inner, text="[ LOGOUT ]", font=get_font(12, "bold"),
            fg_color=COLORS["error"], hover_color="#cc0000", text_color="white",
            height=45, width=120, corner_radius=8, glow_color=COLORS["error"],
            command=self._do_logout).pack(side="right")
        
        # Stats
        stats_frame = ctk.CTkFrame(inner, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 25))
        
        for title, value, color in [
            ("[FRIENDS]", str(len(self.friends_list)), COLORS["accent"]),
            ("[PENDING]", str(len(self.pending_requests.get("incoming", []))), COLORS["accent2"]),
            ("[SENT]", str(len(self.pending_requests.get("outgoing", []))), COLORS["text2"])
        ]:
            stat_card = AnimatedCard(stats_frame, fg_color=COLORS["bg_medium"], corner_radius=10,
                                    border_width=1, border_color=COLORS["border"], height=80,
                                    hover_border=color, hover_fg=COLORS["bg_light"])
            stat_card.pack(side="left", expand=True, fill="both", padx=(0, 10))
            stat_card.pack_propagate(False)
            
            stat_inner = ctk.CTkFrame(stat_card, fg_color="transparent")
            stat_inner.pack(fill="both", expand=True, padx=15, pady=15)
            ctk.CTkLabel(stat_inner, text=title, font=get_font(10), 
                        text_color=COLORS["text3"]).pack(anchor="w")
            ctk.CTkLabel(stat_inner, text=value, font=get_font(24, "bold"), 
                        text_color=color).pack(anchor="w")
        
        # Quick actions
        ctk.CTkLabel(inner, text="> QUICK_ACTIONS:", font=get_font(12, "bold"), 
                    text_color=COLORS["text2"]).pack(anchor="w", pady=(10, 15))
        
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")
        
        AnimatedButton(btn_row, text="[ VIEW FRIENDS ]", font=get_font(12, "bold"),
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"],
            height=50, corner_radius=8, glow_color=COLORS["accent"],
            command=lambda: self.nav("friends")).pack(side="left", padx=(0, 10))
        
        AnimatedButton(btn_row, text="[ REFRESH DATA ]", font=get_font(12, "bold"),
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"],
            height=50, corner_radius=8, glow_color=COLORS["accent"],
            command=self._refresh_friends_data).pack(side="left")
    
    def _do_logout(self):
        """Handle logout"""
        self.online.logout()
        self.is_logged_in = False
        self.friends_list = []
        self.pending_requests = {"incoming": [], "outgoing": []}
        self._update_account_ui()
        self.notify("Logged out successfully")
        self.nav("home")
    
    def show_friends(self):
        """Show friends page"""
        self.clear()
        self._type_title(" ./friends")
        for k, b in self.nav_btns.items():
            b.configure(fg_color=COLORS["accent"] if k == "friends" else "transparent",
                       text_color=COLORS["bg_dark"] if k == "friends" else COLORS["text3"])
        
        if not self.is_logged_in:
            self._show_friends_login_required()
            return
        
        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Tab bar
        tabs = ctk.CTkFrame(inner, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 15))
        
        self.friend_tab_btns = {}
        for tab, txt, count_key in [
            ("friends", "[FRIENDS]", "friends_list"),
            ("pending", "[PENDING]", "incoming"),
            ("add", "[ADD FRIEND]", None)
        ]:
            is_sel = tab == self.friends_tab
            count = ""
            if count_key == "friends_list":
                count = f" ({len(self.friends_list)})"
            elif count_key == "incoming":
                count = f" ({len(self.pending_requests.get('incoming', []))})"
            
            btn = AnimatedButton(tabs, text=f"{txt}{count}", font=get_font(11, "bold" if is_sel else "normal"),
                fg_color=COLORS["accent"] if is_sel else COLORS["bg_medium"],
                hover_color=COLORS["accent_hover"] if is_sel else COLORS["bg_light"],
                text_color=COLORS["bg_dark"] if is_sel else COLORS["text2"],
                height=40, corner_radius=8, border_width=1,
                border_color=COLORS["accent"] if is_sel else COLORS["border"],
                glow_color=COLORS["accent"],
                command=lambda t=tab: self._switch_friends_tab(t))
            btn.pack(side="left", padx=(0, 8))
            self.friend_tab_btns[tab] = btn
        
        # Refresh button
        AnimatedButton(tabs, text="[↻]", font=get_font(14, "bold"),
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"],
            height=40, width=45, corner_radius=8, glow_color=COLORS["accent"],
            command=self._refresh_friends_data).pack(side="right")
        
        # Content area
        self.friends_content = ctk.CTkScrollableFrame(inner, fg_color="transparent")
        self.friends_content.pack(fill="both", expand=True)
        
        self._display_friends_tab()
    
    def _switch_friends_tab(self, tab):
        """Switch between friends tabs"""
        self.friends_tab = tab
        for t, btn in self.friend_tab_btns.items():
            is_sel = t == tab
            btn.configure(
                fg_color=COLORS["accent"] if is_sel else COLORS["bg_medium"],
                text_color=COLORS["bg_dark"] if is_sel else COLORS["text2"],
                border_color=COLORS["accent"] if is_sel else COLORS["border"],
                font=get_font(11, "bold" if is_sel else "normal")
            )
        self._display_friends_tab()
    
    def _display_friends_tab(self):
        """Display content for current friends tab"""
        for w in self.friends_content.winfo_children():
            w.destroy()
        
        if self.friends_tab == "friends":
            self._display_friends_list()
        elif self.friends_tab == "pending":
            self._display_pending_requests()
        elif self.friends_tab == "add":
            self._display_add_friend()
    
    def _display_friends_list(self):
        """Display friends list with enhanced features"""
        # Stats header
        online_count = sum(1 for f in self.friends_list if f.get("is_online"))
        total_count = len(self.friends_list)
        
        stats_frame = ctk.CTkFrame(self.friends_content, fg_color=COLORS["bg_medium"], 
                                   corner_radius=8, height=50)
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.pack_propagate(False)
        
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="both", expand=True, padx=15)
        
        ctk.CTkLabel(stats_inner, text=f"Friends: {total_count}", font=get_font(12, "bold"),
                    text_color=COLORS["text"]).pack(side="left", pady=12)
        ctk.CTkLabel(stats_inner, text=f"  |  ", font=get_font(12),
                    text_color=COLORS["text3"]).pack(side="left")
        ctk.CTkLabel(stats_inner, text=f"● {online_count} Online", font=get_font(11),
                    text_color=COLORS["success"]).pack(side="left")
        ctk.CTkLabel(stats_inner, text=f"  ● {total_count - online_count} Offline", font=get_font(11),
                    text_color=COLORS["error"]).pack(side="left")
        
        if not self.friends_list:
            empty_frame = ctk.CTkFrame(self.friends_content, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True)
            ctk.CTkLabel(empty_frame, text="No friends yet", font=get_font(16, "bold"),
                        text_color=COLORS["text3"]).pack(pady=(50, 10))
            ctk.CTkLabel(empty_frame, text="Go to ADD FRIEND tab to add friends!",
                        font=get_font(11), text_color=COLORS["text3"]).pack()
            return
        
        # Sort: online friends first
        sorted_friends = sorted(self.friends_list, key=lambda x: (not x.get("is_online"), x["username"].lower()))
        
        for idx, friend in enumerate(sorted_friends):
            card = ctk.CTkFrame(self.friends_content, fg_color=COLORS["bg_medium"], corner_radius=10,
                               height=80, border_width=1, 
                               border_color=COLORS["accent"] if friend["is_online"] else COLORS["border"])
            card.pack(fill="x", pady=3)
            card.pack_propagate(False)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=15, pady=10)
            
            # Avatar with online indicator
            avatar_frame = ctk.CTkFrame(inner, fg_color="transparent", width=50)
            avatar_frame.pack(side="left")
            avatar_frame.pack_propagate(False)
            
            avatar = ctk.CTkFrame(avatar_frame, fg_color=COLORS["accent"] if friend["is_online"] else COLORS["text3"],
                                 width=45, height=45, corner_radius=22)
            avatar.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(avatar, text=friend["username"][0].upper(), font=get_font(18, "bold"),
                        text_color=COLORS["bg_dark"]).place(relx=0.5, rely=0.5, anchor="center")
            
            # Info section
            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", padx=15, fill="y")
            
            # Username and display name
            name_frame = ctk.CTkFrame(info, fg_color="transparent")
            name_frame.pack(anchor="w")
            ctk.CTkLabel(name_frame, text=friend.get("display_name") or friend["username"], 
                        font=get_font(13, "bold"), text_color=COLORS["text"]).pack(side="left")
            if friend.get("display_name") and friend["display_name"] != friend["username"]:
                ctk.CTkLabel(name_frame, text=f"  @{friend['username']}", 
                            font=get_font(10), text_color=COLORS["text3"]).pack(side="left")
            
            # Status with last seen
            status_frame = ctk.CTkFrame(info, fg_color="transparent")
            status_frame.pack(anchor="w", pady=(3, 0))
            
            if friend["is_online"]:
                ctk.CTkLabel(status_frame, text="● Online now", font=get_font(10, "bold"), 
                            text_color=COLORS["success"]).pack(side="left")
            else:
                ctk.CTkLabel(status_frame, text="● Offline", font=get_font(10), 
                            text_color=COLORS["error"]).pack(side="left")
                # Show last online time if available
                if friend.get("last_online"):
                    last_online = friend["last_online"]
                    ctk.CTkLabel(status_frame, text=f"  •  Last seen: {last_online[:10]}", 
                                font=get_font(9), text_color=COLORS["text3"]).pack(side="left")
            
            # Action buttons
            btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
            btn_frame.pack(side="right")
            
            # Remove button
            AnimatedButton(btn_frame, text="[REMOVE]", font=get_font(10, "bold"),
                fg_color=COLORS["bg_light"], hover_color=COLORS["error"], text_color=COLORS["text2"],
                width=80, height=32, corner_radius=6, glow_color=COLORS["error"],
                command=lambda u=friend["username"]: self._remove_friend(u)).pack()
    
    def _display_pending_requests(self):
        """Display pending friend requests"""
        incoming = self.pending_requests.get("incoming", [])
        outgoing = self.pending_requests.get("outgoing", [])
        
        if not incoming and not outgoing:
            ctk.CTkLabel(self.friends_content, text="No pending requests", 
                        font=get_font(12), text_color=COLORS["text3"]).pack(pady=50)
            return
        
        # Incoming requests
        if incoming:
            ctk.CTkLabel(self.friends_content, text="> INCOMING_REQUESTS:", font=get_font(12, "bold"),
                        text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 10))
            
            for req in incoming:
                card = AnimatedCard(self.friends_content, fg_color=COLORS["bg_medium"], corner_radius=10,
                                   height=70, border_width=1, border_color=COLORS["accent2"],
                                   hover_border=COLORS["accent"], hover_fg=COLORS["bg_light"])
                card.pack(fill="x", pady=3)
                card.pack_propagate(False)
                
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="both", expand=True, padx=15, pady=10)
                
                ctk.CTkLabel(inner, text=req.get("display_name") or req["username"], 
                            font=get_font(13, "bold"), text_color=COLORS["text"]).pack(side="left")
                ctk.CTkLabel(inner, text=f"  @{req['username']}", 
                            font=get_font(11), text_color=COLORS["text3"]).pack(side="left")
                
                # Buttons
                AnimatedButton(inner, text="[✓]", font=get_font(14, "bold"),
                    fg_color=COLORS["success"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
                    width=40, height=35, corner_radius=8, glow_color=COLORS["success"],
                    command=lambda u=req["username"]: self._accept_friend(u)).pack(side="right", padx=(5, 0))
                
                AnimatedButton(inner, text="[×]", font=get_font(14, "bold"),
                    fg_color=COLORS["error"], hover_color="#cc0000", text_color="white",
                    width=40, height=35, corner_radius=8, glow_color=COLORS["error"],
                    command=lambda u=req["username"]: self._decline_friend(u)).pack(side="right")
        
        # Outgoing requests
        if outgoing:
            ctk.CTkLabel(self.friends_content, text="> SENT_REQUESTS:", font=get_font(12, "bold"),
                        text_color=COLORS["text2"]).pack(anchor="w", pady=(20 if incoming else 0, 10))
            
            for req in outgoing:
                card = ctk.CTkFrame(self.friends_content, fg_color=COLORS["bg_medium"], corner_radius=10,
                                   height=60, border_width=1, border_color=COLORS["border"])
                card.pack(fill="x", pady=3)
                card.pack_propagate(False)
                
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="both", expand=True, padx=15, pady=10)
                
                ctk.CTkLabel(inner, text=req.get("display_name") or req["username"], 
                            font=get_font(12), text_color=COLORS["text"]).pack(side="left")
                ctk.CTkLabel(inner, text="  (pending)", 
                            font=get_font(10), text_color=COLORS["text3"]).pack(side="left")
                
                AnimatedButton(inner, text="[CANCEL]", font=get_font(10, "bold"),
                    fg_color=COLORS["bg_light"], hover_color=COLORS["error"], text_color=COLORS["text2"],
                    width=70, height=30, corner_radius=6, glow_color=COLORS["error"],
                    command=lambda u=req["username"]: self._cancel_request(u)).pack(side="right")
    
    def _display_add_friend(self):
        """Display add friend UI"""
        # Search input
        search_frame = ctk.CTkFrame(self.friends_content, fg_color=COLORS["bg_medium"], corner_radius=10,
                                   border_width=1, border_color=COLORS["border"])
        search_frame.pack(fill="x", pady=(0, 20))
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(search_inner, text="> ADD_FRIEND_BY_USERNAME:", font=get_font(12, "bold"),
                    text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 15))
        
        row = ctk.CTkFrame(search_inner, fg_color="transparent")
        row.pack(fill="x")
        
        self.add_friend_entry = ctk.CTkEntry(row, fg_color=COLORS["bg_dark"], 
            border_color=COLORS["border"], text_color=COLORS["text"], height=45, 
            font=get_font(12), placeholder_text="Enter username...")
        self.add_friend_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.add_friend_entry.bind("<Return>", lambda e: self._send_friend_request())
        
        AnimatedButton(row, text="[ SEND REQUEST ]", font=get_font(12, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=45, width=150, corner_radius=8, glow_color=COLORS["terminal_green"],
            command=self._send_friend_request).pack(side="right")
        
        ctk.CTkLabel(search_inner, text="// Username is case-insensitive",
                    font=get_font(10), text_color=COLORS["text3"]).pack(anchor="w", pady=(10, 0))
    
    def _send_friend_request(self):
        """Send a friend request"""
        username = self.add_friend_entry.get().strip()
        if not username:
            self.notify("Enter a username!", True)
            return
        
        def do_send():
            result = self.online.add_friend(username)
            if result["success"]:
                self.after(0, lambda: self.notify(f"Request sent to {username}!"))
                self.after(0, lambda: self.add_friend_entry.delete(0, "end"))
                self._refresh_friends_data()
            else:
                self.after(0, lambda: self.notify(result.get("error", "Failed to send request"), True))
        
        threading.Thread(target=do_send, daemon=True).start()
    
    def _accept_friend(self, username):
        """Accept a friend request"""
        def do_accept():
            result = self.online.accept_friend(username)
            if result["success"]:
                self.after(0, lambda: self.notify(f"You are now friends with {username}!"))
                self._refresh_friends_data()
            else:
                self.after(0, lambda: self.notify(result.get("error", "Failed"), True))
        
        threading.Thread(target=do_accept, daemon=True).start()
    
    def _decline_friend(self, username):
        """Decline a friend request"""
        def do_decline():
            result = self.online.decline_friend(username)
            if result["success"]:
                self.after(0, lambda: self.notify("Request declined"))
                self._refresh_friends_data()
            else:
                self.after(0, lambda: self.notify(result.get("error", "Failed"), True))
        
        threading.Thread(target=do_decline, daemon=True).start()
    
    def _remove_friend(self, username):
        """Remove a friend"""
        def do_remove():
            result = self.online.remove_friend(username)
            if result["success"]:
                self.after(0, lambda: self.notify(f"Removed {username}"))
                self._refresh_friends_data()
            else:
                self.after(0, lambda: self.notify(result.get("error", "Failed"), True))
        
        threading.Thread(target=do_remove, daemon=True).start()
    
    def _cancel_request(self, username):
        """Cancel a sent friend request"""
        def do_cancel():
            result = self.online.cancel_request(username)
            if result["success"]:
                self.after(0, lambda: self.notify("Request cancelled"))
                self._refresh_friends_data()
            else:
                self.after(0, lambda: self.notify(result.get("error", "Failed"), True))
        
        threading.Thread(target=do_cancel, daemon=True).start()
    
    def _show_friends_login_required(self):
        """Show message when not logged in"""
        inner = ctk.CTkFrame(self.main, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(inner, text="[ LOGIN REQUIRED ]", font=get_font(20, "bold"),
                    text_color=COLORS["accent"]).pack(pady=(100, 20))
        ctk.CTkLabel(inner, text="You need to login to access friends features",
                    font=get_font(12), text_color=COLORS["text2"]).pack(pady=(0, 30))
        
        AnimatedButton(inner, text="[ LOGIN / REGISTER ]", font=get_font(14, "bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color=COLORS["bg_dark"],
            height=55, width=200, corner_radius=10, glow_color=COLORS["terminal_green"],
            command=lambda: self.nav("account")).pack()

    def notify(self, msg, error=False):
        """Animated notification with slide-in and slide-out"""
        n = ctk.CTkFrame(self, fg_color=COLORS["error"] if error else COLORS["accent"], 
                        corner_radius=8, border_width=2, 
                        border_color="#ff3333" if error else COLORS["terminal_green"])
        
        text_color = "white" if error else COLORS["bg_dark"]
        prefix = "[ERROR]" if error else "[OK]"
        ctk.CTkLabel(n, text=f" {prefix} {msg} ", font=get_font(12, "bold"), 
                    text_color=text_color).pack(padx=20, pady=12)
        
        # Start above screen and slide down
        n.place(relx=0.5, y=-60, anchor="n")
        self.update_idletasks()
        
        # Slide in animation
        def slide_in(current_y=-60, target_y=40):
            if current_y < target_y:
                # Ease out cubic
                progress = (current_y + 60) / (target_y + 60)
                eased_step = max(4, int(15 * (1 - progress)))
                new_y = current_y + eased_step
                n.place_configure(y=min(new_y, target_y))
                self.after(16, lambda: slide_in(min(new_y, target_y), target_y))
            else:
                # Hold then slide out
                self.after(2000, lambda: slide_out(target_y))
        
        # Slide out animation
        def slide_out(current_y=40):
            if current_y > -80:
                n.place_configure(y=current_y - 12)
                self.after(16, lambda: slide_out(current_y - 12))
            else:
                n.destroy()
        
        slide_in()

    def update_prog(self, msg, val):
        if hasattr(self, 'play_prog_label') and self.current_page == "play":
            self.play_prog_label.configure(text=msg)
            if val is not None:
                self._animate_progress(self.play_prog_bar, val)
        if hasattr(self, 'home_prog_label') and self.current_page == "home":
            self.home_prog_label.configure(text=msg)
            if val is not None:
                self._animate_progress(self.home_prog_bar, val)
    
    def _animate_progress(self, bar, target_val):
        """Set progress instantly - no animation"""
        try:
            bar.set(target_val)
        except:
            pass
        except:
            pass
    
    def _start_progress_glow(self, bar):
        """Pulsing glow effect on progress bar during download"""
        if not self.is_launching:
            return
        try:
            colors = [COLORS["accent"], COLORS["terminal_green"]]
            self._prog_glow_step = getattr(self, '_prog_glow_step', 0)
            color = colors[self._prog_glow_step % len(colors)]
            bar.configure(progress_color=color)
            self._prog_glow_step += 1
            if self.is_launching:
                self.after(400, lambda: self._start_progress_glow(bar))
            else:
                bar.configure(progress_color=COLORS["accent"])
        except:
            pass

    def launch(self):
        if self.is_launching:
            return
        
        if not self.username.strip():
            self.notify("ERROR: Set username first!", True)
            return

        self.is_launching = True
        prof = self.profiles.get(self.current_profile)
        if not prof:
            self.notify("ERROR: Invalid profile!", True)
            self.is_launching = False
            return

        # Show progress with animation
        if self.current_page == "play" and hasattr(self, 'play_prog_frame'):
            self.play_prog_frame.pack(pady=(0, 10))
            self.play_launch_btn.configure(state="disabled", text="[ LOADING... ]")
            self._start_progress_glow(self.play_prog_bar)
        if self.current_page == "home" and hasattr(self, 'home_prog_frame'):
            self.home_prog_frame.pack(anchor="w", fill="x", pady=(10, 0))
            self.home_launch_btn.configure(state="disabled", text="[ LOADING ]")
            self._start_progress_glow(self.home_prog_bar)

        def do_launch():
            try:
                game_dir = self.settings["game_dir"]
                version = prof["version"]
                loader = prof.get("loader", "fabric")
                ram = prof.get("ram", 4)
                java = self.settings.get("java", "java")

                def prog(m, v):
                    self.after(0, lambda: self.update_prog(m, v))

                dl = GameDownloader(game_dir, prog)

                ver_info = dl.download_vanilla(version)
                if not ver_info:
                    self.after(0, lambda: self.notify("ERROR: Download failed!", True))
                    self.after(0, self.reset_launch)
                    return

                fab_profile = None
                if loader == "fabric":
                    fab_profile = dl.install_fabric(version)
                    
                    # Auto-install Fabric API if enabled
                    if prof.get("fabric_api", True):
                        dl.install_fabric_api(version)

                if prof["mods"] and loader == "fabric":
                    prog("[MODS] Installing...", 0.92)
                    mods_dir = Path(game_dir) / "mods"
                    mods_dir.mkdir(parents=True, exist_ok=True)

                    for mod in prof["mods"]:
                        slug = mod.get("slug")
                        if slug and not mod.get("filename"):
                            versions = ModrinthAPI.get_versions(slug, version)
                            if versions:
                                files = versions[0].get("files", [])
                                if files:
                                    url = files[0].get("url")
                                    fname = files[0].get("filename")
                                    if url and fname:
                                        dest = mods_dir / fname
                                        if not dest.exists():
                                            prog(f"[MOD] {mod['name'][:20]}...", 0.93)
                                            ModrinthAPI.download(url, dest)
                                        mod["filename"] = fname
                    self.profiles.save()

                prog("[EXECUTE] Starting...", 0.98)
                time.sleep(0.3)

                cmd = dl.get_launch_cmd(ver_info, self.username, ram, java, fab_profile)

                try:
                    if platform.system() == 'Windows':
                        subprocess.Popen(cmd, cwd=game_dir, creationflags=0x08000000)
                    else:
                        subprocess.Popen(cmd, cwd=game_dir)

                    loader_txt = f" + {loader.upper()}" if loader == "fabric" else ""
                    self.after(0, lambda: self.notify(f"LAUNCHED: MC {version}{loader_txt}"))

                except FileNotFoundError:
                    self.after(0, lambda: self.notify("ERROR: Java not found!", True))
                except Exception as e:
                    self.after(0, lambda: self.notify(f"ERROR: {str(e)[:40]}", True))

                self.after(0, self.reset_launch)

            except Exception as e:
                print(f"Launch error: {e}")
                import traceback
                traceback.print_exc()
                self.after(0, lambda: self.notify(f"ERROR: {str(e)[:40]}", True))
                self.after(0, self.reset_launch)

        threading.Thread(target=do_launch, daemon=True).start()

    def reset_launch(self):
        self.is_launching = False
        if self.current_page == "play" and hasattr(self, 'play_prog_frame'):
            self.play_prog_frame.pack_forget()
            self.play_launch_btn.configure(state="normal", text="[ EXECUTE MINECRAFT ]")
            self.play_prog_bar.set(0)
        if self.current_page == "home" and hasattr(self, 'home_prog_frame'):
            self.home_prog_frame.pack_forget()
            self.home_launch_btn.configure(state="normal", text="[ EXECUTE ]")
            self.home_prog_bar.set(0)

    def destroy(self):
        """Clean up on close"""
        if hasattr(self, 'matrix_rain'):
            self.matrix_rain.stop()
        super().destroy()


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
