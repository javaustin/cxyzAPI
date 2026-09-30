class RequestLog:
    request_id : str = ""
    urlpath : str = ""
    method : str = ""
    timestamp : int = 0
    server_id : str = "UNKNOWN"
    ip_address : str = ""
    request_body : dict = {}
    status_code : int = 0
    response_body : dict = {}
