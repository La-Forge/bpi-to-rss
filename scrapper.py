


from scrappers.gnius import GniusScrapper
from scrappers.bpi import BpiScrapper
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

import sentry_sdk
sentry_sdk.init(
    "https://050cb1f4aff04d22af23721245c4ae35@o1031661.ingest.sentry.io/5998395",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)
division_by_zero = 1 / 0
class RssRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/rss+xml; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        rss = '<?xml version="1.0" encoding="UTF-8"?><xml></xml>'.encode('utf8')
        if(self.path=="/bpi"):
            rss = self.bpi_scrapper.generate_feed(verbose=False)
        elif(self.path=="/gnius"):
            rss = self.gnius_scrapper.generate_feed(verbose=False)

        self.wfile.write(rss)

    def do_HEAD(self):
        self._set_headers()


def main(server_class=HTTPServer, handler_class=RssRequestHandler, addr="localhost", port=8000):
    handler_class.bpi_scrapper = BpiScrapper()
    handler_class.gnius_scrapper = GniusScrapper()
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    
    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


    
if __name__ == "__main__":
    main(port=int(sys.argv[1]))
