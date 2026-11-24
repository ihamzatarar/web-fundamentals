# Tiny static server for the CRP demo.
# Any file can be slowed down on purpose: /css/index2.css?delay=5000 waits 5 s before answering.
# Caching is disabled so every reload shows a real first load.
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8000


class DelayHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        delay_ms = int(query.get("delay", ["0"])[0])
        if delay_ms:
            time.sleep(delay_ms / 1000)
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


# Threading matters: without it one slow file would hold up every other download.
print(f"CRP demo running on http://localhost:{PORT}")
ThreadingHTTPServer(("", PORT), DelayHandler).serve_forever()
