import os
import importlib
import sqlite3
import threading
import time
import socket
import re
import requests
from dotenv import load_dotenv
from dependants.reply import reply
from dependants.webserver import start_web
from dependants.consolechat import console_input_loop
from dependants.request import send_request
from dependants.loader import loader

# -------------------- LOAD ENV --------------------
load_dotenv()

# -------------------- GLOBAL VARIABLES --------------------
conn = None
cursor = None

IP = "104.236.25.60"
API_URL = f"http://{IP}:3072/api"
TCP_PORT = 4040
BOT_API_PORT = 7871
print("I'm gonna learn spanish now!")

CONFIG = {
    "webonly": False,
    "username": os.getenv("username") or "default_bot",
    "password": os.getenv("password") or "default_password"
}

# Event used to control run state instead of uncontrolled while True loops
run_event = threading.Event()

# -------------------- COMMANDS --------------------

commands = []
commands = loader()
print(commands)

def handle_message(content, ctx):
    msg = content.lower().strip()
    if msg.startswith("/"):
        msg = msg[1:]
        for cmd in commands:
            triggers = getattr(cmd, "COMMANDS", [getattr(cmd, "COMMAND", None)])
            if triggers:
                for trigger in triggers:
                    if msg.startswith(trigger): 
                        if getattr(cmd, "ARGS", False):
                            comd.run(ctx, msg)
                        cmd.run(ctx)
                        return

# -------------------- BOT START --------------------
def start_bot():
    print("Starting bot...")
    send_request({"cmd": "CONNECT", "version": "1.0", "platform": "BOT"})
    send_request({"cmd": "LOGINACC", "username": CONFIG["username"], "password": CONFIG["password"]})

    global conn, cursor
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        AUusername TEXT UNIQUE,
                        Discordusername TEXT UNIQUE,
                        bio TEXT,
                        friend_code_3ds INTEGER,
                        messages_sent INTEGER DEFAULT 0,
                        display TEXT,
                        badges TEXT DEFAULT '',
                        email TEXT,
                        can_assign_badges INTEGER DEFAULT 0,
                        owner BOOLEAN DEFAULT 0,
                        pointless_hexadecimal TEXT UNIQUE,
                        banned BOOLEAN DEFAULT 0,
                        read_only BOOLEAN DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
                        TOKEN TEXT PRIMARY KEY UNIQUE,
                        developer TEXT UNIQUE,
                        bypass_rate_limit INTEGER DEFAULT 0,
                        write INTEGER DEFAULT 0,
                        read_email INTEGER DEFAULT 0,
                        last_used INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS internalsettings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_name TEXT UNIQUE,
                        setting_value TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pokemen (
                        staff TEXT UNIQUE,
                        rarity integer,
                        description TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pokemen_inventory (
                        user TEXT UNIQUE,
                        staff TEXT DEFAULT '{}',
                        last_hunt INTEGER DEFAULT 0
                    )''')

    conn.commit()
    web = start_web()
    if CONFIG.get("webonly"):
        reply("Aurith is online in web-only mode!", CONFIG)
        print("Web server running (web-only mode). Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            reply("Aurith shutting down (web-only mode)", CONFIG)
        return

    # -------------------- THREADS --------------------
    run_event.set()
    threading.Thread(target=console_input_loop, args=(run_event,), daemon=True).start()

    # -------------------- TCP CONNECTION --------------------
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(5.0)
    try:
        s.connect((IP, TCP_PORT))
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    s.settimeout(1.0)
    print("Connected to TCP server")
    try:
        while run_event.is_set():
            try:
                data = s.recv(4096)
                if not data:
                    break
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Socket error: {e}")
                break

            raw_msg = data.decode("utf-8", errors="ignore").strip()
            print(f"[CHAT] {raw_msg}")

            # -------------------- MESSAGE PARSING --------------------
            message_type = "CHAT"
            receiver = None
            platform = None
            username = CONFIG["username"]
            content = raw_msg

            # new format: CHAT|TAG|USERNAME|MESSAGE or DM|RECEIVER|TAG|USERNAME|MESSAGE
            if raw_msg.startswith("CHAT|") or raw_msg.startswith("DM|"):
                parts = raw_msg.split("|")
                if raw_msg.startswith("DM|") and len(parts) >= 5:
                    message_type = "DM"
                    receiver = parts[1]
                    platform = parts[2]
                    username = parts[3]
                    content = "|".join(parts[4:])
                elif raw_msg.startswith("CHAT|") and len(parts) >= 4:
                    message_type = "CHAT"
                    platform = parts[1]
                    username = parts[2]
                    content = "|".join(parts[3:])
            else:
                # legacy parsing
                parts = raw_msg.split(": ")
                if len(parts) >= 2:
                    content = parts[-1].strip("'")
                    candidate = parts[-2].strip().replace('<','').replace('>','')
                    tokens = re.split(r'[\s\(\)\[\]\{\}]+', candidate)
                    username = next((t for t in reversed(tokens) if t), CONFIG["username"])
                    try:
                        platform_match = re.search(r'\(([^)]+)\)', parts[-2])
                        if platform_match:
                            platform_type = platform_match.group(1).strip().lower()
                            if platform_type == "discord":
                                platform = "Discord"
                            elif platform_type in ("wiiu", "wii u"):
                                platform = "Wii U"
                            else:
                                platform = platform_type
                    except Exception:
                        platform = None

            # skip messages from self
            if username == CONFIG["username"]:
                if platform not in ('Discord', 'Fluxer'):
                    try:
                        exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                        if exists:
                            cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE AUusername=?", (username,))
                            conn.commit()
                    except Exception as e:
                        print(f"Failed to update message count for self: {e}")
                continue

            # only process DM if bot is receiver
            if message_type == "DM" and receiver != CONFIG["username"]:
                continue

            # -------------------- DISPATCH --------------------
            handle_message(content, ctx={"username": username, "platform": platform, "receiver": receiver})
    except KeyboardInterrupt:
        run_event.clear()
        print("\nShutting down...")
        # reply("Aurith is shutting down, likely to restart")
    finally:
        try:
            stop_event.set()
            web.join()
            thread.join()
            s.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        print("Aurith has shut down.")

if __name__ == "__main__":
    start_bot()