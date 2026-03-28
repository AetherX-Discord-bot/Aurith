from dependants.request import send_request
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the directory the script is run from
load_dotenv(dotenv_path=Path(os.getcwd()) / ".env")

CONFIG = {
    "owner": os.getenv("owner") or "default_owner",
    "username": os.getenv("username") or "default_bot",
    "password": os.getenv("password") or "default_pass",
    "rawchat_key": os.getenv("rawchat_key") or None,
    "platform": "BOT",
}

def reply(text, consolechat=False, raw=False):
    if CONFIG.get("rawchat_key"):
        if raw:
            payload = {
                "cmd": "RAWCHAT",
                "rawkey": CONFIG["rawchat_key"],
                "content": f'{text}',
                "platform": CONFIG["platform"]
            }
        elif consolechat:
            payload = {
                "cmd": "RAWCHAT",
                "rawkey": CONFIG["rawchat_key"],
                "content": f'~Aurith\'s Dev~ {CONFIG["owner"]}: {text}',
                "platform": CONFIG["platform"]
            }
        else:
            payload = {
                "cmd": "RAWCHAT",
                "rawkey": CONFIG["rawchat_key"],
                "content": f'~Bot~ {CONFIG["username"]}: {text}',
                "platform": CONFIG["platform"]
            }
    else:
        payload = {
            "cmd": "CHAT",
            "content": text,
            "username": CONFIG["username"],
            "password": CONFIG["password"],
            "platform": CONFIG["platform"]
        }
    send_request(payload)