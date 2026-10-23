# cxyzAPI
An async [quart](https://quart.palletsprojects.com/en/latest/) based API to write database entries and cache game servers for the [CXYZ](https://github.com/javaustin/cxyz) plugin
<br></br>
#### ⚠️ Important Notes
- This API is built to supplment the Spigot plugin CXYZ. You can view it [here](https://github.com/javaustin/CXYZ).  
- This project is IN PROGRESS as of February 2026. Please do not expect support as the project has not reached a finalized state.

---

## Outline
### Authentication (all services)

#### Every request should have:
- "X-Identifier": The API key or plugin key. Identifies who is sending the request  
- "X-Timestamp": Unix timestamp  
- "X-Signature": HMAC Signature over a payload, identifier, and timestamp using secret    
#### Every service should have:
- a config file containing a list of subscribers with  
- identifier: the identifying name of the service  
- ip_address: the IPv4 address to post towards  
- secret: the private key of the service used to hash into a signature header    
#### To send:
- Compose a signature: `message = identifier + "\n" + timestamp + "\n" + payload`
- Generate signature: `HMAC_SHA256(secret, message)`
- Send (with all headers)  
#### To recieve:
- Validate identifier, timestamp: (in headers) reject if identifier not found in local config, reject if timestamp is too old (> 30s?)
- Generate signature: use local config secret for the given server, compose the message, and generate
- Compare

---

### Validation
- In general, plugin classes are designed to mirror the SQL table that exists to store their entries.  
- So an object of `MyExampleClass{name="Java",id=3}` is stored in a table of `myExampleClass(TEXT name, INTEGER id)`.  
- Even for values that are  (non-primitive) objects (e.g. ranks, channels...), the plugin only prepares its identifier in the payload, so it can be looked up again on the server.   
  
#### API (db)
- Specific endpoints are used to modify data, most of which require a distinct key ("id", "uuid") to access a row(s)  
- Beyond this anything is fair game, as long as an SQL error isn't thrown because you provided an invalid schema, you should be okay  
- Resolving values inside objects is a responsibility of the plugin  
#### Plugin (server)
The plugin accepts json objects which are then parsed into their respective classes with GSON library
Invalid values may exist (non-existent ranks) but they are resolved during runtime  

---

### Functionality

#### API (db)
- The IP address of each server must point to the port the plugin is using
- Receive POSTs to perform actions (only with authorization)
##### Writes
- Recieves POST `/{table}/{command}` e.g. `/user/modify`, or `/punishment/delete`)
- Payload contains the entire object e.g. `{"uuid" : '...' , "username" : '...'}` 
- Returns only status code and message (no data)
- Posts all affected rows to all subscribing servers in format of `/{table}Delivery`
##### "Reads"
- Since our data is updated automatically after writes (thru table deliveries), the only need to ask for data is on startup or a corrupt state  
- Recieves POST "/cache"   
- Payload is a string list of tables  `{"tables" : ["users", "punishents", ...]}` 
- Returns only status code and message (no data)  
- Posts table(s) to all subscribing servers in format of /{table}Shipment (servers can decide to accept/reject this data)  
- Also supported: GET "/table/id/attribute", or GET "/table/id", or just GET "/table" but should not be used for the plugin unless you really want to live that async life  
##### Read only services
- We can allow access to the API for certain integrations in a read-only state  
- Authorization for this will only require a single API key tied to a in-server player account  
- Example url: /api/users?uuid={uuid}  

#### Plugin (server)
The plugin ONLY accepts requests on the port it defined in config.yml. Do not use the Minecraft default port (25565) or your data will never reach the plugin  
  
- Recieves POSTs of {table}Shipment or {table}Delivery
- Plugin verifies data (version #, GSON verifies schema)
- Plugin simply copies the payload provided to its internal memory and logs the action
- Plugin also recieves POSTs of server actions (e.g. /kick, /sendMessage) that must be initialized server to server.

> Note we use the term plugin and server interchangeably. "Plugin" refers to the Minecraft plugin that runs on the Minecraft server. "Server" just refers to a server a plugin runs on.
