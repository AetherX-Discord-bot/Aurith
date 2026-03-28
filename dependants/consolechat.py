import threading
import sqlite3
import sys
import time
import secrets
import hashlib
from dependants.reply import reply

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
            exists = cursor.execute("SELECT * FROM users WHERE AUusername=?", (musername,)).fetchone()
            if exists:
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
                    reply(f"A new pokestaff has appeared in the wild... it's {pokestaff} \nUse /at pokehunt to hunt for pokestaff")
                except Exception as e:
                    print(f"Error adding pokestaff: {e}")
        elif line.lower().strip() == '/at':
            reply(input('Say what?'), False)
        elif line.lower().strip() == '/rc-car':
            reply(input('Say what?'), False, True)
        elif line.lower().strip() == '/flee':
            reply("Lmutt090 has fleed, no EXP has been gained", False, True)
        elif line.lower().strip() == '/appear':
            reply("A wild Sylveon has appeared! \nIt's Rainy Day (Lmutt090)", False, True)
        elif line.lower().strip() == '/encounter':
            reply("Yall have encountered a wild Sylveon! \nAparrently it's name is Rainy Day (Lmutt090)", False, True)
        else:
            reply(line, True)