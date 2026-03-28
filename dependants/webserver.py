import os
import time
import threading
import logging
import sqlite3
from dotenv import load_dotenv
import flask

conn = None
cursor = None
BOT_API_PORT = 7871

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

    @app.route('/pictures/<path:filename>')
    def serve_pictures(filename):
        return flask.send_from_directory(PICTURE_DIR, filename)

    # list files in the directory
    @app.route('/pictures/')
    def list_pictures():
        files = os.listdir(PICTURE_DIR)
        return "<br>".join(f'<a href="/pictures/{f}">{f}</a>' for f in files)

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

    @app.route('/rules')
    def rules():
        return flask.render_template_string('''
        <html><body>
        <h2>Rules</h2>
        <p>So, we have our own set of rules for use of our bot, a Terms of Service as you will, while there is no *actual* TOS, it's basically a written set of rules for having a profile publically displayed. Please listen to them to **KEEP** a profile on this bot. Do note that if you get banned on the bot, you are not banned on AuroraChat, but information you put on your profile may be subject to moderation actions onto you.</p>
        <p>Do note that if a moderation action is taken on your AuroraChat account, your profile will be marked as Read-Only instead of Banned as, i get it, you were banned and people may try to impersonate you, happened to me when I got banned from a server once, they thought i was ban evading!</p>
        <p>Read Only = you can only read the contents, not write to it, think of there being one pen to your peice of paper and it's locked away</p>
        <p>Banned = nobody can see your profile nor can you edit it, Read Only is automatically turned on</p>
        <p>Do not be mean to others in bio, nor ragebait Aurith, if Aurith bans you from his commands, that's on you, not him (I'M ENTIRELY JOKING! AURITH ISNT AN AI! HAHAHAHHAHAHHAHAHAHHAHAHAHHAAHAHHAHAH)</p>
        <p>Duplicate friend codes are just removed if you might not actually own it... unless the first account has in it's bio that you're an alt</p>
        <p>No gubbi</p>
        <p>No DBZ, Demonkingpiccolo is exempt because he actually came from abridged</p>
        <p>DONT FUCKING PING WITH THE PROFILE SYSTEM! NOT EVEN YOURSELF! :despair:</p>
        <p>Dont say who you arnt, mostly if they are banned... you could end up getting banned by me while i am running on pure boredom at 8 in the morning w/o sleep</p>
        </body></html>
        ''')

    @app.route('/faq')
    def faq():
        return flask.render_template_string('''
        <html><body>
        <h2>FAQ</h2>
        <p>Why am i banned/ignored/on write lock/blah blah blah | Open a ticket in the Unitendo server or go to <a href='../rules'>/rules</a> and see if you broke any of those rules...<p>
        <p>Who moderates Aurith? | Me, me, and Lmutt090 (me)</p>
        <p>Go to sleep... | no</p>
        <p>What is Aurith? | FINALLY, A USEFUL QUESTION :D anyways, Aurith is a profile bot, very cool? no? oh... darn</p>
        <p>Do you log IP's? | HAHA! NO! but we use cloudflared for hosting, everything is subject to Cloudflare's TOS</p>
        <p>What happened to my profile? | I fucked up the database... I'M SORRRYYYYYY 😭</p>
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

    @app.route('/important/api')


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
    return t