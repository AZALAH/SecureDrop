"""import socket
import time

# UDP Socket for broadcasting setup
broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# creates fake user named "Ghost"
ghost_email = "ghost@test.com"
message = f"ONLINE:{ghost_email}"

print(f"User ({ghost_email}) is now broadcasting availability...")

# yells every 2 seconds so the main app sees us
try:
    while True:
        broadcaster.sendto(message.encode("utf-8"), ("<broadcast>", 9999))
        time.sleep(2)
except KeyboardInterrupt:
    print("\nGhost went offline.")"""


import socket
#import time
import sys

# Make sure an email was passed in
if len(sys.argv) < 2:
    print("Error: No email provided to test_online.py")
    print("Usage: python test_online.py <email>")
    exit(1)

# Get the email sent from the main program
user_email = sys.argv[1]

# UDP Socket setup
broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

message = f"ONLINE:{user_email}"

#print(f"User ({user_email}) is now broadcasting availability...")

# Broadcast every 2 seconds
"""try:
    while True:
        broadcaster.sendto(message.encode("utf-8"), ("<broadcast>", 9999))
        time.sleep(2)
except KeyboardInterrupt:
    print("\nUser went offline.")"""
