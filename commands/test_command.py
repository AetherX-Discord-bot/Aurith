from dependants.reply import reply

# This is your command information
COMMAND = "at hello"
HIDDEN = True
INFO = None
ARGS = True
DISPLAY = "at hello [anything goes here :3]"
# COMMANDS = ['at hello', 'at hi']

def run(ctx, full):
    reply("Hello, I'm Dr. ****")
    reply(f"I recived {ctx} and {full} from new-bot.py")