import time
import string
import secrets
import hashlib

#Utility function to generate a token every time the user create a new stock.
#I ask chat gpt for this, and also i use the logic of my previous codes of my work.
def generate_token(length=40):
    alphabet = string.ascii_letters + string.digits
    timestamp = str(int(time.time() * 1000))  
    random_chars_length = length - len(timestamp)
    random_chars = ''.join(secrets.choice(alphabet) for _ in range(random_chars_length))
    return timestamp + random_chars

#Return the hash of the user
def hash_value(string):
    hash = hashlib.sha1()
    hash.update(string.encode())
    return hash.hexdigest()
