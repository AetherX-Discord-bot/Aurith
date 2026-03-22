import socket
import time
import threading
import sys
import logging
import threading
import sys
import requests
import sqlite3 #im finna chatgpt sqlite3
import re
import asyncio
import websockets
import json
import flask
import hashlib
import secrets
import random
from dotenv import load_dotenv
import os

load_dotenv()

name = "main" #fuck it, we ball

conn = None
cursor = None

IP = "104.236.25.60"
API_URL = f"http://{IP}:3072/api"
TCP_PORT = 4040
BOT_API_PORT = 7871
print("I'm gonna learn spanish now!")

CONFIG = {
    "username": os.getenv("username"),
    "password": os.getenv("password"),
    "rawchat": True,
    "rawchat_key": os.getenv("rawchat_key"),
    "platform": "BOT",
    "webonly": False
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
    if CONFIG.get("rawchat"):
        payload = {
            "cmd": "RAWCHAT",
            "rawkey": CONFIG["rawchat_key"],
            "content": f'{CONFIG["username"]}: {text}',
            "platform": CONFIG["platform"]
        }
    else:
        payload = {
            "cmd": "CHAT",
            "content": text, # dont use the rawchat version because it looks weird in chat
            "username": CONFIG["username"],
            "password": CONFIG["password"],
            "platform": CONFIG["platform"]
        }
    send_request(payload)


def _get_user_row_by_name(name_to_find, discord_first=False):
    """Return a user row searching AUusername first, then Discordusername."""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if discord_first:
            row = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (name_to_find,)).fetchone()
            if row:
                conn.close()
                return row, False
        row = cursor.execute("SELECT * FROM users WHERE AUusername=?", (name_to_find,)).fetchone()
        if row:
            conn.close()
            return row, True
        row = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (name_to_find,)).fetchone()
        conn.close()
        return (row, False) if row else (None, None)
    except Exception:
        return (None, None)


def _profile_dict_from_row(row, authorized=False):
    if not row:
        return None

    # DB columns: id, AUusername, Discordusername, bio, friend_code_3ds,
    # messages_sent, display, badges, can_assign_badges, owner, email

    d = {
        "id": row[0],
        "au_username": row[1],
        "discord_username": row[2],
        "bio": row[3],
        "friend_code_3ds": row[4],
        "messages_sent": row[5],
        "display": row[6],
        "badges": (row[7] or '').split(',') if row[7] else [],
        "can_assign_badges": bool(row[8]),
        "owner": bool(row[10]),
    }

    if authorized == True:
        d["email"] = row[10]
        d["pointless_hexadecimal"] = row[11]

    # gravatar
    email = str(((row[8] or row[1]) or '')).strip().lower()
    h = hashlib.md5(email.encode('utf-8')).hexdigest()
    d["gravatar"] = f"https://www.gravatar.com/avatar/{h}?d=identicon&s=128"

    return d


def do_pokehunt(username, is_auto=False):
    conn_local = sqlite3.connect('database.db')
    cursor_local = conn_local.cursor()
    try:
        cursor_local.execute("SELECT * FROM pokemen")
        pokestaff = cursor_local.fetchall()

        if not pokestaff:
            if not is_auto:
                reply("Lmutt090 is lazy")
            return

        cursor_local.execute("SELECT * FROM pokemen_inventory WHERE user=?", (username,))
        inventory = cursor_local.fetchone()

        if not inventory:
            try:
                cursor_local.execute("INSERT INTO pokemen_inventory (user, staff, last_hunt) VALUES (?, ?, ?)", (username, '[]', 0))
                conn_local.commit()
            except sqlite3.IntegrityError:
                pass  # already exists
            inventory = cursor_local.execute("SELECT * FROM pokemen_inventory WHERE user=?", (username,)).fetchone()

        last_hunt = inventory[2] if inventory and len(inventory) > 2 else 0
        now = int(time.time())

        if not is_auto and now - last_hunt < 90:
            remaining = 90 - (now - last_hunt)
            minutes = remaining // 60
            seconds = remaining % 60
            reply(f"You are too tired to hunt for a staff member. Please wait {minutes}m {seconds}s before trying again.")
            return

        # Select random pokestaff with weighted rarity (lower numbers = rarer)
        weights = [r for _, r, _ in pokestaff]
        staffmemberhuntedhopefullyorstandoorvirt, rarity, description = random.choices(pokestaff, weights=weights, k=1)[0]

        # Load current staff inventory
        try:
            current_staff = json.loads(inventory[1]) if inventory and inventory[1] else []
        except json.JSONDecodeError:
            current_staff = []

        # Add new caught pokemon to inventory
        current_staff.append({
            "name": staffmemberhuntedhopefullyorstandoorvirt,
            "rarity": rarity,
            "description": description,
            "caught_at": now
        })

        # Update inventory with new pokemon and timestamp
        try:
            cursor_local.execute("UPDATE pokemen_inventory SET staff=?, last_hunt=? WHERE user=?", 
                         (json.dumps(current_staff), now, username))
            conn_local.commit()
            if is_auto:
                reply(f"Aurith went hunting and caught a {staffmemberhuntedhopefullyorstandoorvirt}! (Rarity: {rarity}) :3\n{description}")
            else:
                reply(f"You caught a {staffmemberhuntedhopefullyorstandoorvirt}! (Rarity: {rarity}) :3\n{description}")
        except Exception as e:
            if not is_auto:
                reply(f"Error saving your catch: {e}")
            print(f"Error updating pokemen inventory: {e}")
    finally:
        conn_local.close()


def show_pokedex(pokestaff_name):
    """Show one pokestaff entry from pokemen table."""
    conn_local = sqlite3.connect('database.db')
    cursor_local = conn_local.cursor()
    try:
        cursor_local.execute("SELECT staff, rarity, description FROM pokemen WHERE staff=?", (pokestaff_name,))
        row = cursor_local.fetchone()
        if not row:
            reply(f"No pokedex entry found for '{pokestaff_name}'.")
            return

        staff, rarity, description = row
        reply(f"Pokedex - {staff}: Rarity {rarity}. {description}")
    except Exception as e:
        reply(f"Error reading pokedex entry: {e}")
        print(f"show_pokedex error: {e}")
    finally:
        conn_local.close()


def show_pokebox(username):
    """List caught pokestaff for user from pokemen_inventory."""
    conn_local = sqlite3.connect('database.db')
    cursor_local = conn_local.cursor()
    try:
        cursor_local.execute("SELECT staff, last_hunt FROM pokemen_inventory WHERE user=?", (username,))
        row = cursor_local.fetchone()
        if not row:
            reply(f"{username} has no pokebox yet. Use /at pokehunt to catch one!")
            return

        staff_json, last_hunt = row
        try:
            staff_list = json.loads(staff_json or '[]')
        except json.JSONDecodeError:
            staff_list = []

        if not staff_list:
            reply(f"{username} has no pokestaff yet. Use /at pokehunt to catch one!")
            return

        lines = [f"Pokebox for {username} ({len(staff_list)} caught):"]
        for entry in staff_list:
            name = entry.get('name', '<unknown>')
            rarity = entry.get('rarity', '?')
            desc = entry.get('description', '')
            lines.append(f"- {name} (Rarity {rarity}) {desc}")

        # Keep one message only, but fallback if > 5 entries
        if len(lines) > 15:
            reply(f"{username} has {len(staff_list)} pokestaff. Use /at pokedex <name> for details.")
        else:
            reply("\n".join(lines))
    except Exception as e:
        reply(f"Error reading pokebox: {e}")
        print(f"show_pokebox error: {e}")
    finally:
        conn_local.close()


def list_pokestaff():
    """List all pokestaff entries available."""
    conn_local = sqlite3.connect('database.db')
    cursor_local = conn_local.cursor()
    try:
        cursor_local.execute("SELECT staff, rarity FROM pokemen ORDER BY rarity ASC, staff ASC")
        rows = cursor_local.fetchall()
        if not rows:
            reply("No pokestaff has been configured yet.")
            return

        lines = ["Available pokestaff:"]
        for staff, rarity in rows:
            lines.append(f"- {staff} (Rarity {rarity})")

        if len(lines) > 25:
            reply(f"There are {len(rows)} pokestaff entries. Use /at pokedex <name> for details.")
        else:
            reply("\n".join(lines))
    except Exception as e:
        reply(f"Error listing pokestaff: {e}")
        print(f"list_pokestaff error: {e}")
    finally:
        conn_local.close()


def auto_hunt_loop():
    while run_event.is_set():
        time.sleep(90)  # 90 seconds
        do_pokehunt(CONFIG["username"], is_auto=True)
def start_web():
    app = flask.Flask(__name__)

    @app.route('/health')
    def health():
        return "OK", 200

    @app.route('/api')
    @app.route('/api/')
    @app.route('/api/user')
    @app.route('/api/user/')
    @app.route('/api/pokestaff')
    @app.route('/api/pokestaff/')
    def theydida400():
        return flask.jsonify({"error": "missing parameters"}), 400

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if flask.request.method == 'POST':
            username = flask.request.form.get('username', '').strip()
            platform = flask.request.form.get('platform', '').strip()
            resp = flask.make_response(flask.redirect('/profile'))
            if username:
                resp.set_cookie('au_user', username, max_age=60*60*24*30)
            if platform:
                resp.set_cookie('au_platform', platform, max_age=60*60*24*30)
            return resp

        return flask.render_template_string('''
        <html><body>
        <h2>Who are you?</h2>
        <form method="post">
          <label>Username: <input name="username"></label><br>
          <label>Platform: <select name="platform"><option value="AU">AU</option><option value="Discord">Discord</option></select></label><br>
          <button type="submit">Save</button>
        </form>
        <p>Or view someone: <a href="/user/example">/user/example</a></p>
        <p>View PokeStaff: <a href="/pokestaff">/pokestaff</a></p>
        </body></html>
        ''')

    @app.route('/info')
    def info():
        return flask.render_template_string('''
        <html><body>
        <h2>Aurith Info</h2>
        <p>Aurith is a bot made by Lmutt090 and ClaudiWolf to have profiles for everyone on AuroraChat.</p>
        <p>There is litteraly only ONE command that is hidden... so, uh... yeah... great bot!</p>
        <p>If you wanna see the source code, it's at <a href="https://github.com/AetherX-Discord-Bot/Aurith">https://github.com/AetherX-Discord-Bot/Aurith</a> and is the base for the bot library... you may want to CHANGE ALOT... please?</p>
        <p>Use /at help for the commands... blah blah blah, you get the gist</p>
        <p>Oh, there's a page to see profiles. But it's a work in progress... it's at the <a href="..">Main Page</a></p>
        <p style="font-size:smaller;color:gray"><a href="../license">View the License here</a></p>
        </body></html>
        ''')
    @app.route('/commands')
    def commands():
        return flask.render_template_string('''
        <html><body>
        <h2>Aurith Commands</h2>
        <p>/at register</p>
        <p>/at credits, /profile [username] (/at dash), /at info, /at source, /at bugbounty</p>
        <p>registered users only: /at setbio [bio], /at setfc [friend code], /at setdisplayname [display name]</p>
        <p>done with Aurith? use /at delete</p>
        </body></html>
        ''')

    @app.route('/license')
    def license():
        return flask.render_template_string('''
            MIT License
            <br>
            Copyright (c) 2026 Lmutt090
            <br>
            Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions: credit must be 
            attributed to all contributors that have worked on Aurith and the software
            must not be used to scrape messages from AuroraChat servers to identify
            users without their explicit consent and must include a data deletion option.
            <br>
            The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.
            <br>
            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.
        ''')

    @app.route('/profile')
    def profile():
        username = flask.request.cookies.get('au_user')
        if not username:
            return flask.redirect('/')
        row, is_au = _get_user_row_by_name(username)
        d = _profile_dict_from_row(row)
        if not d:
            return flask.render_template_string('<html><body><p>No profile found for {{u}}</p><p><a href="/">Back</a></p></body></html>', u=username), 404
        return flask.render_template_string('''
        <html><body>
        <h2>Profile for {{p.display or (p.au_username or p.discord_username)}}</h2>
        <img src="{{p.gravatar}}" alt="avatar"><br>
        <b>AU username:</b> {{p.au_username}}<br>
        <b>Discord username:</b> {{p.discord_username}}<br>
        <b>Bio:</b> {{p.bio}}<br>
        <b>Friend code:</b> {{p.friend_code_3ds}}<br>
        <b>Badges:</b> {{p.badges}}<br>
        <p><a href="/">Change user</a></p>
        </body></html>
        ''', p=d)

    @app.route('/user/<string:username>')
    def public_user(username):
        row, _ = _get_user_row_by_name(username)
        d = _profile_dict_from_row(row)
        if not d:
            return flask.render_template_string('<html><body><p>No profile found for {{u}}</p><p><a href="/">Back</a></p></body></html>', u=username), 404
        return flask.render_template_string('''
        <html><body>
        <h1></h1>
        <h2>Public profile: {{p.display or (p.au_username or p.discord_username)}}</h2>
        <img src="{{p.gravatar}}" alt="avatar"><br>
        <b>AU username:</b> {{p.au_username}}<br>
        <b>Discord username:</b> {{p.discord_username}}<br>
        <b>Bio:</b> {{p.bio}}<br>
        <b>Badges:</b> {{p.badges}}<br>
        </body></html>
        ''', p=d)

    @app.route('/pokestaff')
    def pokestaff_index():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT staff, rarity, description FROM pokemen ORDER BY rarity ASC, staff ASC')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return flask.render_template_string('''
            <html><body>
            <h2>PokeStaff</h2>
            <p>No pokestaff has been configured yet.</p>
            <p><a href="/">Back</a></p>
            </body></html>
            ''')

        return flask.render_template_string('''
        <html><body>
        <h2>PokeStaff</h2>
        <p>List of current pokestaff creatures.</p>
        <ul>
        {% for staff, rarity, description in rows %}
          <li><a href="/pokestaff/{{staff}}">{{staff}}</a> (rarity {{rarity}}) - {{description}}</li>
        {% endfor %}
        </ul>
        <p><a href="/">Back</a></p>
        </body></html>
        ''', rows=rows)

    @app.route('/pokestaff/<string:staff>')
    def pokestaff_detail(staff):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT staff, rarity, description FROM pokemen WHERE staff=?', (staff,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return flask.render_template_string('<html><body><p>No pokestaff entry found for {{s}}</p><p><a href="/pokestaff">Back</a></p></body></html>', s=staff), 404

        staff_name, rarity, description = row
        return flask.render_template_string('''
        <html><body>
        <h2>PokeStaff: {{s}}</h2>
        <p><b>Rarity:</b> {{r}}</p>
        <p><b>Description:</b> {{d}}</p>
        <p><a href="/pokestaff">Back to list</a></p>
        </body></html>
        ''', s=staff_name, r=rarity, d=description)

    @app.route('/api/user/<string:username>', methods=['GET', 'POST'])
    def api_user(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # FINALLY ADDED IT! Someone decided to scrape my bot's database apparently... so now we have an API with rate limits and token authentication to prevent abuse...
        token = flask.request.args.get("token")
        if not token:
            token = flask.request.headers.get("Authorization")

        if not token:
            return flask.jsonify({"error": "missing token"}), 401

        cursor.execute("SELECT * FROM tokens WHERE TOKEN=?", (token,))
        token_row = cursor.fetchone()

        if not token_row:
            return flask.jsonify({"error": "invalid token"}), 403

        # rate limit: max 1 request per minute unless bypass_rate_limit is enabled, may relax later but this is to prevent abuse from external developers... cant trust anyone >:(
        now = time.time()
        last_used = token_row[5] if len(token_row) > 5 and token_row[5] is not None else 0
        bypass_rate_limit = bool(token_row[2])

        if now - last_used < 60 and not bypass_rate_limit:
            return flask.jsonify({"error": "rate limit exceeded"}), 429

        cursor.execute("UPDATE tokens SET last_used=? WHERE TOKEN=?", (int(now), token))
        conn.commit()

        print(f"API request for user {username} with token {token_row[0]} (developer: {token_row[1]})") # This is temporary logging because external developers may abuse this

        row, _ = _get_user_row_by_name(username)
        d = _profile_dict_from_row(row, bool(token_row[4]))

        if not d:
            return flask.jsonify({"error": "not found"}), 404

        if flask.request.method == 'POST':
            # require write access for updates
            if not bool(token_row[3]):
                return flask.jsonify({"error": "write permission required"}), 403

            data = flask.request.get_json(silent=True)
            if not isinstance(data, dict):
                return flask.jsonify({"error": "invalid json payload"}), 400

            allowed = {
                'AUusername': 'AUusername',
                'Discordusername': 'Discordusername',
                'bio': 'bio',
                'friend_code_3ds': 'friend_code_3ds',
                'display': 'display',
                'badges': 'badges',
                'email': 'email'
            }

            update_fields = {}
            for key, value in data.items():
                if key not in allowed:
                    continue
                if key == 'friend_code_3ds' and value is not None:
                    fc_digits = ''.join(ch for ch in str(value) if ch.isdigit())
                    if len(fc_digits) != 12:
                        return flask.jsonify({"error": "friend_code_3ds must contain exactly 12 digits"}), 400
                    update_fields[allowed[key]] = fc_digits
                elif key in ('can_assign_badges', 'owner') and value is not None:
                    try:
                        update_fields[allowed[key]] = 1 if int(value) else 0
                    except Exception:
                        return flask.jsonify({"error": f"{key} must be 0 or 1"}), 400
                elif value is not None:
                    update_fields[allowed[key]] = str(value)

            if not update_fields:
                return flask.jsonify({"error": "no updatable fields provided"}), 400

            set_clause = ', '.join(f"{col}=?" for col in update_fields.keys())
            values = list(update_fields.values())
            cursor.execute(f"UPDATE users SET {set_clause} WHERE AUusername=? OR Discordusername=?", values + [username, username])
            conn.commit()

            row, _ = _get_user_row_by_name(username)
            updated = _profile_dict_from_row(row, bool(token_row[4]))
            print(f"Updated user {username} via API token {token_row[0]} (developer: {token_row[1]}), fields updated: {list(update_fields.keys())}") # Temporary logging for external developer updates
            return flask.jsonify({"success": True, "user": updated})

        return flask.jsonify(d)

    @app.route('/api/pokestaff/<string:staff>', methods=['GET'])
    def api_pokestaff(staff=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        token = flask.request.args.get('token')
        if not token:
            token = flask.request.headers.get('Authorization')

        if not token:
            conn.close()
            return flask.jsonify({'error': 'missing token'}), 401

        cursor.execute('SELECT * FROM tokens WHERE TOKEN=?', (token,))
        token_row = cursor.fetchone()

        if not token_row:
            conn.close()
            return flask.jsonify({'error': 'invalid token'}), 403

        now = time.time()
        last_used = token_row[5] if len(token_row) > 5 and token_row[5] is not None else 0
        bypass_rate_limit = bool(token_row[2])

        if now - last_used < 60 and not bypass_rate_limit:
            conn.close()
            return flask.jsonify({'error': 'rate limit exceeded'}), 429

        cursor.execute('UPDATE tokens SET last_used=? WHERE TOKEN=?', (int(now), token))
        conn.commit()

        if staff:
            cursor.execute('SELECT staff, rarity, description FROM pokemen WHERE staff=?', (staff,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return flask.jsonify({'error': 'not found'}), 404
            staff_name, rarity, description = row
            return flask.jsonify({'staff': staff_name, 'rarity': rarity, 'description': description})

        cursor.execute('SELECT staff, rarity, description FROM pokemen ORDER BY rarity ASC, staff ASC')
        rows = cursor.fetchall()
        conn.close()

        results = [{'staff': r[0], 'rarity': r[1], 'description': r[2]} for r in rows]
        return flask.jsonify({'pokestaff': results})

    # run in a thread so the main bot loop can continue
    def run_app():
        # Suppress the Flask/werkzeug production warning/banner in a non-dev deployment
        try:
            import flask.cli
            flask.cli.show_server_banner = lambda *args, **kwargs: None
        except Exception:
            pass
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        app.run(host='0.0.0.0', port=BOT_API_PORT, debug=False, use_reloader=False)

    t = threading.Thread(target=run_app, daemon=True)
    t.start()


def console_input_loop(event: threading.Event):
    """Read lines from the console and send them to chat while `event` is set."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    while event.is_set():
        try:
            line = input()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split(" ", 1)
        content = parts[-1] if len(parts) >= 2 else line
        # allow a local quit command
        if line.lower().strip() in ("/quit", ":q", "exit"):
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
        elif line.lower().strip().startswith("/dbmod "):
            musername = content.strip()
            exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (musername,)).fetchone()
            if exsists:
                superexists = 0
                print("So, you want to manually modify the bot in the console? cool!")
                print("I think you know what to do")
                print("discord, email, owner, badges, canbadge...")
                dbtype = input()
                print("Now the value, remember. True = 1")
                dbvalue = input()
                print("I'm checking the varibles, hold on")
                if dbtype:
                    print("dbtype exists")
                    superexists += 1
                else:
                    print("dbtype doesn't exist")
                if dbvalue:
                    print("the dbvalue exists")
                    superexists += 1
                else:
                    print("the dbvalue doesn't exist")
                if superexists == 2:
                    print("It works, i'ma go into the database now")
                    try:
                        cursor.execute(f"UPDATE users SET {dbtype}=? WHERE AUusername=?", (dbvalue, musername))
                        conn.commit()
                    except Exception as e:
                        print(f"well, you fucked up: {e}")
                else:
                    print("it dont work, i'ma ignore you >:3")
            else:
                print("User doesn't not exist dumbass")
        elif line.lower().strip() == "/gtoken":
            print("Generating token for external developer access...")
            dev_name = input("Developer name: ").strip()
            if not dev_name:
                print("Developer name cannot be empty.")
                return

            # Check if developer exists in users table first
            user_exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (dev_name,)).fetchone()
            if not user_exists:
                print(f"Error: User '{dev_name}' does not exist. They must register first!")
                return

            rng_value = secrets.token_hex(16)
            token_value = hashlib.sha256(f"{dev_name}:{time.time()}".encode('utf-8')).hexdigest() + "." + rng_value
            try:
                cursor.execute("INSERT INTO tokens (TOKEN, developer) VALUES (?, ?)", (token_value, dev_name))
                conn.commit()
                print(f"Generated token for {dev_name}: {token_value}")
                print("Please DM the token to the developer. Then delete it once saved.")
            except Exception as e:
                print(f"Error generating token: {e}")
        elif line.lower().strip() == "/cpokestaff":
            pokestaff = input("Enter the name of the staff member here ya idiot: ")
            cursor.execute("SELECT * FROM pokemen WHERE staff=?", (pokestaff,))
            exists = cursor.fetchone()
            if exists:
                updatevalue = input("Select a value to update: ")
                if updatevalue.lower().strip() == "rarity":
                    newrarity = input("Enter the new rarity (number only): ")
                    try:
                        rarity_int = int(newrarity)
                        cursor.execute("UPDATE pokemen SET rarity=? WHERE staff=?", (rarity_int, pokestaff))
                        conn.commit()
                        print("Rarity updated successfully!")
                    except ValueError:
                        print("Invalid rarity value. Must be an integer.")
                elif updatevalue.lower().strip() == "description":
                    newdescription = input("Enter the new description: ")
                    cursor.execute("UPDATE pokemen SET description=? WHERE staff=?", (newdescription, pokestaff))
                    conn.commit()
                    print("Description updated successfully!")
            else:
                rarity = input("Enter the rarity (number only) of this staff member's pokeman: ")
                description = input("Enter a description for this staff member's pokeman: ")
                iforgor = "dr strange"
                try:
                    cursor.execute("INSERT INTO pokemen (staff, rarity, description) VALUES (?, ?, ?)", (pokestaff, int(rarity), description))
                    conn.commit()
                    reply(f"A new pokestaff has appeared in the wild... it's {pokestaff}")
                except Exception as e:
                    print(f"Error adding pokestaff: {e}")

        else:
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
                        AUusername TEXT UNIQUE,
                        Discordusername TEXT UNIQUE,
                        bio TEXT,
                        friend_code_3ds integer,
                        messages_sent integer DEFAULT 0,
                        display TEXT,
                        badges TEXT DEFAULT '',
                        email TEXT,
                        can_assign_badges INTEGER DEFAULT 0,
                        owner INTEGER DEFAULT 0,
                        pointless_hexadecimal TEXT UNIQUE
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
    if CONFIG["webonly"]:
        print("Starting web server only...")
        start_web()
        reply("Aurith is online in web-only mode!")
        print("Web server is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down web server...")
            reply("Aurith is shutting down (web-only mode)")
            print("Web server has shut down.")
        return
    start_web()
    reply("Aurith is online!")
    stinky = cursor.execute("SELECT setting_value FROM internalsettings WHERE setting_name='stinky_mode'").fetchone()
    stinky = bool(int(stinky[0])) if stinky else False
    # start console input thread
    run_event.set()
    console_thread = threading.Thread(target=console_input_loop, args=(run_event,), daemon=True)
    console_thread.start()
    # start auto hunt thread
    auto_hunt_thread = threading.Thread(target=auto_hunt_loop, daemon=True)
    auto_hunt_thread.start()

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

                # Check if message is in new pipe-separated format
                if raw_msg.startswith("CHAT|") or raw_msg.startswith("DM|"):
                    parts = raw_msg.split("|")
                    if raw_msg.startswith("DM|") and len(parts) >= 5:
                        # DM|RECEIVER|TAG|USERNAME|MESSAGE
                        message_type = "DM"
                        receiver = parts[1]
                        tag = parts[2]
                        username = parts[3]
                        content = "|".join(parts[4:])  # Join remaining parts in case message contains |
                        platform = tag  # TAG might represent platform
                    elif raw_msg.startswith("CHAT|") and len(parts) >= 4:
                        # CHAT|TAG|USERNAME|MESSAGE
                        message_type = "CHAT"
                        tag = parts[1]
                        username = parts[2]
                        content = "|".join(parts[3:])  # Join remaining parts in case message contains |
                        platform = tag  # TAG might represent platform
                        receiver = None
                    else:
                        # Malformed new format, skip
                        continue
                else:
                    # Legacy format parsing
                    message_type = "CHAT"
                    receiver = None
                    parts = raw_msg.split(": ")
                    content = parts[-1] if len(parts) >= 2 else raw_msg
                    content = content.strip("'")  # Bandaid fix for server bug wrapping messages in quotes

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
                                if norm == 'discord':
                                    platform = 'Discord'
                                elif norm == 'wiiu' or platform_type == 'wii u':
                                    platform = 'Wii U'
                                elif norm == 'fluxer':
                                    platform = 'Fluxer'
                                else:
                                    platform = platform_type.lower()
                        except Exception as e:
                            print(f"Error extracting platform: {e}")
                            platform = None

                if username == CONFIG["username"]:
                    if platform not in ('Discord', 'Fluxer'):
                        try:
                            exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                            if exsists:
                                cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE AUusername=?", (username,))
                                conn.commit()
                        except Exception as e:
                            print(f"yo bot dumb and cant update message count for itself")
                            print(f"Error updating message count: {e}")
                    continue

                # For DMs, only process if this bot is the receiver
                if message_type == "DM" and receiver != CONFIG["username"]:
                    continue

                if content.lower().strip() == "/at hello":
                    reply("Hello, Im Dr. Sex")
                elif content.lower().strip() == "/at info" or content.lower().strip() == "/at about":
                    reply("Aurith is a bot made by Lmutt090 and ClaudiWolf to have profiles for everyone on AuroraChat.\nThere is litteraly only ONE command that is hidden... so, uh... yeah... great bot!\nThere is a webpage if you wanna see more, https://aurith.aether-x.org/info\n(also, if i ever make a pay to use feature in the bot, please fork this and make your own... please...)")
                elif content.lower().strip() == "/at help" or content.lower().strip() == "/at commands" or content.lower().strip() == "/at":
                    if stinky:
                        reply(f"Command viewing is currently web-only. Please visit https://aurith.aether-x.org/commands.")
                        continue

                    reply("Available commands: /at register\n/at credits, /profile [username] (/at dash), /at info, /at source, /at pokehunt\nregistered users only: /at setbio [bio], /at setfc [friend code], /at setdisplayname [display name], /at newhex\nuse /au help for the regular bot's commands")
                elif content.lower().strip() == "/at credits":
                    reply("Made by: Lmutt090 (<https://lmutt090.me>) and ClaudiWolf (<https://www.claudiwolf2056.com/>)") # Please do not remove the credits from these people, atleast to the people who fork this...
                elif content.lower().strip().startswith("/profile "):
                    musername = content[9:].strip()
                    if not musername:
                        musername = username

                    if stinky:
                        reply(f"Profile viewing is currently web-only. Please visit https://aurith.aether-x.org/user/{musername}.")
                        continue

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
                        if musername == "aurorachat": 
                            profile += "\nStatus: Godly being that can delete you in seconds"
                        elif user[5]:
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
                    if platform not in ('Discord', 'Fluxer'):
                        try:
                            pointless_hex = hashlib.sha256(f"{username}:{time.time()}".encode('utf-8')).hexdigest()
                            cursor.execute("INSERT INTO users (AUusername, pointless_hexadecimal) VALUES (?, ?)", (username, pointless_hex))
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
                        if platform not in ('Discord', 'Fluxer'):
                            cursor.execute("DELETE FROM users WHERE AUusername=?", (username,))
                        elif platform == 'Discord':
                            cursor.execute("DELETE FROM users WHERE Discordusername=?", (username,))
                        elif platform == 'Fluxer':
                            cursor.execute("DELETE FROM users WHERE AUusername=? OR Discordusername=?", (username, username))
                        else:
                            reply("Unknown platform, cannot delete.")
                            return
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
                # from here
                elif content.lower().strip().find("imutt") != -1:
                    reply(f"It's Lmutt, not imutt {username}")
                elif content.lower().strip().find("lmutt") != -1:
                    reply("<@1286383453016686705>")
                elif content.lower().strip().find("rainy") != -1:
                    reply("<@1286383453016686705>")
                # to here, can be removed if you want... idrgaf
                elif content.lower().strip() == "//au help":
                    reply("Aurith commands now start with /at instead of //au to avoid confusion with the main bot's commands. Use /at help for a list of commands!")
                elif content.lower().strip() == "/at donate":
                    reply("Oh my god! you found a donate command!\nIf you want to support Aurith, you can do so here: https://ko-fi.com/lmutt090\nThanks for atleast reading this, i never even put it in  the help command ^w^")
                elif content.lower().strip() == "/at dash":
                        reply("The open beta dashboard is at https://aurith.aether-x.org you cant actually change your profile yet... also ask Lmutt090 to add an Email to your profile to get a profile picture :)")
                elif content.lower().strip() == "/at stinky":
                    if platform == 'Discord':
                        row, is_au = _get_user_row_by_name(username, True)
                        d = _profile_dict_from_row(row)
                    else:
                        row, is_au = _get_user_row_by_name(username, False)
                        d = _profile_dict_from_row(row)
                    is_owner = d and d.get("owner", False)
                    if is_owner:
                        stinky = not stinky
                        status = "enabled" if stinky else "disabled"
                        cursor.execute("INSERT OR REPLACE INTO internalsettings (setting_name, setting_value) VALUES (?, ?)", ("stinky_mode", "1" if stinky else "0"))
                        conn.commit()
                        reply(f"Web-only profile/command viewing has been {status}.")
                        print(f"Stinky mode {'enabled' if stinky else 'disabled'} by {username} on {platform if platform else 'unknown platform'}")
                    else:
                        reply("You do not have permission to use this command.")
                        print(f"{username} on {platform if platform else 'unknown platform'} attempted to toggle stinky mode without permission.")
                elif content.lower().strip() == "/at bugbounty":
                    reply("If you find a bug in Aurith, please report it to Lmutt090 on Discord. I don't have any money to give you for bug bounties though... But I will appreciate the help!")
                elif content.lower().strip() == "/at source":
                    reply("Aurith is open source! You can find the code on GitHub: https://github.com/AetherX-Discord-Bot/Aurith")
                elif content.lower().strip() == "/at newhex":
                    if platform not in ('Discord', 'Fluxer'):
                        cursor.execute("SELECT pointless_hexadecimal FROM users WHERE AUusername=?", (username,))
                        exists = cursor.fetchone()
                        if exists:
                            pointless_hex = hashlib.sha256(f"{username}:{time.time()}".encode('utf-8')).hexdigest()
                            try:
                                cursor.execute("UPDATE users SET pointless_hexadecimal=? WHERE AUusername=?", (pointless_hex, username))
                            except Exception as e:
                                print(f"Error updating pointless hexadecimal: {e}")
                    elif platform == 'Discord':
                        cursor.execute("SELECT pointless_hexadecimal FROM users WHERE Discordusername=?", (username,))
                        exists = cursor.fetchone()
                        if exists:
                            pointless_hex = hashlib.sha256(f"{username}:{time.time()}".encode('utf-8')).hexdigest()
                            try:
                                cursor.execute("UPDATE users SET pointless_hexadecimal=? WHERE Discordusername=?", (pointless_hex, username))
                            except Exception as e:
                                print(f"Error updating pointless hexadecimal: {e}")
                    elif platform == 'Fluxer':
                        cursor.execute("SELECT pointless_hexadecimal FROM users WHERE Fluxerusername=?", (username,))
                        exists = cursor.fetchone()
                        if exists:
                            pointless_hex = hashlib.sha256(f"{username}:{time.time()}".encode('utf-8')).hexdigest()
                            try:
                                cursor.execute("UPDATE users SET pointless_hexadecimal=? WHERE Fluxerusername=?", (pointless_hex, username))
                            except Exception as e:
                                print(f"Error updating pointless hexadecimal: {e}")
                    else:
                        return
                    reply("You got a new pointess hexadecimal... Why do you want this? lmfao")
                elif content.lower().strip() == "/at pokehunt":
                    do_pokehunt(username)
                elif content.lower().strip().startswith("/at pokedex "):
                    pokestaff_name = content[12:].strip()
                    show_pokedex(pokestaff_name)
                elif content.lower().strip() == "/at pokebox":
                    show_pokebox(username)
                elif content.lower().strip() == "/at pokestaff":
                    list_pokestaff()

                if platform not in ('Discord', 'Fluxer'):
                    try:
                        exsists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE AUusername=?", (username,))
                            conn.commit()
                    except Exception as e:
                        print(f"Error updating message count: {e}")
                elif platform == 'Discord':
                    try:
                        exsists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE Discordusername=?", (username,))
                            conn.commit()
                    except Exception as e:
                        print(f"Error updating message count: {e}")
                elif platform == 'Fluxer':
                    try:
                        exsists = cursor.execute("SELECT * FROM users WHERE Fluxerusername=?", (username,)).fetchone()
                        if exsists:
                            cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE Fluxerusername=?", (username,))
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
