"""Local checks. These tests do not call YouTube or TikTok."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import StringIO
from pathlib import Path

import auth_youtube
import fetch_stats
import posting_lib as lib
import upload_tiktok
import upload_youtube

ROOT = Path(__file__).resolve().parent


class RulesTest(unittest.TestCase):
    def test_channels_cover_the_requested_accounts(self) -> None:
        rows = lib.load_channels(ROOT / "channels.json")
        youtube = [row["key"] for row in rows if row["platform"] == "youtube"]
        tiktok = [row["key"] for row in rows if row["platform"] == "tiktok"]
        self.assertEqual(
            youtube,
            [
                "pet_story_select",
                "yoru_neko_camera",
                "sonae_30",
                "yoru_no_tana",
                "nemuri_no_tana",
                "pet_kurasu_monogatari",
                "fireworker012_reserved",
            ],
        )
        self.assertEqual(
            tiktok,
            [
                "yoru_no_tana",
                "uchi_no_fukuro",
                "pet_chiisana_monogatari",
                "yua",
                "moto_konkatsu_miki",
                "kane_memo",
            ],
        )
        yoru = next(row for row in rows if row["platform"] == "youtube" and row["key"] == "yoru_no_tana")
        self.assertEqual(yoru["login_label"], "")
        self.assertEqual(yoru["status"], "hold")
        self.assertNotIn("client_secret_dir", yoru)
        dirs = {
            "pet_story_select": "C:/Users/hp/Downloads/youtube/fireworker01",
            "yoru_neko_camera": "C:/Users/hp/Downloads/youtube/fireworker06",
            "sonae_30": "C:/Users/hp/Downloads/youtube/fireworker04",
            "nemuri_no_tana": "C:/Users/hp/Downloads/youtube/fireworker011",
            "pet_kurasu_monogatari": "C:/Users/hp/Downloads/youtube/naomichi235",
            "fireworker012_reserved": "C:/Users/hp/Downloads/youtube/fireworker012",
        }
        for key, folder in dirs.items():
            row = next(item for item in rows if item["platform"] == "youtube" and item["key"] == key)
            self.assertEqual(row["client_secret_dir"], folder)
        reserved = next(
            row for row in rows if row["platform"] == "youtube" and row["key"] == "fireworker012_reserved"
        )
        self.assertEqual(reserved["status"], "reserved")
        self.assertEqual(reserved["title"], "")
        pet = next(row for row in rows if row["platform"] == "youtube" and row["key"] == "pet_kurasu_monogatari")
        self.assertEqual(pet["title"], "ペットと暮らす小さな物語")
        self.assertEqual(pet["login_label"], "naomichi235")
        yua = next(row for row in rows if row["platform"] == "tiktok" and row["key"] == "yua")
        self.assertEqual(yua["login_label"], "fireworker012")

    def test_disclosure_and_affiliate_url(self) -> None:
        lib.assert_disclosure(f"本文。{lib.A8_DISCLOSURE}", True)
        with self.assertRaises(lib.ValidationError):
            lib.assert_disclosure("開示なし", True)
        lib.assert_disclosure("開示なし", False)
        with self.assertRaises(lib.ValidationError):
            lib.assert_no_affiliate_url("https://px.a8.net/svt/ejp")

    def test_youtube_limits(self) -> None:
        lib.assert_youtube_text("a" * 100, "b" * 5000)
        with self.assertRaises(lib.ValidationError):
            lib.assert_youtube_text("a" * 101, "ok")
        with self.assertRaises(lib.ValidationError):
            lib.assert_youtube_text("ok", "b" * 5001)
        with self.assertRaises(lib.ValidationError):
            lib.assert_youtube_text("a<b", "ok")

    def test_schedule_becomes_private_until_publish_at(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        privacy, publish_at, note = lib.youtube_status("public", future)
        self.assertEqual(privacy, "private")
        self.assertTrue(publish_at.endswith("Z"))
        self.assertIn("公開", note)
        with self.assertRaises(lib.ValidationError):
            lib.youtube_status("unlisted", future)
        with self.assertRaises(lib.ValidationError):
            lib.youtube_status("private", "2020-01-01T00:00:00Z")
        with self.assertRaises(lib.ValidationError):
            lib.youtube_status("private", "2026-10-22T21:00:00")

    def test_youtube_body_marks_paid_placement_for_a8(self) -> None:
        body, part = lib.build_youtube_body(
            title="t",
            description=lib.A8_DISCLOSURE,
            category_id="22",
            language="ja",
            privacy_status="private",
            publish_at="2026-10-22T12:00:00Z",
            made_for_kids=False,
            synthetic=True,
            a8=True,
        )
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertEqual(body["status"]["publishAt"], "2026-10-22T12:00:00Z")
        self.assertIs(body["status"]["selfDeclaredMadeForKids"], False)
        self.assertIs(body["status"]["containsSyntheticMedia"], True)
        self.assertIs(body["paidProductPlacementDetails"]["hasPaidProductPlacement"], True)
        self.assertIn("paidProductPlacementDetails", part)
        plain, plain_part = lib.build_youtube_body(
            title="t",
            description="d",
            category_id="15",
            language="ja",
            privacy_status="public",
            publish_at=None,
            made_for_kids=False,
            synthetic=False,
            a8=False,
        )
        self.assertNotIn("paidProductPlacementDetails", plain)
        self.assertNotIn("paidProductPlacementDetails", plain_part)

    def test_tiktok_chunks_follow_the_published_rules(self) -> None:
        chunk, count, slices = lib.tiktok_chunk_plan(50_000_123)
        self.assertEqual((chunk, count, slices), (50_000_123, 1, [(0, 50_000_123)]))
        chunk, count, slices = lib.tiktok_chunk_plan(4_194_304)
        self.assertEqual(count, 1)
        self.assertEqual(slices, [(0, 4_194_304)])
        chunk, count, slices = lib.tiktok_chunk_plan(100_000_100)
        self.assertEqual(chunk, 10_000_000)
        self.assertEqual(count, 10)
        self.assertEqual(sum(end - start for start, end in slices), 100_000_100)
        self.assertEqual(slices[-1], (90_000_000, 100_000_100))
        self.assertLessEqual(slices[-1][1] - slices[-1][0], 128_000_000)
        chunk, count, slices = lib.tiktok_chunk_plan(64_000_001)
        self.assertGreaterEqual(count, 2)
        self.assertEqual(sum(end - start for start, end in slices), 64_000_001)
        self.assertTrue(all(end - start >= 5_000_000 for start, end in slices[:-1]))
        with self.assertRaises(lib.ValidationError):
            lib.tiktok_chunk_plan(0)

    def test_names_ignore_at_and_case(self) -> None:
        self.assertTrue(lib.names_match("よるの棚", "夜の棚", "別タイトル", "@夜の棚"))
        self.assertTrue(lib.names_match("pet_story_select", "", "別", "@Pet_Story_Select"))
        self.assertFalse(lib.names_match("ねむりの棚", "", "別のチャンネル", ""))

    def test_errors_drop_query_secrets(self) -> None:
        message = lib.public_api_error(
            "https://upload.example/video?upload_token=super-secret",
            400,
            b'{"error":"invalid_grant","refresh_token":"rft-secret"}',
        )
        self.assertNotIn("super-secret", message)
        self.assertNotIn("upload_token", message)
        self.assertNotIn("rft-secret", message)
        self.assertIn("invalid_grant", message)

    def test_find_client_secret_accepts_parenthesized_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            secret = folder / "client_secret_123(1).json"
            secret.write_text("{}", encoding="utf-8")
            self.assertEqual(lib.find_client_secret(folder), secret)

    def test_find_client_secret_rejects_zero_or_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with self.assertRaises(lib.ValidationError) as empty:
                lib.find_client_secret(folder)
            self.assertIn("該当: なし", str(empty.exception))
            (folder / "client_secret_a.json").write_text("{}", encoding="utf-8")
            (folder / "client_secret_b.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(lib.ValidationError) as both:
                lib.find_client_secret(folder)
            message = str(both.exception)
            self.assertIn("client_secret_a.json", message)
            self.assertIn("client_secret_b.json", message)

    def test_hold_and_reserved_channels_refuse_credentials(self) -> None:
        hold = {"key": "yoru_no_tana", "title": "よるの棚", "status": "hold"}
        with self.assertRaises(lib.ValidationError) as held:
            lib.google_credentials(ROOT, "yoru_no_tana", "", channel=hold)
        self.assertIn("アカウント未定のため保留", str(held.exception))
        reserved = {"key": "fireworker012_reserved", "title": "", "status": "reserved"}
        with self.assertRaises(lib.ValidationError) as waiting:
            lib.resolve_youtube_client(ROOT, reserved)
        self.assertIn("チャンネル名が未定", str(waiting.exception))

    def test_token_defaults_beside_client_secret_outside_the_repo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            secret = folder / "client_secret_abc(1).json"
            secret.write_text(
                json.dumps({"installed": {"client_id": "cid", "client_secret": "sec"}}),
                encoding="utf-8",
            )
            token = folder / "token.json"
            token.write_text(json.dumps({"refresh_token": "rft"}), encoding="utf-8")
            channel = {
                "key": "pet_story_select",
                "title": "pet_story_select",
                "status": "active",
                "client_secret_dir": str(folder),
            }
            creds = lib.google_credentials(ROOT, "pet_story_select", "", channel=channel)
            self.assertEqual(creds["client_path"], secret)
            self.assertEqual(creds["token_path"], token)
            self.assertEqual(creds["client_id"], "cid")
            self.assertEqual(creds["refresh_token"], "rft")
            self.assertEqual(
                lib.default_youtube_token_path(ROOT, "pet_story_select", secret),
                token,
            )
        inside = ROOT / "not-a-secret" / "client_secret_example.json"
        self.assertEqual(
            lib.default_youtube_token_path(ROOT, "pet_story_select", inside),
            ROOT / "tokens" / "youtube" / "pet_story_select.json",
        )

    def test_auth_hold_channel_stops_before_the_browser(self) -> None:
        buffer = StringIO()
        with redirect_stderr(buffer):
            code = auth_youtube.main(["--channel", "yoru_no_tana", "--no-browser"])
        self.assertEqual(code, 2)
        self.assertIn("アカウント未定のため保留", buffer.getvalue())
        with redirect_stderr(buffer):
            reserved = auth_youtube.main(["--channel", "fireworker012_reserved", "--no-browser"])
        self.assertEqual(reserved, 2)
        self.assertIn("チャンネル名が未定", buffer.getvalue())

    def test_google_download_shape(self) -> None:
        client_id, secret = lib.google_client_fields(
            {"installed": {"client_id": "id.apps.googleusercontent.com", "client_secret": "sec"}}
        )
        self.assertEqual(client_id, "id.apps.googleusercontent.com")
        self.assertEqual(secret, "sec")

    def test_processing_status_blocks_a_second_send(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "posted.csv"
            lib.append_csv(
                path,
                lib.POSTED_COLUMNS,
                {
                    "platform": "tiktok",
                    "channel_key": "kane_memo",
                    "file_sha256": "abc",
                    "status": "PROCESSING_UPLOAD",
                },
            )
            self.assertTrue(lib.already_posted(path, "tiktok", "kane_memo", "abc"))
            self.assertFalse(lib.already_posted(path, "tiktok", "kane_memo", "other"))

    def test_csv_headers_match_the_writers(self) -> None:
        posted = (ROOT / "posted.csv.example").read_text(encoding="utf-8").strip()
        stats = (ROOT / "stats.csv.example").read_text(encoding="utf-8").strip()
        self.assertEqual(posted, ",".join(lib.POSTED_COLUMNS))
        self.assertEqual(stats, ",".join(lib.STATS_COLUMNS))

    def test_gitignore_covers_secrets(self) -> None:
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for needle in ("secrets/", "tokens/", "posted.csv", "stats.csv", ".env", "client_secret", "token.json"):
            self.assertIn(needle, text)

    def test_resumable_put_accepts_308_without_following_it(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_PUT(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or "0")
                self.rfile.read(length)
                self.server.hits += 1  # type: ignore[attr-defined]
                self.server.saw_auth = "Authorization" in self.headers  # type: ignore[attr-defined]
                if self.server.hits == 1:  # type: ignore[attr-defined]
                    self.send_response(308)
                    self.send_header("Location", "http://127.0.0.1/should-not-follow?token=hidden")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                body = b'{"id":"abc12345abc"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        server.hits = 0  # type: ignore[attr-defined]
        server.saw_auth = False  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
                handle.write(b"1234567890")
                handle.flush()
                payload = lib.upload_chunks(
                    f"http://127.0.0.1:{server.server_address[1]}/upload?upload_token=hidden",
                    Path(handle.name),
                    [(0, 4), (4, 10)],
                    access_token="access-secret",
                    content_type="video/mp4",
                    done=frozenset({200, 201}),
                    continue_codes=frozenset({308}),
                )
            self.assertEqual(json.loads(payload)["id"], "abc12345abc")
            self.assertEqual(server.hits, 2)  # type: ignore[attr-defined]
            self.assertTrue(server.saw_auth)  # type: ignore[attr-defined]
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_tiktok_put_does_not_send_authorization(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_PUT(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or "0")
                self.rfile.read(length)
                self.server.saw_auth = "Authorization" in self.headers  # type: ignore[attr-defined]
                body = b""
                self.send_response(201)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        server.saw_auth = False  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
                handle.write(b"abcd")
                handle.flush()
                lib.tiktok_put(
                    f"http://127.0.0.1:{server.server_address[1]}/up?upload_token=hidden",
                    Path(handle.name),
                    [(0, 4)],
                )
            self.assertFalse(server.saw_auth)  # type: ignore[attr-defined]
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.keys = (
            "YOUTUBE_CLIENT_ID",
            "YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_REFRESH_TOKEN",
            "TIKTOK_CLIENT_KEY",
            "TIKTOK_CLIENT_SECRET",
            "TIKTOK_REFRESH_TOKEN",
            "CI",
            "GITHUB_ACTIONS",
        )
        self.saved = {key: os.environ.pop(key, None) for key in self.keys}
        self.posted = ROOT / "posted.csv"
        self.existed = self.posted.exists()

    def tearDown(self) -> None:
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if not self.existed and self.posted.exists():
            self.posted.unlink()

    def youtube_args(self, video: str, extra: list[str]) -> list[str]:
        return [
            "--channel",
            "pet_story_select",
            "--video",
            video,
            "--title",
            "ねこの朝",
            "--description",
            "窓の光。",
            "--privacy",
            "private",
            "--category-id",
            "15",
            "--not-made-for-kids",
            *extra,
        ]

    def test_youtube_dry_run_does_not_write_or_require_tokens(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
            handle.write(b"not-a-real-video")
            handle.flush()
            buffer = StringIO()
            with redirect_stdout(buffer):
                code = upload_youtube.main(self.youtube_args(handle.name, []))
        self.assertEqual(code, 0)
        self.assertIn("DRY-RUN", buffer.getvalue())
        self.assertNotIn("refresh", buffer.getvalue().casefold())
        self.assertFalse(self.posted.exists())

    def test_a8_without_disclosure_fails_before_publish(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
            handle.write(b"x")
            handle.flush()
            code = upload_youtube.main(self.youtube_args(handle.name, ["--a8"]))
        self.assertEqual(code, 2)

    def test_publish_without_credentials_does_not_call_network(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
            handle.write(b"x")
            handle.flush()
            code = upload_youtube.main(self.youtube_args(handle.name, ["--publish"]))
        self.assertEqual(code, 2)
        self.assertFalse(self.posted.exists())

    def test_ci_blocks_publish(self) -> None:
        os.environ["CI"] = "true"
        with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
            handle.write(b"x")
            handle.flush()
            buffer = StringIO()
            with redirect_stderr(buffer):
                code = upload_youtube.main(self.youtube_args(handle.name, ["--publish"]))
        self.assertEqual(code, 2)
        self.assertIn("GitHub Actions", buffer.getvalue())

    def test_tiktok_schedule_is_rejected(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with tempfile.NamedTemporaryFile(suffix=".mp4") as handle:
            handle.write(b"x")
            handle.flush()
            code = upload_tiktok.main(
                [
                    "--channel",
                    "kane_memo",
                    "--video",
                    handle.name,
                    "--title",
                    "メモ",
                    "--description",
                    lib.A8_DISCLOSURE,
                    "--privacy",
                    "private",
                    "--a8",
                    "--schedule",
                    future,
                ]
            )
        self.assertEqual(code, 2)

    def test_stats_dry_run_explains_missing_clicks(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            code = fetch_stats.main(
                ["--platform", "youtube", "--channel", "pet_story_select", "--video-id", "abc"]
            )
        self.assertEqual(code, 0)
        self.assertIn("DRY-RUN", buffer.getvalue())
        self.assertIn("クリック", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
