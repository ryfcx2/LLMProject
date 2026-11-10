"""Small standard-library web server for the Snowman game."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import secrets
from threading import Lock

from snowman import SnowmanGame

ROOT = Path(__file__).resolve().parent
GAMES = {}
GAMES_LOCK = Lock()
STATIC = {
    "/": ("snowman.html", "text/html; charset=utf-8"),
    "/snowman.css": ("snowman.css", "text/css; charset=utf-8"),
    "/snowman.js": ("snowman.js", "text/javascript; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in STATIC:
            return self.respond(404, {"error": "Not found."})
        filename, content_type = STATIC[self.path]
        content = (ROOT / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path not in ("/api/new", "/api/guess", "/api/hint", "/api/bonus"):
            return self.respond(404, {"error": "Not found."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096:
                return self.respond(413, {"error": "Request too large."})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Invalid request.")
            with GAMES_LOCK:
                if self.path == "/api/new":
                    game = SnowmanGame(payload.get("level"))
                    token = secrets.token_urlsafe(24)
                    GAMES[token] = game
                    return self.respond(200, {"token": token, "game": game.state()})
                token = payload.get("token")
                game = GAMES.get(token)
                if game is None:
                    return self.respond(404, {"error": "Game not found. Start a new game."})
                if self.path == "/api/guess":
                    state = game.guess(payload.get("guess", ""))
                elif self.path == "/api/hint":
                    state = game.hint()
                else:
                    if not isinstance(payload.get("play"), bool):
                        raise ValueError("Choose whether to play the bonus round.")
                    state = game.start_bonus(payload["play"])
                return self.respond(200, {"game": state})
        except (ValueError, TypeError) as error:
            return self.respond(400, {"error": str(error)})

    def respond(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Snowman is ready at http://localhost:{port}")
    server.serve_forever()
