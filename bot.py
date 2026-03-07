import socket
import time
import threading
import sys
import threading
import sys
import requests
import sqlite3 #im finna chatgpt sqlite3
import re

IP = "104.236.25.60"
API_URL = f"http://{IP}:3072/api"
TCP_PORT = 4040
print("I'm gonna learn spanish now!")

CONFIG = {
    "username": "Username",
    "password": "Password",
    "platform": "BOT"
}

# Event used to control run state instead of uncontrolled while True loops
run_event = threading.Event()
def send_request(payload):
    try:
        requests.post(API_URL, json=payload, headers={'User-Agent': 'PyBot'}, timeout=5)
    except:
        pass

def reply(text):
    time.sleep(0.5)
    send_request({
        "cmd": "CHAT",
        "content": text,
        "username": CONFIG["username"],
        "password": CONFIG["password"],
        "platform": CONFIG["platform"]
    })

def console_input_loop(event: threading.Event):
    """Read lines from the console and send them to chat while `event` is set."""
    while event.is_set():
        try:
            line = input()
        except EOFError:
            break
        if not line:
            continue
        # allow a local quit command
        if line.strip() in ("/quit", ":q", "exit"):
            reply("Aurith is shutting down (console command)")
            # clear the event to signal shutdown
            try:
                event.clear()
            except Exception:
                pass
            try:
                sys.exit(0)
            except SystemExit:
                break
        reply(line)

# (Duplicate console loop removed)

def start_bot():
    print("Iniciando bot...")
    send_request({"cmd": "CONNECT", "version": "1.0", "platform": "BOT"})
    send_request({"cmd": "LOGINACC", "username": CONFIG["username"], "password": CONFIG["password"]})
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        display TEXT,
                        AUusername TEXT UNIQUE,
                        Discordusername TEXT UNIQUE,
                        bio TEXT,
                        friend_code_3ds integer,
                        messages_sent integer DEFAULT 0,
                        badges TEXT DEFAULT '',
                        can_assign_badges INTEGER DEFAULT 0,
                        owner INTEGER DEFAULT 0
                    )''')
    conn.commit()
    reply("Aurith is online!")
    # start console input thread
    run_event.set()
    console_thread = threading.Thread(target=console_input_loop, args=(run_event,), daemon=True)
    console_thread.start()

    try:
        # single attempt: connect once and read until disconnect or shutdown
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(5.0)
        try:
            s.connect((IP, TCP_PORT))
        except Exception as e:
            print(f"Connection failed: {e}")
            s.close()
            return

        print("Conectado al servidor TCP")
        s.settimeout(1.0)

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

            try:
                raw_msg = data.decode("utf-8", errors="ignore").strip()
                print(f"[CHAT] {raw_msg}")

                if CONFIG["username"] in raw_msg:
                    continue

                parts = raw_msg.split(": ")
                content = parts[-1] if len(parts) >= 2 else raw_msg

                # Try to infer the username from the message before the final ': '
                username = CONFIG["username"]
                platform = None
                if len(parts) >= 2:
                    candidate = parts[-2].strip()
                    candidate = candidate.replace('<', '').replace('>', '')
                    tokens = re.split(r'[\s\(\)\[\]\{\}]+', candidate.strip())
                    username = next((t for t in reversed(tokens) if t), CONFIG["username"])

                    try:
                        platform_match = re.search(r'\(([^)]+)\)', parts[-2])
                        if platform_match:
                            platform_type = platform_match.group(1).strip()
                            norm = re.sub(r'[^a-z0-9]', '', platform_type.lower())
                            if norm == 'int':
                                platform = None
                            elif norm == 'wiiu' or platform_type == 'Wii U':
                                platform = 'Wii U'
                            else:
                                platform = platform_type.lower()
                    except Exception as e:
                        print(f"Error extracting platform: {e}")
                        platform = None

                # command handling (unchanged logic)
                if content.lower().strip() == "/at hello":
                    reply("Hello, Im Dr. Sex")
                elif content.lower().strip() == "/at help":
                    reply("Available commands: DO THIS FIRST: /at register\n/at credits, /at profile [username], /at setbio [bio], /at setfc [friend code], /at setdisplayname [display name]\nuse /au help for the regular bot's commands")
                elif content.lower().strip() == "/at credits":
                    reply("Made by: Lmutt090 (<https://lmutt090.me>) and ClaudiWolf (<https://www.claudiwolf2056.com/>)") # Please do not remove the credits from these people, atleast to the people who fork this...
                elif content.lower().strip().startswith("/at profile "):
                    musername = content[12:].strip()
                    if not musername:
                        musername = username

                    cursor.execute("SELECT * FROM users WHERE AUusername=?", (musername,))
                    user = cursor.fetchone()
                    if user:
                        profile = None
                        if user[6]:
                            profile = f"{user[6]}\n{musername}'s profile:"
                        if user[3]:
                            if profile:
                                profile += f"\nBio: {user[3]}"
                            else:
                                profile = f"{musername}'s profile:\nBio: {user[3]}"
                        if user[4]:
                            try:
                                fc = str(user[4])
                                fc_digits = ''.join(ch for ch in fc if ch.isdigit())
                                fc_digits = fc_digits.zfill(12)
                                fc_display = f"{fc_digits[0:4]}-{fc_digits[4:8]}-{fc_digits[8:12]}"
                            except Exception:
                                fc_display = str(user[4])
                            if profile:
                                profile += f"\nFriend Code: {fc_display}"
                            else:
                                profile = f"{musername}'s profile:\nFriend Code: {fc_display}"
                        if user[5]:
                            if user[5] > 0 and user[5] < 10:
                                if profile:
                                    profile += f"\nStatus: Newcomer"
                                else:
                                    profile = f"{musername}'s profile:\nStatus: Newcomer"
                            elif user[5] >= 10 and user[5] < 50:
                                if profile:
                                    profile += f"\nStatus: New but sent more than 10 messages"
                                else:
                                    profile = f"{musername}'s profile:\nStatus: New but sent more than 10 messages"
                            elif user[5] >= 50 and user[5] < 100:
                                if profile:
                                    profile += f"\nStatus: Regular"
                                else:
                                    profile = f"{musername}'s profile:\nStatus: Regular"
                            elif user[5] >= 500:
                                if profile:
                                    profile += f"\nStatus: Veteran"
                                else:
                                    profile = f"{musername}'s profile:\nStatus: Veteran"
                        if profile:
                            reply(profile)
                        else:
                            reply(f"{username}'s profile doesn't exist")
                    else:
                        reply("No profile found.")
                elif content.lower().strip() == "/at whoami":
                    reply(f"You are {username} on {platform if platform else 'A platform I cant detect... i\'m just gonna guess youse on discord'}")
                elif content.lower().strip() == "/at register":
                    if platform:
                        try:
                            cursor.execute("INSERT INTO users (AUusername) VALUES (?)", (username,))
                            conn.commit()
                            reply(f"Registered {username} to AU profiles!\nUse /at setbio and /at setfc to set up your profile!\nNote: If you want your discord account linked, DM Lmutt090 with your AU username...")
                        except sqlite3.IntegrityError:
                            reply(f"{username} is already registered.")
                        except Exception as e:
                            reply(f"Error registering: {e}")
                    else:
                        reply("Contact Lmutt090 to register")
                elif content.lower().strip().startswith("/at setbio "):
                    bio = content[11:].strip()
                    if platform:
                        exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET bio=? WHERE AUusername=?", (bio, username))
                            conn.commit()
                            reply("Bio updated!")
                        else:
                            reply("You must register first!")
                    else:
                        exsists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET bio=? WHERE Discordusername=?", (bio, username))
                            conn.commit()
                            reply("Bio updated!")
                        else:
                            reply("You must register first!")
                elif content.lower().strip().startswith("/at setfc "):
                    fc_raw = content[10:].strip()
                    fc_digits = ''.join(ch for ch in fc_raw if ch.isdigit())
                    if len(fc_digits) != 12:
                        reply("Friend code must contain exactly 12 digits (format ####-####-####). Please try again.")
                    else:
                        if platform:
                            exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                            if exsists:
                                try:
                                    cursor.execute("UPDATE users SET friend_code_3ds=? WHERE AUusername=?", (fc_digits, username))
                                    conn.commit()
                                    reply("Friend code updated!")
                                except Exception as e:
                                    reply(f"Error updating friend code: {e}")
                            else:
                                reply("You must register first!")
                        else:
                            exsists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
                            if exsists:
                                try:
                                    cursor.execute("UPDATE users SET friend_code_3ds=? WHERE Discordusername=?", (fc_digits, username))
                                    conn.commit()
                                    reply("Friend code updated!")
                                except Exception as e:
                                    reply(f"Error updating friend code: {e}")
                            else:
                                reply("You must register first!")
                elif content.lower().strip() == "/at delete":
                    exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                    if exsists:
                        if platform:
                            cursor.execute("DELETE FROM users WHERE AUusername=?", (username,))
                        else:
                            cursor.execute("DELETE FROM users WHERE Discordusername=?", (username,))
                        conn.commit()
                        reply("You have been unregistered.")
                    else:
                        reply("You are not registered.")
                elif content.lower().strip().startswith("/at setdisplayname "):
                    new_name = content[19:].strip()
                    if platform:
                        exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                        if exsists:
                            try:
                                cursor.execute("UPDATE users SET display=? WHERE AUusername=?", (new_name, username))
                                conn.commit()
                                reply(f"Display name updated to {new_name}!")
                                username = new_name
                            except Exception as e:
                                reply(f"Error updating display name: {e}")
                        else:
                            reply("You must register first!")
                    else:
                        exsists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
                        if exsists:
                            try:
                                cursor.execute("UPDATE users SET display=? WHERE Discordusername=?", (new_name, username))
                                conn.commit()
                                reply(f"Display name updated to {new_name}!")
                                username = new_name
                            except Exception as e:
                                reply(f"Error updating display name: {e}")
                        else:
                            reply("You must register first!")
                # This
                elif content.lower().strip() == "/at online":
                    reply("/au online")
                elif content.lower().strip().startswith("/at badge"):
                    # /at badge add <username> <badge>
                    # /at badge remove <username> <badge>
                    # /at badge list [username]
                    cmd = content.split(None, 2)
                    sub = cmd[1].lower() if len(cmd) > 1 else ''
                    rest = cmd[2].strip() if len(cmd) > 2 else ''

                    def get_user_row(name_to_find):
                        if platform:
                            return cursor.execute("SELECT * FROM users WHERE AUusername=?", (name_to_find,)).fetchone()
                        else:
                            return cursor.execute("SELECT * FROM users WHERE Discordusername=?", (name_to_find,)).fetchone()

                    if sub == 'list':
                        target = rest or username
                        user = get_user_row(target)
                        if not user:
                            reply("No profile found.")
                        else:
                            badges = user[7] or ''
                            badges_list = [b for b in [x.strip() for x in badges.split(',')] if b]
                            reply(f"Badges for {target}: {', '.join(badges_list) if badges_list else 'None'}")
                    elif sub in ('add', 'remove'):
                        # must have assign permission
                        caller_row = get_user_row(username)
                        caller_has_perm = False
                        if caller_row:
                            caller_has_perm = bool(caller_row[8]) if len(caller_row) > 8 else False
                        if not caller_has_perm:
                            reply("You do not have permission to assign or remove badges.")
                        else:
                            parts = rest.split(None, 1)
                            if len(parts) < 2:
                                reply("Usage: /at badge add|remove <username> <badge>")
                            else:
                                target, badge = parts[0].strip(), parts[1].strip()
                                user = get_user_row(target)
                                if not user:
                                    reply("Target user not found.")
                                else:
                                    badges = user[7] or ''
                                    badges_set = set(b for b in [x.strip() for x in badges.split(',')] if b)
                                    if sub == 'add':
                                        if badge in badges_set:
                                            reply(f"{target} already has the badge '{badge}'.")
                                        else:
                                            badges_set.add(badge)
                                            new_badges = ','.join(sorted(badges_set))
                                            if platform:
                                                cursor.execute("UPDATE users SET badges=? WHERE AUusername=?", (new_badges, target))
                                            else:
                                                cursor.execute("UPDATE users SET badges=? WHERE Discordusername=?", (new_badges, target))
                                            conn.commit()
                                            reply(f"Badge '{badge}' added to {target}.")
                                    else:
                                        if badge not in badges_set:
                                            reply(f"{target} does not have the badge '{badge}'.")
                                        else:
                                            badges_set.discard(badge)
                                            new_badges = ','.join(sorted(badges_set))
                                            if platform:
                                                cursor.execute("UPDATE users SET badges=? WHERE AUusername=?", (new_badges, target))
                                            else:
                                                cursor.execute("UPDATE users SET badges=? WHERE Discordusername=?", (new_badges, target))
                                            conn.commit()
                                            reply(f"Badge '{badge}' removed from {target}.")
                    else:
                        reply("Badge commands: /at badge list [username], /at badge add <username> <badge>, /at badge remove <username> <badge>")
                elif content.lower().strip().find("imutt") != -1:
                    reply(f"It's Lmutt, not imutt {username}")
                elif content.lower().strip().find("lmutt") != -1:
                    reply("<@1286383453016686705>")
                # to here, can be removed if you want... idrgaf
                elif content.lower().strip() == "//au help":
                    reply("Aurith commands now start with /at instead of //au to avoid confusion with the main bot's commands. Use /at help for a list of commands!")

                if platform:
                    try:
                        exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE AUusername=?", (username,))
                            conn.commit()
                    except Exception as e:
                        print(f"Error updating message count: {e}")
                else:
                    try:
                        exsists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE Discordusername=?", (username,))
                            conn.commit()
                    except Exception as e:
                        print(f"Error updating message count: {e}")
            except:
                pass

        s.close()
    except KeyboardInterrupt:
        run_event.clear()
        print("\nShutting down...")
        reply("Aurith is shutting down, likely to restart")
    finally:
        try:
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
