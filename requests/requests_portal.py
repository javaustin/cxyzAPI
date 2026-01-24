import json

import requests, ast

apiKey = "TSmTS2us5INUfhw2"

def get_request(uri):
    headers = {"Accept" : "application/json", "X-API-KEY" : apiKey}

    response = requests.get(uri, headers = headers)

    print(f"Status code: {response.status_code}")

    return response.text

def post_request(uri, body: dict = None):
    headers = {"Content-Type": "application/json", "X-API-KEY": apiKey}
    response = requests.post(uri, headers=headers, json=body or {})

    print(f"Status code: {response.status_code}")

    return response.text

__all__ = ["post_request", "get_request"]

while True:
    method = input("select GET or POST: ")
    
    if method == "GET":
        url = input("enter url: ")

        resp = get_request(url)

        print(json.loads(resp))
    
    if method == "DELETE":
        url = input("enter url: ")

        resp = requests.delete(url, headers = {"X-API-KEY" : apiKey})

        print(resp.text)

    if method == "POST":
        url = input("enter url: ")

        input_ = input("input data (dict): ")
        
        if input_ != "":
            data = ast.literal_eval(input_)
            resp = post_request(url, data)

        else:
            resp = post_request(url)

        print(json.loads(resp))

