import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

class RssRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/rss+xml; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        rss = '<?xml version="1.0" encoding="UTF-8"?><xml></xml>'.encode('utf8')

        if self.path.startswith("/bpi"):
            rss_file_path = os.path.join('feeds', 'bpi_feed.xml')
        elif self.path.startswith("/gnius"):
            rss_file_path = os.path.join('feeds', 'gnius_feed.xml')
        else:
            self.send_response(404)
            self.end_headers()
            return

        try:
            with open(rss_file_path, 'rb') as file:
                rss = file.read()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            return

        self.wfile.write(rss)

    def do_HEAD(self):
        self._set_headers()


def main(server_class=HTTPServer, handler_class=RssRequestHandler, addr="localhost", port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main(port=int(sys.argv[1]))
