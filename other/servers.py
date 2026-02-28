import json

class Server:
    servers : list[Server] = []
    api : Server = None


    def __init__(self, identifier, ip, secret):

        if not all([identifier, ip, secret]):
            raise RuntimeError("Missing parameters")

        self.identifier = identifier
        self.ip = ip
        self.secret = secret

    @staticmethod
    def load_servers():
        with open("config.json", "r") as config:
            data = json.load(config)

            if not data["servers"]:
                raise RuntimeError("No servers found in config.json.")

            for server in data["servers"]:
                identifier = server
                ip = data["servers"][identifier]["ip-address"]
                secret = data["servers"][identifier]["secret"]

                if not all([identifier, ip, secret]):
                    continue

                Server.servers.append(Server(identifier, ip, secret))

    @staticmethod
    def load_api():
        with open("config.json", "r") as config:
            data = json.load(config)

            if not data["API"]:
                raise RuntimeError("Missing API server data")

            identifier = "API"
            ip = data[identifier]["ip-address"]
            secret = data[identifier]["secret"]

            Server.api = Server(identifier, ip, secret)

    @staticmethod
    def get_server(identifier):
        for server in Server.servers:
            if server.identifier == identifier:
                return server

        return None


    def __str__(self) -> str:
        return self.identifier + self.ip + self.secret
