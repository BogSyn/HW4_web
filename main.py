import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from pathlib import Path
import os
import mimetypes
import logging
from datetime import datetime
import socket
from threading import Thread

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000



class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        match pr_url.path:
            case '/':
                self.send_html_file('index.html')
            case '/message.html':
                self.send_html_file('message.html')
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static_file(file)
                else:
                    self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    def send_static_file(self, filename, status=200):
        self.send_response(status)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def do_POST(self):
        size = self.headers.get('Content-Length')
        post_data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # UDP socket
        client_socket.sendto(post_data, (SOCKET_HOST, SOCKET_PORT))         # Відправляємо на сервер дані
        client_socket.close()                                               # Закриваємо з'єднання
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


def save_data_from_form(post_data):
    if not os.path.exists('storage'):
        os.makedirs('storage')
    if not os.path.exists('storage/data.json'):
        with open('storage/data.json', 'w') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
    parse_data = urllib.parse.unquote_plus(post_data.decode())
    try:
        with open('storage/data.json', 'r', encoding='utf-8') as fr:
            try:
                json_dict = json.load(fr)
                logging.info(json_dict)
            except ValueError as err:
                logging.error(err)
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        json_dict[str(datetime.now())] = parse_dict
        logging.info(json_dict)
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(json_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # UDP socket
    server_socket.bind((host, port))                                    # Зв'язуємо сокет із адресою служби
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)          # Очікування відповіді від http сервера
            save_data_from_form(msg)                                    # Парсимо та зберігаємо в json
    except KeyboardInterrupt:
        server_socket.close()

def run_http(host, port):
    server_address = (host, port)
    http = HTTPServer(server_address, HttpHandler)
    logging.info("Starting http server")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    http_server = Thread(target=run_http, args=(HTTP_HOST, HTTP_PORT))
    http_server.start()

    socket_server = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_server.start()
