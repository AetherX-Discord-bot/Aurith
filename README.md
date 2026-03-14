# Aurith

Aurith is a Python-based chat bot designed for AuroraChat servers.  
It connects to the AuroraChat server, listens for messages, and responds to commands while maintaining user profiles stored in a local SQLite database.

## Features

- A user profile system stored in SQLite
- Command-based interaction through chat
- Badge assignment system (WIP)
- Message tracking per user and saved in console because of the manual sending support
- Console input support for sending messages manually

## Commands

Aurith commands begin with `/at`.

### General

- `/at help` – Displays available commands
- `/at credits` – Shows project credits
- `/at whoami` – Shows detected username and platform
- `/at online` – Shows online users via AuroraChat
- `/at donate` – Displays the donation link

### Profile System

- `/at register` – Registers your AuroraChat account in the profile system
- `/at profile [username]` – View a user's profile
- `/at delete` – Remove your profile

### Profile Editing

- `/at setbio <bio>` – Update your bio
- `/at setfc <friend code>` – Set a Nintendo 3DS friend code
- `/at setdisplayname <name>` – Set your display name

Friend codes must contain exactly **12 digits**.

### Badge Commands

- `/at badge list [username]`
- `/at badge add <username> <badge>`
- `/at badge remove <username> <badge>`

Badge assignment requires permission in the database.

## Database

Aurith stores user information in a SQLite database named:

`database.db`

### Users Table

| Column | Description |
|------|-------------|
| id | Primary key |
| display | Display name |
| AUusername | AuroraChat username |
| Discordusername | Linked Discord username |
| bio | User biography |
| friend_code_3ds | Nintendo 3DS friend code |
| messages_sent | Number of messages sent |
| badges | Comma-separated badge list |
| can_assign_badges | Badge assignment permission |
| owner | Owner flag |

The database is created automatically on first launch.
