from dependants.reply import reply
import sqlite3


COMMAND = "profile"
DISPLAY = "profile {username}"
ARGS = True
INFO = "View the profile of another user"

def run(ctx, full):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    musername = full[8:].strip()
    if not musername:
        musername = ctx.username

    cursor.execute("SELECT * FROM users WHERE AUusername=?", (musername,))
    user = cursor.fetchone()
    if user:
        if user[12] == 1:
            reply('This user has been banned from Aurith')
            return
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
            if not profile:
                profile = "G O D"
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
            reply(f"{musername}'s profile doesn't exist")
    else:
        reply("No profile found.")
    conn.close()