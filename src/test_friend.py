import socket
import time
import os
from cryptography.fernet import Fernet

# this creates a fake file to send to the real user
filename = "test_secret.txt"
with open(filename, "w") as f:
    f.write("This is a secret message from the Ghost Friend!")

# locks the file just like the real program does
key = Fernet.generate_key()
f = Fernet(key)

with open(filename, "rb") as file:
    file_data = file.read()
encrypted_data = f.encrypt(file_data)

# save the locked file temporarily
enc_filename = filename + ".encrypted"
with open(enc_filename, "wb") as file:
    file.write(encrypted_data)

file_size = os.path.getsize(enc_filename)
seq_num = 500 # random ticket number
sender_email = "ghost@test.com"

print(f"Ghost Friend is ready to send '{filename}' to you...")

# this calls/connects to your main program (this test is running on localhost)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 9998)) # Connect to the user's File Listener
    
    # sends shipping label/header: filename|filesize|seq_num|key|sender_email
    header = f"{filename}|{file_size}|{seq_num}|{key.decode('utf-8')}|{sender_email}"
    s.send(header.encode("utf-8"))
    time.sleep(0.1)
    
    # sends the actual file now
    with open(enc_filename, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk: break
            s.send(chunk)
            
    print("Ghost Friend sent the package successfully!")
    s.close()
    
except Exception as e:
    print(f"Ghost Friend could not connect! Is your main program running? Error: {e}")

# this deletes the temp files
os.remove(filename)
os.remove(enc_filename)