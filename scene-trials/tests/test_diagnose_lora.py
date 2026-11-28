from __future__ import annotations

import base64
import contextlib
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import diagnose_lora  # noqa: E402

PROMPT = "1girl, <lora:nieva_xl:0.8>, <lora:ghost_xl:0.5>"


def _server(listed: list[dict[str, object]], honest: bool):
    state = {"calls": []}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.reply(listed)

        def do_POST(self) -> None:  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["calls"].append(body["prompt"])
            has_tag = "<lora:" in body["prompt"]
            picture = base64.b64encode(b"with" if has_tag and honest else b"plain").decode()
            hashes = ', Lora hashes: "nieva_xl: ab12cd34"' if has_tag and honest else ""
            info = json.dumps({"infotexts": [f"x\nSteps: 4, Seed: 1{hashes}"]})
            self.reply({"images": [picture], "info": info})

        def reply(self, payload: object) -> None:
            data = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, state


def _run(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = diagnose_lora.main(list(args))
    return code, out.getvalue()


class DiagnoseTests(unittest.TestCase):
    @staticmethod
    def _stop(server: HTTPServer) -> None:
        server.shutdown()
        server.server_close()

    def test_pure_helpers(self) -> None:
        self.assertEqual(diagnose_lora.tag_names("<lora:a:1>, <LYCO:b>, <lora:a:2>"), ["a", "b"])
        info = json.dumps({"infotexts": ['Steps: 4, Lora hashes: "a: 1, b: 2", V: x']})
        self.assertEqual(diagnose_lora.applied_in(info), {"a", "b"})
        self.assertEqual(diagnose_lora.applied_in(json.dumps({"infotexts": ["Steps: 4"]})), set())
        self.assertIsNone(diagnose_lora.applied_in("not json"))

    def test_a_name_the_webui_lacks_is_reported_with_a_hint(self) -> None:
        server, _state = _server([{"name": "nieva_xl"}, {"name": "ghost_xl_v2"}], honest=True)
        self.addCleanup(self._stop, server)
        code, text = _run(f"http://127.0.0.1:{server.server_port}", "--prompt", PROMPT)
        self.assertEqual(code, 1)
        self.assertIn("ok       nieva_xl", text)
        self.assertIn("MISSING  ghost_xl", text)
        self.assertIn("ghost_xl_v2", text)

    def test_everything_known_and_applied_is_ok(self) -> None:
        server, state = _server([{"name": "nieva_xl"}], honest=True)
        self.addCleanup(self._stop, server)
        code, text = _run(f"http://127.0.0.1:{server.server_port}", "--prompt", "1girl, <lora:nieva_xl:0.8>", "--generate")
        self.assertEqual(code, 0, text)
        self.assertIn("applied by the WebUI: ['nieva_xl']", text)
        self.assertIn("differs from the one without", text)
        self.assertEqual(len(state["calls"]), 2)
        self.assertNotIn("<lora:", state["calls"][1])

    def test_a_webui_that_ignores_the_tags_is_caught(self) -> None:
        server, _state = _server([{"name": "nieva_xl"}], honest=False)
        self.addCleanup(self._stop, server)
        code, text = _run(f"http://127.0.0.1:{server.server_port}", "--prompt", "1girl, <lora:nieva_xl:0.8>", "--generate")
        self.assertEqual(code, 1)
        self.assertIn("NOT APPLIED: ['nieva_xl']", text)
        self.assertIn("IDENTICAL", text)

    def test_jobs_file_is_read(self) -> None:
        server, _state = _server([{"name": "nieva_xl"}], honest=True)
        self.addCleanup(self._stop, server)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.json"
            path.write_text(json.dumps({"jobs": [{"id": "a", "prompt": "<lora:nieva_xl:1>"}]}), encoding="utf-8")
            code, text = _run(f"http://127.0.0.1:{server.server_port}", "--jobs", str(path))
        self.assertEqual(code, 0)
        self.assertIn("ok       nieva_xl", text)


if __name__ == "__main__":
    unittest.main()
