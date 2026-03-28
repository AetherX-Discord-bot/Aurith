import os
import importlib

def _load_commands():
    commands_list = []
    helpcommand = importlib.import_module("dependants.default-help")
    try:
        for file in os.listdir("commands"):
            if not file.endswith(".py") or file == "__init__.py":
                continue

            filepath = os.path.join("commands", file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if "from dependants.reply import reply" not in content and file != "help.py":
                print(f"Skipping {file}, not a valid command, please import the reply function.")
                continue

            module_name = f"commands.{file[:-3]}"
            module = importlib.import_module(module_name)

            if file == "help.py":
                print("You have a custom help command, the default will be overridden")
                helpcommand = module
                continue

            commands_list.append(module)
    except Exception as e:
        print(e)
        return []
    finally:
        commands_list.append(helpcommand)
        return commands_list

def commands():
    # simple wrapper to return the commands
    return _load_commands()

def loader():
    return _load_commands()