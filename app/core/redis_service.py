import json 
from app.core.redis import redis_client

REGISTRATION_PREFIX = "registration:"
OTP_PREFIX = "otp:"
COOLDOWN_PREFIX = "cooldown:"

def save_registration_data(email: str,data:dict,ttl:int = 1800):
    redis_client.setex(
        registration_key(email),
        ttl,
        json.dumps(data)
    )

def get_registration_data(email:str):
    data = redis_client.get(registration_key(email))
    if not data:
        return None
    return json.loads(data)

def delete_registration_data(email: str):
    redis_client.delete(registration_key(email))

def registration_key(email:str):
    return f"{REGISTRATION_PREFIX}{email}"

def registration_exists(email:str):
    key = registration_key(email)
    return redis_client.exists(key) 

def otp_key(email:str):
    return f"{OTP_PREFIX}{email}"   

def cooldown_key(email:str):
    return f"{COOLDOWN_PREFIX}{email}"

def save_otp(
        email: str,
        otp_hash: str,
        ttl: int=300
):
    redis_client.setex(
        otp_key(email),
        ttl,
        otp_hash
    )

def get_otp(email: str):
    return redis_client.get(
        otp_key(email)
    )

def delete_otp(email: str):
    redis_client.delete(
        otp_key(email)
    )

def start_cooldown(
        email: str,
        ttl: int = 30
):
    redis_client.setex(
        cooldown_key(email),
        ttl,
        "1"
    )  

def cooldown_exists(email: str):
    return redis_client.exists(
        cooldown_key(email)
    )

def delete_cooldown(email:str):
    redis_client.delete(
        cooldown_key(email)
    )

