from dependants.reply import reply
import sqlite3

COMMAND = "at set"
INFO = "Set a setting"
DISPLAY = "at set {bio/display/fc} {value}"
ARGS = True

def run(ctx, full):
    username = ctx.username
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if full.lower().strip().startswith("at set bio "):
        bio = full[11:].strip()
        if ctx.platform:
            exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
            if exists:
                if exists[12] == 1 or exists[13] == 1:
                    reply("You are in read only mode or banned")
                    return
                cursor.execute("UPDATE users SET bio=? WHERE AUusername=?", (bio, username))
                conn.commit()
                reply("Bio updated!")
            else:
                reply("You must register first!")
        else:
            exists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
            if exists:
                if exists[12] == 1 or exists[13] == 1:
                    reply("You are in read only mode or banned")
                    return
                cursor.execute("UPDATE users SET bio=? WHERE Discordusername=?", (bio, username))
                conn.commit()
                reply("Bio updated!")
            else:
                reply("You must register first!")
    elif full.lower().strip().startswith("at set fc "):
        fc_raw = full[10:].strip()
        fc_digits = ''.join(ch for ch in fc_raw if ch.isdigit())
        if len(fc_digits) != 12:
            reply("Friend code must contain exactly 12 digits (format ####-####-####). Please try again.")
        else:
            if ctx.platform:
                exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
                if exists:
                    if exists[12] == 1 or exists[13] == 1:
                        reply("You are in read only mode or banned")
                        return
                    try:
                        cursor.execute("UPDATE users SET friend_code_3ds=? WHERE AUusername=?", (fc_digits, username))
                        conn.commit()
                        reply("Friend code updated!")
                    except Exception as e:
                        reply(f"Error updating friend code: {e}")
                else:
                    reply("You must register first!")
            else:
                exists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
                if exists:
                    if exists[12] == 1 or exists[13] == 1:
                        reply("You are in read only mode or banned")
                        return
                    try:
                        cursor.execute("UPDATE users SET friend_code_3ds=? WHERE Discordusername=?", (fc_digits, username))
                        conn.commit()
                        reply("Friend code updated!")
                    except Exception as e:
                        reply(f"Error updating friend code: {e}")
                else:
                    reply("You must register first!")
    elif full.lower().strip().startswith("at set display "):
        new_name = full[15:].strip()
        if ctx.platform:
            exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
            if exists:
                if exists[12] == 1 or exists[13] == 1:
                    reply("You are in read only mode or banned")
                    return
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
            exists = cursor.execute("SELECT * FROM users WHERE Discordusername=?", (username,)).fetchone()
            if exists:
                if exists[12] == 1 or exists[13] == 1:
                    reply("You are in read only mode or banned")
                    return
                try:
                    cursor.execute("UPDATE users SET display=? WHERE Discordusername=?", (new_name, username))
                    conn.commit()
                    reply(f"Display name updated to {new_name}!")
                    username = new_name
                except Exception as e:
                    reply(f"Error updating display name: {e}")
            else:
                reply("You must register first!")