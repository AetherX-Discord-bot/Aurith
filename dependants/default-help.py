from dependants.reply import reply
from dependants.loader import commands

# base variables that the loader expects
info = "Shows this help message for all commands"
hidden = True

# optional triggers (your loader already checks COMMANDS or COMMAND)
COMMANDS = ["at help", "at commands"]

def run(ctx):
    """
    ctx is the dictionary your loader passes:
    {"username": ..., "platform": ..., "receiver": ...}
    """
    # build a help message using the other commands
    msg = "Available commands:\n"
    allcommands = commands()
    for cmd in allcommands:
        if getattr(cmd, "HIDDEN", False):
            continue
        triggers = getattr(cmd, "COMMANDS", [getattr (cmd, "DISPLAY", (getattr(cmd, "COMMAND", None)))])
        triggers = [t for t in triggers if t]
        desc = getattr(cmd, "INFO", None) or "No description"
        for trigger in triggers:
            msg += f"/{trigger} - {desc}\n"

    # now send the message using your reply function or print
    print(f"[HELP] Requested by {ctx['username']}:")
    print(msg)