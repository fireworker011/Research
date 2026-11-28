"""The span queue builds a prompt and refuses to replace an existing file."""

from __future__ import annotations

import json
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from h3.live_remake import RemakeError, build_remake_plan
from h3.span_queue import (
    build_ref2va_prompt,
    finished_history,
    history_video,
    mux_source_audio_argv,
    output_paths,
    post_prompt,
    select_span,
    video_vae_name,
)


def _plan() -> dict:
    sheet = {
        "schema": "h3-live-remake/v1",
        "source": {
            "path": "/content/drive/MyDrive/動画倉庫/ネタBOX/source.mp4",
            "duration_s": 7.375,
            "width": 1920,
            "height": 1080,
            "fps": 24.0,
            "has_audio": True,
        },
        "audio": "source",
        "max_span_s": 8.0,
        "cast": {
            "S1": {"stills": {"default": "/stills/a.jpg"}},
            "S2": {"stills": {"default": "/stills/b.jpg"}},
        },
        "place_still": "/stills/place.jpg",
        "props": {},
        "spans": [
            {
                "index": 1,
                "start_s": 0.0,
                "end_s": 7.375,
                "shots": 1,
                "split_inside_shot": False,
                "cast": {"S1": "default", "S2": "default"},
                "place": True,
                "props": [],
                "description": "[Shot 1] The two people hold still and the camera stays wide.",
                "soundscape": "",
                "music": "N/A",
            }
        ],
    }
    return build_remake_plan(sheet)


class QueueTests(unittest.TestCase):
    def test_span_01_prompt_is_20_steps_without_a_lora(self) -> None:
        plan = _plan()
        span = select_span(plan, 1)
        self.assertEqual(span["length"], 192)
        self.assertEqual(span["frames"], 177)
        prompt = build_ref2va_prompt(
            plan,
            span,
            image_files=["IMG_1251.JPG", "IMG_1250.JPG", "1024-cairo-night-road-v2.jpg"],
            video_file="span-01-ref.mp4",
            video_vae="minimax_h3_video_vae_int8_convrot.safetensors",
            seed=1024,
        )
        kinds = [item["class_type"] for item in prompt.values()]
        self.assertNotIn("LoraLoaderModelOnly", kinds)
        self.assertEqual(prompt["6"]["inputs"]["steps"], 20)
        self.assertEqual(prompt["6"]["inputs"]["scheduler"], "simple")
        self.assertEqual(prompt["5"]["inputs"]["sampler_name"], "res_multistep")
        self.assertEqual(prompt["8"]["inputs"]["length"], 192)
        self.assertEqual(prompt["8"]["inputs"]["width"], 1344)
        self.assertEqual(prompt["8"]["inputs"]["height"], 768)
        self.assertEqual(prompt["8"]["inputs"]["ref_images.ref_image_0"], ["20", 0])
        self.assertEqual(prompt["8"]["inputs"]["ref_images.ref_image_2"][0], "22")
        self.assertEqual(prompt["12"]["inputs"]["file"], "span-01-ref.mp4")
        self.assertEqual(prompt["4"]["inputs"]["unet_name"], "minimax_h3_ref2va_pruned_int8_convrot.safetensors")
        self.assertLess(prompt["8"]["inputs"]["prompt"].index("<Picture 1>"), prompt["8"]["inputs"]["prompt"].index("<Video 1>"))

    def test_existing_output_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "span-01.mp4"
            target.write_bytes(b"keep")
            with self.assertRaises(RemakeError):
                output_paths(tmp, 1)
            self.assertEqual(target.read_bytes(), b"keep")

    def test_fp16_vae_is_used_only_when_int8_is_absent(self) -> None:
        plan = {"model": {"video_vae": "minimax_h3_video_vae_int8_convrot.safetensors"}}
        self.assertEqual(
            video_vae_name(plan, ["minimax_h3_video_vae_fp16.safetensors"]),
            "minimax_h3_video_vae_fp16.safetensors",
        )
        self.assertEqual(
            video_vae_name(plan, ["minimax_h3_video_vae_int8_convrot.safetensors", "minimax_h3_video_vae_fp16.safetensors"]),
            "minimax_h3_video_vae_int8_convrot.safetensors",
        )

    def test_mux_takes_source_audio_for_the_measured_span(self) -> None:
        argv = mux_source_audio_argv("span-01.mp4", "/drive/1024.mp4", 0.0, 177, "span-01_with-audio.mp4")
        self.assertLess(argv.index("-ss"), argv.index("/drive/1024.mp4"))
        self.assertIn("trim=end_frame=177", "".join(argv))
        self.assertEqual(argv[-1], "span-01_with-audio.mp4")

    def test_post_prompt_returns_an_id_and_does_not_invent_one(self) -> None:
        seen: dict[str, object] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                seen["body"] = json.loads(self.rfile.read(length))
                raw = json.dumps({"prompt_id": "abc"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, fmt: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address[:2]
            prompt_id = post_prompt(f"http://{host}:{port}", {"1": {"class_type": "SaveVideo", "inputs": {}}})
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(prompt_id, "abc")
        self.assertEqual(seen["body"]["prompt"]["1"]["class_type"], "SaveVideo")

    def test_unfinished_history_waits_and_an_error_stops(self) -> None:
        self.assertIsNone(finished_history({}, "abc"))
        done = finished_history({"abc": {"status": {"completed": True, "status_str": "success"}, "outputs": {}}}, "abc")
        self.assertIsNotNone(done)
        with self.assertRaises(RemakeError):
            finished_history({"abc": {"status": {"status_str": "error"}}}, "abc")

    def test_history_finds_the_mp4(self) -> None:
        name = history_video({"outputs": {"19": {"videos": [{"filename": "span-01_00001_.mp4"}]}}})
        self.assertEqual(name, "span-01_00001_.mp4")


if __name__ == "__main__":
    unittest.main()
