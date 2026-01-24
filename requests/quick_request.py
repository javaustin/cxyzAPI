# Re-defining the quick test functions after code execution reset
import asyncio
import random
import time
import uuid
from typing import List

apiKey = "TSmTS2us5INUfhw2"
base_url = "http://127.0.0.1:5000"

import requests

def get_request(uri):
    headers = {"Accept": "application/json", "X-API-KEY": apiKey}
    response = requests.get(uri, headers=headers)
    # print(f"GET request to {uri}")
    # print(f"Status code: {response.status_code}")
    # print(response.text)

    if response.status_code != 200:
        print(response.status_code, response.text, uri)

    return response.json()

def delete_request(uri):
    headers = {"Accept": "application/json", "X-API-KEY": apiKey}
    response = requests.delete(uri, headers=headers)
    # print(f"DELETE request to {uri}")
    # print(f"Status code: {response.status_code}")
    # print(response.text)

    if response.status_code != 200:
        print(response.status_code, response.text, uri)

    return response.json()

def post_request(uri, body: dict = None):
    headers = {"Content-Type": "application/json", "X-API-KEY": apiKey}
    response = requests.post(uri, headers=headers, json=body or {})
    # print(f"POST request to {uri}")
    # print(f"Request body: " + str(body).replace("\n", ""))
    # print(f"Status code: {response.status_code}")

    if response.status_code != 200:
        print(response.status_code, response.text, uri, body)

    return response.json()

def create(uuid):
    return post_request(f"{base_url}/party/create", {"sender_uuid": uuid})

def disband(uuid):
    return post_request(f"{base_url}/party/disband", {"sender_uuid": uuid})

def invite(sender_uuid, recipient_name):
    return post_request(f"{base_url}/party/invite", {"sender_uuid": sender_uuid, "recipient_name": recipient_name})

def join(sender_uuid, inviter_name):
    return post_request(f"{base_url}/party/join", {"sender_uuid": sender_uuid, "inviter_name": inviter_name})

def leave(target_uuid):
    return post_request(f"{base_url}/party/leave", {"target_uuid": target_uuid})

def list_(sender_uuid):
    return post_request(f"{base_url}/party/list", {"sender_uuid": sender_uuid})

def remove(sender_uuid, target_name):
    return post_request(f"{base_url}/party/remove", {"sender_uuid": sender_uuid, "target_name": target_name})

def set_public(sender_uuid, value = None):
    return post_request(f"{base_url}/party/public", {"sender_uuid": sender_uuid, "value": value})

def set_leader(sender_uuid, target_name):
    return post_request(f"{base_url}/party/set_leader", {"sender_uuid": sender_uuid, "target_name": target_name})

def get_party(uuid):
    return get_request(f"{base_url}/party/{uuid}")

def wipe():
    return delete_request(f"{base_url}/party/wipe")

def warp(sender_uuid):
    return post_request(f"{base_url}/party/warp", {"sender_uuid": sender_uuid})

def get_punishment(id):
    return get_request(f"{base_url}/punishment/get_one/{id}")

def get_punishments(uuid):
    return get_request(f"{base_url}/punishment/get_many/{uuid}")

def set_punishment(obj):
    return post_request(f"{base_url}/punishment/set", {"punishment" : obj})

def edit_punishment(obj, id):
    return post_request(f"{base_url}/punishment/edit", {"punishment" : obj, "id" : id})

def delete_punishment(id):
    return delete_request(f"{base_url}/punishment/delete/{id}")

a_punishment = { # only thing we should require from the database is the player uuid
        "id" : 1,
        "username" : "carrot",
        "modUsername" : "kitty",
        "modUUID" : "london",
        "type" : "ban",
        "issuedTimestamp" : 23523623,
        "effectiveUntilTimestamp" : 174962362603949,
        "expireTimestamp" : 2436234623,
        "reason" : "way too lame"
    }

def random_punishment():
    return {
        "id" : random.randint(0, 10000),
        "username" : random.choice(["Skeppy", "DaddyMekealian", "austinyoung", "changeisnothing", "barryManilow", "WalterWhite", "carrot", "kitty"]),
        "modUsername" : random.choice(["Skeppy", "DaddyMekealian", "austinyoung", "changeisnothing", "barryManilow", "WalterWhite", "carrot", "kitty"]),
        "modUUID" : " ".join(random.choice("a b c d e f 0 1 2 3 4 5 6 7 8 9".split(" ")) for i in range(16)).replace(" ", ""),
        "type" : random.choice(["warn", "mute", "kick", "ban"]),
        "issuedTimestamp" : int(time.time()),
        "effectiveUntilTimestamp" : int(time.time()) + random.randint(60, 86400),
        "expireTimestamp" : random.choice([int(time.time()) + (86400 * 7), -1]),
        "reason" : random.choice(["bad behavior", "goonery", "mischief", "hacking", "being an annoyance"])
    }

