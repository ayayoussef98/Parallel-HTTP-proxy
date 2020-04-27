import sys
import os
import enum
import re
import _thread
import socket


class HttpRequestInfo(object):
    """
    Represents a HTTP request information
    Since you'll need to standardize all requests you get
    as specified by the document, after you parse the
    request from the TCP packet put the information you
    get in this object.
    To send the request to the remote server, call to_http_string
    on this object, convert that string to bytes then send it in
    the socket.
    client_address_info: address of the client;
    the client of the proxy, which sent the HTTP request.
    requested_host: the requested website, the remote website
    we want to visit.
    requested_port: port of the webserver we want to visit.
    requested_path: path of the requested resource, without
    including the website name.
    NOTE: you need to implement to_http_string() for this class.
    """

    def __init__(self, client_info, method: str, requested_host: str,
                 requested_port: int,
                 requested_path: str,
                 headers: list):
        self.method = method
        self.client_address_info = client_info
        self.requested_host = requested_host
        self.requested_port = requested_port
        self.requested_path = requested_path
        # Headers will be represented as a list of lists
        # for example ["Host", "www.google.com"]
        # if you get a header as:
        # "Host: www.google.com:80"
        # convert it to ["Host", "www.google.com"] note that the
        # port is removed (because it goes into the request_port variable)
        self.headers = headers

    def to_http_string(self):
        """
        Convert the HTTP request/response
        to a valid HTTP string.
        As the protocol specifies:
        [request_line]\r\n
        [header]\r\n
        [headers..]\r\n
        \r\n
        (just join the already existing fields by \r\n)
        You still need to convert this string
        to byte array before sending it to the socket,
        keeping it as a string in this stage is to ease
        debugging and testing.

         """
        allHeaders = ""
        header = ""
        string = self.method + ' ' + self.requested_path + ' HTTP/1.0' + '\r\n'
        for i in range(0, len(self.headers)):
            header = self.headers[i][0] + ': ' + self.headers[i][1] + '\r\n'
            allHeaders = allHeaders + header

        all = string + allHeaders + '\r\n'

        print("*" * 50)
        print("[to_http_string] Implement me!")
        print("*" * 50)
        return all

    def to_byte_array(self, http_string):
        """
        Converts an HTTP string to a byte array.
        """
        return bytes(http_string, "UTF-8")

    def display(self):
        print(f"Client:", self.client_address_info)
        print(f"Method:", self.method)
        print(f"Host:", self.requested_host)
        print(f"Port:", self.requested_port)
        stringified = [": ".join([k, v]) for (k, v) in self.headers]
        print("Headers:\n", "\n".join(stringified))


class HttpErrorResponse(object):
    """
    Represents a proxy-error-response.
    """

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def to_http_string(self):
        """ Same as above """
        errorResponse = str(self.code) + ' ' + self.message
        return errorResponse

    def to_byte_array(self, http_string):
        """
        Converts an HTTP string to a byte array.
        """
        return bytes(http_string, "UTF-8")

    def display(self):
        print(self.to_http_string())


class HttpRequestState(enum.Enum):
    """
    The values here have nothing to do with
    response values i.e. 400, 502, ..etc.
    Leave this as is, feel free to add yours.
    """
    INVALID_INPUT = 0
    NOT_SUPPORTED = 1
    GOOD = 2
    PLACEHOLDER = -1


def entry_point(proxy_port_number):
    """
    Entry point, start your code here.
    Please don't delete this function,
    but feel free to modify the code
    inside it.
    """
    proxy_port_number = int(proxy_port_number)
    setup_clientSocket(proxy_port_number)
    print("*" * 50)
    print("[entry_point] Implement me!")
    print("*" * 50)
    return None

def setup_clientSocket(proxy_port_number):
    """
    Example function for some helper logic, in case you
    want to be tidy and avoid stuffing the main function.
    Feel free to delete this function.
    """
    proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxySocket.bind(("127.0.0.1", proxy_port_number))
    proxySocket.listen(25)
    Cache = {}

    while 1:
        clientConnection, address = proxySocket.accept()
        _thread.start_new_thread(threading,(clientConnection, address,Cache))



def setup_serverSocket(pipelinedRequest: HttpRequestInfo):
    allData = []
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        IPaddress = socket.gethostbyname(pipelinedRequest.requested_host)
    except TypeError or TimeoutError:
        return None
    serverSocket.connect((IPaddress, int(pipelinedRequest.requested_port)))
    serverSocket.send(pipelinedRequest.to_byte_array(pipelinedRequest.to_http_string()))
    receivedData = serverSocket.recv(100000)
    while len(receivedData) > 0:
        allData.append(receivedData)
        receivedData = serverSocket.recv(100000)
    serverSocket.close()
    return allData


def threading(clientConnection, address, Cache):
    allRequest = bytes("", "utf8")
    while 1:
        request = clientConnection.recv(2048)
        allRequest = allRequest + request
        if allRequest[len(allRequest) - 4:] == b'\r\n\r\n':
            break
    decodedReq = allRequest.decode()
    pipelinedRequest = http_request_pipeline(address, decodedReq)

    if issubclass(type(pipelinedRequest), HttpRequestInfo):
        URL = pipelinedRequest.requested_host + ':' + str(pipelinedRequest.requested_port) + pipelinedRequest.requested_path
        searchCache = Cache.get(URL)
        if searchCache == None:
            x = setup_serverSocket(pipelinedRequest)
            Cache[URL] = x
        else:
            x = searchCache

        for pipelinedRequest in x:
            clientConnection.sendto(pipelinedRequest, address)
        clientConnection.close()
    else:
        clientConnection.sendto(pipelinedRequest.to_byte_array(pipelinedRequest.to_http_string()), address)
        clientConnection.close()


def http_request_pipeline(source_addr, http_raw_data):
    """
    HTTP request processing pipeline.
    - Validates the given HTTP request and returns
      an error if an invalid request was given.
    - Parses it
    - Returns a sanitized HttpRequestInfo
    returns:
     HttpRequestInfo if the request was parsed correctly.
     HttpErrorResponse if the request was invalid.
    Please don't remove this function,f but feel
    free to change its content
    """
    errorResponse = HttpErrorResponse(None, None)
    validity = check_http_request_validity(http_raw_data)

    if validity == HttpRequestState.GOOD:
        ret = parse_http_request(source_addr, http_raw_data)
        sanitize_http_request(ret)
        return ret

    elif validity == HttpRequestState.INVALID_INPUT:
        errorResponse.code = 400
        errorResponse.message = "Bad Request"
        return errorResponse

    elif validity == HttpRequestState.NOT_SUPPORTED:
        errorResponse.code = 501
        errorResponse.message = "Not Implemented"
        return errorResponse

    # Validate, sanitize, return Http object.
    print("*" * 50)
    print("[http_request_pipeline] Implement me!")
    print("*" * 50)
    return None


def parse_http_request(source_addr, req_str):
    """
    This function parses a "valid" HTTP request into an HttpRequestInfo
    object.
    """
    requestLine = []
    header = []
    listt = []
    port = ""

    tupless = req_str.split("\r\n")
    requestLine = tupless[0]
    if req_str[4] == '/':
        requestVar = requestLine.split(" ")
        method = requestVar[0]
        path = requestVar[1]
        version = requestVar[2]
        hostLine = tupless[1]
        hostVar = hostLine.split(":")
        headerName = hostVar[0]
        host = hostVar[1].strip()

        if len(hostVar) == 3:
            if hostVar[2].startswith('/'):
                preHost = hostVar[2]
                host = preHost[2:]
                port = 80
            else:
                preHost = hostVar[1].strip()
                host = preHost
                port = hostVar[2]

        elif len(hostVar) == 4:
            preHost = hostVar[2]
            host = preHost[2:]
            port = hostVar[3]

        else:
            host = hostVar[1].strip()
            port = 80

        for i in range(1, len(tupless) - 2):
            header = tupless[i].split(":")
            header[0] = header[0].strip()
            header[1] = header[1].strip()
            if len(header) == 3:
                del header[2]
            listt.append([header[0], header[1]])

    else:
        requestL = requestLine.split(" ")
        method = requestL[0]
        version = requestL[2]
        preHost = requestL[1]
        if 'https://' in preHost:
            preHost = preHost[8:]
        elif 'http://' in preHost:
            preHost = preHost[7:]
        hostVar = preHost.split(":")

        initHost = hostVar[0]
        if '/' in initHost:
            position = initHost.find('/')
            path = initHost[position:]
            port = 80
            host = initHost[:position]
        else:
            path = '/'
            port = 80
            host = initHost

        if len(hostVar) == 2:
            host = initHost
            if '/' in hostVar[1]:
                position = hostVar[1].find('/')
                port = hostVar[1][:position]
                path = hostVar[1][position:]
            else:
                port = hostVar[1]
                path = '/'
        for i in range(1, len(tupless) - 2):
            header = tupless[i].split(":")
            if len(header) == 3:
                del header[2]
            listt.append([header[0], header[1]])
    print("*" * 50)
    print("[parse_http_request] Implement me!")
    print("*" * 50)
    # Replace this line with the correct values.

    ret = HttpRequestInfo(source_addr, method.strip(), host, port, path.strip(), listt)
    return ret


def check_method(method):
    if method.strip().lower() == 'get':
        return True
    elif method.strip().lower() == 'put':
        return 4
    elif method.strip().lower() == 'post':
        return 4
    elif method.strip().lower() == 'head':
        return 4
    else:
        return 5


def check_HeaderStarter(string):
    if string.strip().lower() == 'host':
        return True
    else:
        return False


def check_headerLine(headerLine):
    matches = re.findall(r"(\w+)(:)\s\S+", headerLine)
    if not matches:
        return False
    else:
        return True


def check_version(string):
    if string.strip() == 'HTTP/':
        return True
    else:
        return False


def check_port(portNum):
    if portNum.isdigit():
        return True
    else:
        return False


def check_requestLineAM(requestLine):
    matches = re.findall(r"(\w+)\s\S+\s(HTTP/)\d.\d", requestLine)
    if not matches:
        return False
    else:
        return True


def check_requestLineRM(requestLine):
    matches = re.findall(r"(\w+)\s((\/\w*)+\sHTTP/)\d.\d", requestLine)
    if not matches:
        return False

    else:
        return True


def check_http_request_validity(http_raw_data) -> HttpRequestState:
    """
    Checks if an HTTP request is valid
    returns:
    One of values in HttpRequestState
    """
    port = "80"
    tupless = http_raw_data.split("\r\n")
    if len(tupless) > 0:
        requestLine = tupless[0]
        if check_requestLineRM(requestLine) is True:
            requestVar = requestLine.split("/")
            method = requestVar[0]
            version = requestVar[1] + '/' + requestVar[2]

            if tupless[len(tupless) - 1] == '' and tupless[len(tupless) - 2] == '':
                del tupless[len(tupless) - 1]
                del tupless[len(tupless) - 1]
            elif tupless[len(tupless) - 1] == '':
                del tupless[len(tupless) - 1]

            if len(tupless) > 1:
                if check_headerLine(tupless[1]) is True:
                    splitHeader = tupless[1].split(":")
                    if check_HeaderStarter(splitHeader[0]) is False:
                        return HttpRequestState.INVALID_INPUT
                else:
                    return HttpRequestState.INVALID_INPUT
                if len(tupless) >= 2:
                    for i in range(2, len(tupless)):
                        if check_headerLine(tupless[i]) is False:
                            return HttpRequestState.INVALID_INPUT
            else:
                return HttpRequestState.INVALID_INPUT

            if check_method(method) == 4:
                return HttpRequestState.NOT_SUPPORTED
            elif check_method(method) == 5:
                return HttpRequestState.INVALID_INPUT

            getPort = tupless[1].split(":")

            if len(getPort) == 3:
                if '/' in getPort[2]:
                    position = getPort[2].find('/')
                    port = getPort[2][:position]
                else:
                    port = getPort[2]

        elif check_requestLineAM(requestLine) is True:
            requestVar = requestLine.split(" ")
            method = requestVar[0]
            version = requestVar[2]

            if tupless[len(tupless) - 1] == '' and tupless[len(tupless) - 2] == '':
                del tupless[len(tupless) - 1]
                del tupless[len(tupless) - 1]
            elif tupless[len(tupless) - 1] == '':
                del tupless[len(tupless) - 1]

            if len(tupless) > 2:
                for i in range(2, len(tupless)):
                    if check_headerLine(tupless[i]) is False:
                        return HttpRequestState.INVALID_INPUT
            elif len(tupless) == 2:
                if check_headerLine(tupless[1]) is False:
                    return HttpRequestState.INVALID_INPUT

            if check_method(method) == 4:
                return HttpRequestState.NOT_SUPPORTED
            elif check_method(method) == 5:
                return HttpRequestState.INVALID_INPUT

            getPort = tupless[0].split(":")

            if len(getPort) == 3:
                if '/' in getPort[1]:
                    position = getPort[1].find('/')
                    port = getPort[1][:position]
                else:
                    port = getPort[1]

        else:
            return HttpRequestState.INVALID_INPUT

        return HttpRequestState.GOOD
    else:
        return HttpRequestState.INVALID_INPUT

    print("*" * 50)
    print("[check_http_request_validity] Implement me!")
    print("*" * 50)

    # return HttpRequestState.PLACEHOLDER


def sanitize_http_request(request_info: HttpRequestInfo):
    """
    Puts an HTTP request on the sanitized (standard) form
    by modifying the input request_info object.
    for example, expand a full URL to relative path + Host header.
    returns:
    nothing, but modifies the input object
    """

    if len(request_info.headers) > 0:
        if request_info.headers[0][1] != request_info.requested_host:
            hostHeader = ["Host", request_info.requested_host]
            request_info.headers.insert(0, hostHeader)
    else:
        hostHeader = ["Host", request_info.requested_host]
        request_info.headers.insert(0, hostHeader)

    print("*" * 50)
    print("[sanitize_http_request] Implement me!")
    print("*" * 50)


#######################################
# Leave the code below as is.
#######################################


def get_arg(param_index, default=None):
    """
        Gets a command line argument by index (note: index starts from 1)
        If the argument is not supplies, it tries to use a default value.
        If a default value isn't supplied, an error message is printed
        and terminates the program.
    """
    try:
        return sys.argv[param_index]
    except IndexError as e:
        if default:
            return default
        else:
            print(e)
            print(
                f"[FATAL] The comand-line argument #[{param_index}] is missing")
            exit(-1)  # Program execution failed.


def check_file_name():
    """
    Checks if this file has a valid name for *submission*
    leave this function and as and don't use it. it's just
    to notify you if you're submitting a file with a correct
    name.
    """
    script_name = os.path.basename(__file__)
    import re
    matches = re.findall(r"(\d{4}_){,2}lab2\.py", script_name)
    if not matches:
        print(f"[WARN] File name is invalid [{script_name}]")
    else:
        print(f"[LOG] File name is correct.")


def main():
    """
    Please leave the code in this function as is.
    To add code that uses sockets, feel free to add functions
    above main and outside the classes."""

    print("\n\n")
    print("*" * 50)
    print(f"[LOG] Printing command line arguments [{', '.join(sys.argv)}]")
    check_file_name()
    print("*" * 50)
    proxy_port_number = get_arg(1, 18888)
    entry_point(proxy_port_number)


if __name__ == "__main__":
    main()
