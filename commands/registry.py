from dependants.reply import reply
import sqlite3

COMMAND = "register"
INFO = "Register an account with Aurith."

def run(ctx):
    username = ctx.username
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if ctx.platform not in ["Discord", "Fluxer"]:
        exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (username,)).fetchone()
        if exists:
            reply("You are already registered!")
        else:
            cursor.execute("INSERT INTO users (AUusername) VALUES (?)", (username,))
            conn.commit()
            reply("Registration successful!")
    else:
        print(f"Register command is not available for platform {ctx.platform}. Please contact Lmutt090.")
    conn.close()