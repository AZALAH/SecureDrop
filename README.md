# SecureDrop

A command-line secure file-sharing system written in Python. Users register, log in, manage contacts, see which contacts are online, and send each other encrypted files with replay-attack protection.

Built as the final project for Intro to Cybersecurity at UMass Lowell (Fall 2025).

## Features

| Milestone | Feature | How it works |
|---|---|---|
| 1 | Registration | Passwords are hashed with `scrypt` and a random 16-byte salt, never stored in plain text |
| 2 | Login | Reuses the same hashing code to verify credentials, with a three-attempt lockout |
| 3 | Contacts | Each user's contacts are stored in a separate JSON file |
| 4 | Online detection | UDP broadcasts announce `ONLINE:<email>`; a background listener tracks which saved contacts are online |
| 5 | Encrypted file transfer | Each file gets a new Fernet key, is encrypted, sent over TCP, and decrypted on arrival |
| 5 | Replay protection | Every transfer carries a sequence number; out-of-order or repeated transfers are rejected |

## Requirements

- Python 3.10 or newer
- `cryptography` (for Fernet encryption)

```bash
pip install -r requirements.txt
```

## How to run

```bash
git clone https://github.com/AZALAH/SecureDrop.git
cd SecureDrop
python src/secure_drop.py
```

Run it from the repository root, since user data is saved to the `data/` folder.

1. On first launch, register with a name, email, and password.
2. Run it again and log in.
3. At the `secure_drop>` prompt:
   - `help` shows all commands
   - `add` adds a contact
   - `list` shows which contacts are online
   - `send <contact_email> <filepath>` sends an encrypted file, for example `send friend@gmail.com ./notes.txt`
   - `exit` quits

### Testing two users on one machine

Set `LOCAL_TEST = True` in `secure_drop.py` to route broadcasts and transfers through `127.0.0.1`. `src/test_online.py` and `src/test_friend.py` simulate a second user so online detection and file transfer can be tested on a single computer.

## Security notes

- Password hashing: `hashlib.scrypt` (n=2^14, r=8, p=1) with a unique salt per user, stored as base64(salt + hash)
- File encryption: Fernet (AES-128-CBC with HMAC-SHA256) with a fresh key per transfer
- The `data/` folder holds user records and is excluded from version control, so no credentials or hashes are committed

## Roadmap

- Exchange file keys securely (for example with public-key encryption) instead of sending them alongside the file
- Use constant-time comparison when verifying password hashes
- Support multiple users per client
- Handle a missing contacts file on first `add`

## Team

Built by a team of three:

- **Ahmed Salah:** registration, salted password hashing, and login authentication (milestones 1 and 2); integration and testing of online detection and file transfer
- **Adam Kazi:** per-user contact management (milestone 3) and online detection (milestone 4)
- **Orion Golden:** UDP online detection (milestone 4) and encrypted file transfer with replay protection (milestone 5)

All three tested milestones 4 and 5 together.

---

Ahmed Salah · [azalah.github.io](https://azalah.github.io) · [LinkedIn](https://www.linkedin.com/in/ahmed-salah-cs2006)
