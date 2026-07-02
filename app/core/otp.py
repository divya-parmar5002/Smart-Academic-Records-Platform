import random
from datetime import datetime, timedelta
import hashlib

def generate_otp():
    return str(random.randint(100000, 999999))

def hash_otp(otp:str)->str:
    return hashlib.sha256(otp.encode()).hexdigest()

