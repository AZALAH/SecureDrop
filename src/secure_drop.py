import os
import json
import hashlib
import base64
import time
import sys
# (no new imports needed for milestone 3)

# Imports for 
#Import for Milestone 4 and 5
import socket
import threading
from cryptography.fernet import Fernet




def user_exists():
    # This function checks if a user has already been registered on this client.
    # If the users.json file exists, it means a user account already exists.
    return os.path.exists("data/users.json")



def hash_password(password):
    # Generate a random 16-byte salt.
    # The salt makes sure that even identical passwords produce different hashes.
    salt = os.urandom(16)

    # Use the scrypt key-derivation function to hash the password.
    # scrypt is intentionally slow and memory-hard to protect against brute-force attacks.
    key = hashlib.scrypt(
        password.encode("utf-8"),  # convert password to bytes
        salt=salt,                 # add salt to the hash
        n=2**14,                   # CPU/memory cost (higher = more secure, slower)
        r=8,                       # block size parameter
        p=1,                       # parallelization parameter (keeping this low limits how fast attackers can hash passwords)
        dklen=32                   # length of the derived key in bytes
    )

    # Combine the salt and the hashed password into one value,
    # then encode it so it can be stored safely as text in JSON.
    return base64.b64encode(salt + key).decode("utf-8")



def verify_password(stored_hash, entered_password):
    # Decode the stored hash from Base64 back into raw bytes.
    decoded = base64.b64decode(stored_hash.encode("utf-8"))

    # Extract the original salt (first 16 bytes)
    salt = decoded[:16]

    # Extract the original hashed password (remaining bytes)
    key = decoded[16:]

    # Re-hash the entered password using the SAME salt and parameters.
    # If the passwords match, the hashes will match.
    new_key = hashlib.scrypt(
        entered_password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32
    )

    # Return True if the hashes match, False otherwise.
    return new_key == key

email = None

def register_user():
    # This function handles new user registration.
    # It collects user information, hashes the password securely,
    # and stores the data in users.json.

    print("No users are registered with this client.")
    choice = input("Do you want to register a new user (y/n)? ").strip().lower()
    if choice != "y":
        print("Exiting SecureDrop.")
        return

    print("Starting registration...")
    full_name = input("Enter Full Name: ").strip()
    email = input("Enter Email Address: ").strip().lower()

    # Limit password confirmation attempts to prevent infinite retries.
    MAX_TRIES = 3
    tries = 0

    while tries < MAX_TRIES:
        password = input("Enter Password: ").strip()
        confirm = input("Re-enter Password: ").strip()

        # Ensure the user typed the same password twice.
        if password != confirm:
            tries += 1
            remaining = MAX_TRIES - tries
            if remaining > 0:
                print(f"Passwords do not match. You have {remaining} attempts left.\n")
            else:
                print("Passwords do not match. Maximum attempts reached. Registration aborted.\n")
                return
        else:
            print("Passwords match!\n")
            break

    # Create the user record.
    # Note: We NEVER store the plaintext password.
    user_data = {
        "full_name": full_name,
        "email": email,
        "pw_hash": hash_password(password)
    }

    # Ensure the data directory exists.
    os.makedirs("data", exist_ok=True)

    # Save user data to users.json.
    with open("data/users.json", "w") as file:
        json.dump(user_data, file, indent=4)

    print("User registered and data saved successfully!")


def login_user():
    # This function authenticates an existing user.
    # It loads stored user data and verifies credentials securely.

    with open("data/users.json", "r") as file:
        users = json.load(file)

    print("Please log in.")
    attempts = 3

    while attempts > 0:
        email = input("Enter Email Address: ").strip().lower()
        password = input("Enter Password: ").strip()

        # Search for the user by email.
        user_data = next((u for u in users if u["email"].lower() == email), None)

        # Verify the password using the same hashing logic from registration.
        if user_data and verify_password(user_data["pw_hash"], password):
            print("Welcome to SecureDrop!")

            # Start background threads for online detection (Milestone 4).
            threading.Thread(target=start_listener, args=(email,), daemon=True).start()
            threading.Thread(target=broadcast_presence, args=(email,), daemon=True).start()

            # Start the file listener for secure file transfer (Milestone 5).
            # Each user listens on a unique port.
            file_port = 10002 if email == "ahmed@gmail.com" else 10003
            threading.Thread(
                target=start_file_listener,
                args=(email, file_port),
                daemon=True
            ).start()

            return True, email

        else:
            attempts -= 1
            if attempts > 0:
                print(f"Invalid email or password. You have {attempts} attempts left.\n")
            else:
                print("Invalid email or password. Too many failed attempts. Exiting SecureDrop.")
                return False, None

# milestone 3 addins happen here 

def add_contact(current_user_email):   # needed help but found a way to store a contact in a JSON
    os.makedirs("data", exist_ok=True)
    contacts_path = f"data/{current_user_email}_contacts.json"  # making the path for the contacts for one user 
    #if the file does NOT exist, create it so opening it won't crash
    if not os.path.exists(contacts_path):
        with open(contacts_path, "w") as f:
            json.dump({}, f)  # empty contacts

    with open(contacts_path, "r") as f:
        contacts = json.load(f)   # load the contacts currently saved

    full_name = input("Enter Full Name: ").strip()
    email = input("Enter Email Address: ").strip().lower()   # get contact name + make email lowercase
    contacts[email] = full_name

    with open(contacts_path, "w") as f:
        json.dump(contacts, f, indent=4)   # write the updated contacts back to the file

    print("Contact added successfully!")   # past lines basically save the info to the file


#updated for milestone 4 
def list_contacts(current_user_email):
    # Safety check
    contacts_path = f"data/{current_user_email}_contacts.json"
    
    # checking if the file exists so we dont crash
    if not os.path.exists(contacts_path): 
        print("No contacts found.")
        return

    # loading the saved contacts
    with open(contacts_path, "r") as f:
        contacts = json.load(f) 

    # checking if the list is empty
    if not contacts: 
        print("No contacts found.")
        return

    # milestone 4 changes
    print("Online Contacts:")
    found_online_friend = False
    
    # we loop through your saved contacts
    for email, name in contacts.items():
        # THE CHECK: is this saved contact also in our 'online_contacts' list?
        if email in online_contacts:
            print(f"  * {name} <{email}>")
            found_online_friend = True
    
    # if nobody was found online, tell the user
    if not found_online_friend:
        print("  (No friends are online right now)")


# global dictionary to store friends who are online right now.
# format: { "user@gmail.com": " the ip" }
online_contacts = {}

# NEW: this variable allows the main shell to talk to the file listener.
# it acts like a signal. when the user types 'y' or 'n', we save it here.
transfer_decision = None

# this function listens for "I AM ONLINE" messages.
# if the person shouting is in our contacts, we mark them as online.
# this function listens for "I AM ONLINE" messages.
# if the person shouting is in our contacts, we mark them as online.
def start_listener(current_user_email):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port_number = 9999
    
    try:
        s.bind(("0.0.0.0", port_number))
        
        # if the lines above worked, this prints. if they failed, it jumps to 'except'.
        # i commented this out so the user doesnt see technical stuff when logging in.
        # print(f"Listener started successfully! Waiting for friends on port {port_number}...")
    except Exception as e:
        print(f"Error! Could not start listener: {e}")
    
    while True:
        data, addr = s.recvfrom(4096)
        message = data.decode("utf-8")
        
        # we expect messages like: "ONLINE:user@gmail.com"
        if message.startswith("ONLINE:"):
            sender_email = message.split(":")[1]
            
            # ignore our own shouts (we know we are online)
            if sender_email == current_user_email:
                continue
            
            # check if this person is in our contacts list
            contacts_path = f"data/{current_user_email}_contacts.json"
            
            if os.path.exists(contacts_path):
                with open(contacts_path, "r") as f:
                    contacts = json.load(f)
                
                # the if user is online check
                if sender_email in contacts:
                    # save their email and IP address so we can send files later
                    online_contacts[sender_email] = addr[0] 
                    #print(f"\n[FRIEND DETECTED] {contacts[sender_email]} is online!")

# this function screams "I AM HERE" to everyone on the network every 1 second.
# this allows other users to know you are online.
def broadcast_presence(user_email):
    # UDP socket for broadcasting
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # this option allows us to send data to everyone (255.255.255.255)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # LOCAL_TEST mode is used only for debugging on a single machine.
    # When LOCAL_TEST is False, SecureDrop relies entirely on LAN broadcast,
    # which allows online detection across different devices on the same network.
    LOCAL_TEST = False
    while True:
        # the message we shout: "ONLINE:user@gmail.com"
        message = f"ONLINE:{user_email}"
        
        # shout it to port 9999 (where everyone is listening on the LAN)
        broadcaster.sendto(message.encode("utf-8"), ("<broadcast>", 9999))
        
        if LOCAL_TEST:
            broadcaster.sendto(message.encode("utf-8"), ("127.0.0.1", 9999))
        
        # wait 1 second before shouting again so the network doesn't crash
        time.sleep(1)





# MILESTONE 5
# this function creates the secert key that when you run it, it's always unique.
# Fernet is the standard tool used for Symmetric Encryption.
# The ".generate_key()" command creates random strings of random values
# and then the key is returned so you can use it to lock the file.
def generate_key():
    return Fernet.generate_key()

# this function takes the file that is going to be sent, and then 
# encrypts it so it is unreadable and saves that new file. The only way to see the readable
# version is by using the key made to unlock the file.
def encrypt_file(filepath, key):
    f = Fernet(key) # this makes the program only use this key for locking files.
    
    # read the original file data
    # rb stands for read binary numbers, this is needed so we can encrpyt any type of file.
    with open(filepath, "rb") as file:
        file_data = file.read()
        
    # Encrypt the data
    encrypted_data = f.encrypt(file_data)
    
    # Save the encrypted data to a new file
    enc_filename = filepath + ".encrypted" # names the new file that was locked
    with open(enc_filename, "wb") as file:
        file.write(encrypted_data) # copies all the data in the unreadable file and saves it in the new file created for it.
        
    return enc_filename

# this function unlocks the file. 
# it takes the encrypted file and the secret key, unlocks it,
# and saves the original file back to your computer.
def decrypt_file(filepath, key):
    f = Fernet(key)
    
    with open(filepath, "rb") as file:
        encrypted_data = file.read()
        
    # the actual unlocking happens here using the key.
    decrypted_data = f.decrypt(encrypted_data)
    
    # saving the unlocked data back to a file and removes the ".encrypted" from the name.
    dec_filename = filepath.replace(".encrypted", "")
    with open(dec_filename, "wb") as file:
        file.write(decrypted_data)
        
    return dec_filename

# global dictionary to remember the next sequence number we expect from each user.
# example: the email is ali@gmail.com and the sequence number is 501
# this means if bob sends anything that isnt 501, we reject it.
user_sequence_numbers = {}


# Milestone 5
# this function checks for replay attacks using sequence numbers.
# we compare the number attached to the file with the number we are expecting.
# if they dont match (like sending an old number that is already been used), we block it.
def check_replay_attack(sender_email, incoming_seq_num):
    
    # if this is a new user or  their first time connecting, we accept whatever number 
    # they start with as the random seed and start counting from there.
    if sender_email not in user_sequence_numbers:
        user_sequence_numbers[sender_email] = incoming_seq_num + 1
        return False # safe (first time/handshake)
        
    expected_seq_num = user_sequence_numbers[sender_email]
    
    # if the number they sent is NOT what we expected, it might be a replay attack.
    if incoming_seq_num != expected_seq_num:
        # actually, if its LOWER than expected, its definitely a replay.
        if incoming_seq_num < expected_seq_num:
            return True # yes, attack detected which means they are using an old ticket.
            
    # if it matches, we update our expectation for next time.
    user_sequence_numbers[sender_email] = incoming_seq_num + 1
    return False # safe


# MILESTONE 5
# this function acts as the server for file transfers.
# it listens on a specific port for incoming files from friends.
# it receives the locked file, checks for replay attacks, and then decrypts it.
def start_file_listener(current_user_email, file_port):
    # accessing the global variable so we can read the user's choice
    global transfer_decision
    
    # we use TCP here because it guarantees the file arrives perfectly.
    # using the provided file_port so each user can have a unique listener.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # === NEW: use the passed-in port number instead of hardcoding it ===
    port_number = file_port  # keeping it in a variable for printing later
    
    try:
        server.bind(("0.0.0.0", port_number))  # bind to custom port
        server.listen(5)
        
        # if the lines above worked, this prints. if they failed, it jumps to 'except'.
        # i commented this out so the user doesnt see technical stuff when logging in.
        # print(f"File Listener started successfully on port {port_number}...")
    except Exception as e:
        print(f"Error! Could not start file listener: {e}")
        return  # stop the listener if binding fails

    while True:
        # is the specific phone call/ connection with the person sending the file.
        friend_connection, address = server.accept()
        
        #so i say its getting the heder for the file being sent, 
        # like a shipping label on a package and u have the infomation of who sent it, 
        # where it is going and the size of it before u open the package/file
        # we grab a small amount of data first to read the file info (name, size, key).
        header_data = friend_connection.recv(1024).decode("utf-8")
        
        try:
            # reading the label to understand what is coming
            filename, filesize, seq_num, key, sender_email = header_data.split("|")
            
            # converting numbers from text back to math numbers
            seq_num = int(seq_num)
            filesize = int(filesize)
            key = key.encode("utf-8") # turning the key back into bytes so we can use it.
            
            # === NEW: PAUSE AND WAIT FOR MAIN SHELL ===
            # telling the user someone is sending a file and asking for a yes or no.
            print(f"\n[INCOMING] Contact '{sender_email}' is sending a file.")
            print("Type 'y' or 'n' in the shell to Accept or Deny.")
            print("secure_drop> ", end="", flush=True) # reprints prompt so u can type
            
            # resetting the signal to empty before we start waiting
            transfer_decision = None
            
            # we loop here forever until the user types 'y' or 'n' in the main shell.
            # we check the global variable every 0.5 seconds.
            while transfer_decision is None:
                time.sleep(0.5)
            
            # once the loop breaks, it means the user typed something!
            # if they said anything other than 'y', we decline.
            if transfer_decision != 'y':
                print(f"\n[INFO] Transfer declined.")
                friend_connection.close()
                print("secure_drop> ", end="", flush=True)
                continue
            # ==========================================
            
            print(f"\n[INCOMING] File request from {sender_email}...")

            # checking the sequence number to ensure this isnt a replay attack.
            if check_replay_attack(sender_email, seq_num):
                print(f"[SECURITY ALERT] Replay attack detected from {sender_email}! Blocking file.")
                friend_connection.close()
                continue
            
            # 2. GET THE ACTUAL FILE (CONTENT)
            encrypted_filename = f"received_{filename}.encrypted"
            total_collected_so_far = 0
            
            with open(encrypted_filename, "wb") as f:
                # keep looping until we have collected the full size of the file
                while total_collected_so_far < filesize:
                    
                    # grab a big scoop of data (4096 bytes)
                    file_piece = friend_connection.recv(4096)
                    
                    # if the scoop is empty, the transfer is done/broken
                    if not file_piece: 
                        break
                    
                    # save this piece to our computer
                    f.write(file_piece)
                    
                    # add the size of this piece to our total count
                    total_collected_so_far += len(file_piece)
            
            print(f"File received. Decrypting...")
            
            # decrypting the file using the key we just received.
            try:
                final_filename = decrypt_file(encrypted_filename, key)
                print(f"[SUCCESS] File saved as: {final_filename}")
            except Exception as error_message:
                print(f"[ERROR] Decryption failed: {error_message}")
                
        except ValueError:
            print("[ERROR] Received a bad file header.")
        
        # hang up the phone/ connection ends
        friend_connection.close()
        
        # there was a bug where the prompt look frozen after getting the 
        # message and this print statemnt fixes that.
        print("secure_drop> ", end="", flush=True)



# MILESTONE 5 ENDS


# updated for Milestone 5
def shell(current_user_email):
    # accessing the global variable so we can update it when user types y or n
    global transfer_decision
    
    while True: # start loop 
        # we need to split the input to get the command and the file info separately
        user_input = input("secure_drop> ").strip()
        cmd_parts = user_input.split()
        
        if not cmd_parts:
            continue
            
        cmd = cmd_parts[0].lower() # grab the first word as the command
        
        # yes and no checks
        if cmd in ['y', 'yes', 'n', 'no']:
            # if they typed 'yes', we just save y to the global variable and same thing for no and n.
            # this ensures the listener always gets a simple y or n and doesn't get told command
            # not recongized.
            if cmd.startswith('y'):
                transfer_decision = 'y'
            else:
                transfer_decision = 'n'
                
            continue
        
        
        if cmd == "exit": #if user wants to end
            print("Exiting SecureDrop.")
            break

        elif cmd == "help": # display all the commands 4 ease of use 
            print('"add"  => Add a new contact\n"list" => List all contacts\n"send <email> <filepath>" => Securely transfer a file\n"exit" => To Exit SecureDrop')

        elif cmd == "add": #add a new email
            add_contact(current_user_email)

        elif cmd == "list":#display list
            list_contacts(current_user_email)

        elif cmd == "send":
            # checking if they typed enough information (send + email + file)
            if len(cmd_parts) < 3:
                print("Usage: send <email> <filepath>")
                continue
                
            contact_email = cmd_parts[1]
            filepath = cmd_parts[2]

            # checking if the file actually exists on the computer
            if not os.path.exists(filepath):
                print(f"Error: File '{filepath}' not found.")
                continue

            # checking if friend is ONLINE because we need their IP address to call them/ send the file.
            if contact_email not in online_contacts:
                print(f"Error: {contact_email} is not online right now.")
                continue
                
            # Determine target IP/ Local test
            LOCAL_TEST = False  # change to False for real network or true for LocAL
            if LOCAL_TEST:
                target_ip = "127.0.0.1"
            else:
                    target_ip = online_contacts[contact_email]

            # Determine target file port
            if contact_email == "ahmed@gmail.com":
                    target_port = 10002  # Ahmed's file listener port
            elif contact_email == "friend@gmail.com":
                target_port = 10003  # Friend's file listener port
            else:
                    target_port = 10002  # fallback, just in case

            print(f"Preparing to send '{filepath}' to {contact_email}...")
            #print(f"Preparing to send '{filepath}' to {contact_email} ({target_ip}:{target_port})...") 
            # the commented print statement is meant to originally we printed the IP and port to verify that file transfers were targeting the correct user during testing,
            # for the final version we hid that information to avoid exposing network details, while still using it internally.


            
            # The Packing the box/ header for the file starts
            # making a unique "ticket number" based on the clock time.
            # this prevents replay attacks because time never goes backward.
            seq_num = int(time.time()) 
            
            # making a brand new key just for this specific file.
            file_key = generate_key()
            
            # locking the file locally first so it is safe during travel/ encrypting the file.
            encrypted_file = encrypt_file(filepath, file_key)
            
            # measuring the package weight/size so the friend knows when to stop reading.
            file_size = os.path.getsize(encrypted_file)
            
            try:
                # The sending of the package/sending the file begins
                
                # dialing the friend's number/connecting to their file listener port.
                connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection.connect((target_ip, target_port)) 
                
                # The sending the shipping label/header for file starts.
                # we create the label with: filename, size, ticket number, key, and our name.
                shipping_label = f"{filepath}|{file_size}|{seq_num}|{file_key.decode('utf-8')}|{current_user_email}"
                
                # send the label/header first
                connection.send(shipping_label.encode("utf-8"))
                
                # wait a tiny bit to make sure the label doesn't get stuck to the package content.
                time.sleep(0.1) 
                
                # Now  sending the package/file process starts
                # opening the locked file and sending it piece by piece.
                with open(encrypted_file, "rb") as f:
                    while True:
                        # grab a piece of the file
                        file_piece = f.read(4096)
                        
                        # if the piece is empty, we are done
                        if not file_piece: 
                            break
                        
                        # put the piece on the truck/ internet connection
                        connection.send(file_piece)
                        
                print(f"[SUCCESS] File sent successfully to {contact_email}!")
                
                # hang up the phone/drive the truck away aka end the connection
                connection.close()
                
            except Exception as error_message:
                print(f"[ERROR] Could not send file: {error_message}")
            
        else: 
            print("Commmand not recognized! Enter 'help' for commands.\n")

# Added for Milestone 4 and Milestone 5
def main():
    print("Welcome to SecureDrop")

    if not user_exists():
        register_user()
    else:
        success, email = login_user() 
        if success:
            print("Access granted. Loading SecureDrop...")

            # milestone 4 changes
            # we must pass 'email' now so the listener knows whose contacts to check
            listener_thread = threading.Thread(target=start_listener, args=(email,), daemon=True)
            listener_thread.start()

            # milestone 4 changes
            # here is where the broadcasting starts
            # we need to tell the network who we are
            broadcast_thread = threading.Thread(target=broadcast_presence, args=(email,), daemon=True)
            broadcast_thread.start()

            # MILESTONE 5 CHANGES
            # choose unique file listener port per user
            file_port = 10000 if email == "ahmed@gmail.com" else 10001
            # this starts the file listener thread in the background
            # it allows the program to wait for incoming files constantly without freezing the rest of the app
            file_thread = threading.Thread(target=start_file_listener, args=(email, file_port), daemon=True)
            file_thread.start()

            shell(email)
        else:
            return



def test_online(email):
    # UDP Socket setup
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    message = f"ONLINE:{email}"
    broadcaster.sendto(message.encode(), ("<broadcast>", 5000))

    print(f"Broadcasted: {message}")





if __name__ == "__main__":
    main()

