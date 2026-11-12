import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from transmitly import Transmitly, TransmitlyError


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/v1/health":
            self._send(200, {"status": "ok"})
        elif self.path.startswith("/v1/messages"):
            self._send(200, {"messages": [], "total": 0, "path": self.path})
        else:
            self._send(404, {"error": {"code": "not_found", "message": "missing"}})

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/v1/emails":
            if self.headers.get("Authorization") != "Bearer txk_test":
                self._send(403, {"error": {"code": "insufficient_scope", "message": "admin required"}})
                return
            self._send(202, {"id": "msg_1", "status": "accepted", "recipients": 1, "body": body})
        else:
            self._send(404, {"error": {"code": "not_found", "message": "missing"}})

    def _send(self, status, payload):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class SDKTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_send_and_health(self):
        tx = Transmitly("txk_test", base_url=self.base)
        out = tx.send_email(from_="a@example.com", to="b@example.net", subject="Hi", text="hello")
        self.assertEqual(out["id"], "msg_1")
        self.assertEqual(out["body"]["text"], "hello")
        self.assertEqual(tx.health()["status"], "ok")

    def test_error(self):
        tx = Transmitly("bad", base_url=self.base)
        with self.assertRaises(TransmitlyError) as ctx:
            tx.send_email(from_="a@example.com", to="b@example.net", subject="Hi", text="hello")
        self.assertEqual(ctx.exception.status, 403)
        self.assertEqual(ctx.exception.code, "insufficient_scope")

    def test_query(self):
        tx = Transmitly("txk_test", base_url=self.base)
        out = tx.list_messages(status="bounced", limit=2)
        self.assertIn("status=bounced", out["path"])


if __name__ == "__main__":
    unittest.main()
