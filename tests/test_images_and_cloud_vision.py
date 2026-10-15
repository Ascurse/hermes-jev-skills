"""Images for Jev (TypeSafe's "Dreamer-ready" preview) and the cloud half of the vision shadow.

* images.py refuses, before any request, every picture the API would refuse.
* client.ask sends assets and box questions to TypeSafe only, with the Danger Zone header,
  refuses an unreferenced asset, and validates a box answer like any other.
* `/jev vision_cloud shadow` is its own switch: the local shadow never sends a picture, and
  the cloud one logs ids, hashes and classes, never the picture, path or question.
"""
from __future__ import annotations

import base64
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_vision_shadow import QUESTION, Base  # noqa: E402

from jevkit import client, images  # noqa: E402


def png(width: int = 300, height: int = 300, animated: bool = False) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\x00" + b"\x00" * width for _ in range(height))
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
    if animated:
        out += chunk(b"acTL", struct.pack(">II", 2, 0))
    return out + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def jpeg(width: int = 400, height: int = 300, marker: int = 0xC0) -> bytes:
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = bytes([0xFF, marker]) + struct.pack(">HBHHB", 11, 8, height, width, 1) + b"\x01\x11\x00"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


class Images(unittest.TestCase):
    def test_headers_are_read(self):
        self.assertEqual(images.inspect(png(320, 280)), ("png", 320, 280))
        self.assertEqual(images.inspect(jpeg(400, 300)), ("jpeg", 400, 300))

    def test_what_the_api_would_refuse_is_refused_here(self):
        cases = {"unsupported_format": b"GIF89a" + b"\x00" * 40,
                 "animated_png": png(animated=True),
                 "progressive_jpeg": jpeg(marker=0xC2),
                 "side_out_of_range": png(200, 400),
                 "pixels_out_of_range": png(256, 300)}
        for code, data in cases.items():
            with self.assertRaises(images.ImageError) as caught:
                images.check(data)
            self.assertEqual(caught.exception.code, code)
        with mock.patch.object(images, "MAX_FILE_BYTES", 10):
            with self.assertRaises(images.ImageError):
                images.check(png())

    def test_an_asset_is_base64_with_a_uuid_reference(self):
        ref, item = images.asset(png())
        self.assertRegex(ref, r"^img-[0-9a-f-]{36}$")
        self.assertEqual(item["format"], "png")
        self.assertEqual(base64.b64decode(item["data_base64"]), png())


class Requests(unittest.TestCase):
    def setUp(self):
        self.sent = []

    def transport(self, answers):
        def send(body, headers, timeout):
            self.sent.append((json.loads(body), headers))
            return json.dumps({"model": "jev-1.14.0", "answers": answers, "usage": {"input_tokens": 900}}).encode()
        return send

    def test_assets_go_with_the_header(self):
        ref, item = images.asset(png())
        out = client.ask({"tile": ref}, {"ok": client.noul("Is `tile` clipped?")}, assets={ref: item},
                         api_key="k", provider="typesafe", transport=self.transport({"ok": {"type": "noul", "noul": 0.1}}))
        body, headers = self.sent[0]
        self.assertEqual(headers[images.DANGER_ZONE_HEADER], "true")
        self.assertEqual(body["assets"][ref]["format"], "png")
        self.assertEqual(out["answers"]["ok"]["noul"], 0.1)

    def test_text_only_requests_are_unchanged(self):
        client.ask("x", {"ok": client.noul("Is it fine?")}, api_key="k", provider="typesafe",
                   transport=self.transport({"ok": {"type": "noul", "noul": 0.5}}))
        body, headers = self.sent[0]
        self.assertNotIn("assets", body)
        self.assertNotIn(images.DANGER_ZONE_HEADER, headers)

    def test_an_unreferenced_asset_is_refused_before_sending(self):
        ref, item = images.asset(png())
        with self.assertRaises(ValueError):
            client.ask("no picture here", {"ok": client.noul("Is it fine?")}, assets={ref: item},
                       api_key="k", provider="typesafe", transport=self.transport({}))
        self.assertEqual(self.sent, [])

    def test_images_go_to_typesafe_only(self):
        ref, item = images.asset(png())
        for provider in ("openrouter", "venice", "zen"):
            with self.assertRaises(client.JevError) as caught:
                client.ask({"tile": ref}, {"ok": client.noul("Is `tile` clipped?")}, assets={ref: item},
                           api_key="k", provider=provider, transport=self.transport({}))
            self.assertEqual(caught.exception.code, "images_unsupported")
        self.assertEqual(self.sent, [])

    def test_a_box_is_read_and_checked(self):
        ref, item = images.asset(png())
        good = {"type": "box", "box": {"left": 0.1, "top": 0.2, "right": 0.4, "bottom": 0.5}, "confidence": 0.8}
        out = client.ask({"photo": ref}, {"where": client.box("the mug in `photo`")}, assets={ref: item},
                         api_key="k", provider="typesafe", transport=self.transport({"where": good}))
        self.assertEqual(out["answers"]["where"]["box"]["right"], 0.4)
        self.assertEqual(self.sent[0][1][images.DANGER_ZONE_HEADER], "true")
        flat = dict(good, box={"left": 0.5, "top": 0.2, "right": 0.4, "bottom": 0.5})
        with self.assertRaises(client.JevError) as caught:
            client.ask({"photo": ref}, {"where": client.box("the mug in `photo`")}, assets={ref: item},
                       api_key="k", provider="typesafe", transport=self.transport({"where": flat}))
        self.assertEqual(caught.exception.invariant, "box_has_area")

    def test_a_box_takes_no_criteria(self):
        with self.assertRaises(ValueError):
            client.check_question("where", {"type": "box", "instructions": "the mug", "criteria": {"a": "b"}})


class CloudShadow(Base):
    def setUp(self):
        super().setUp()
        self.image.write_bytes(png())
        self.asked = []

        def fake_ask(state, questions, **kwargs):
            self.asked.append((state, questions, kwargs))
            return {"answers": {"verdict": {"type": "choice", "choice": "No", "confidence": 0.88,
                                            "probabilities": {"Yes": 0.12, "No": 0.88}}},
                    "jev_model": "jev-1.14.0", "input_tokens": 1200}
        patcher = mock.patch.object(self.plugin.cloud_vision.client, "ask", fake_ask)
        patcher.start()
        self.addCleanup(patcher.stop)

    def cloud_rows(self):
        return [row for row in self.rows() if row.get("model") == "typesafe-jev"]

    def test_the_local_shadow_never_sends_a_picture(self):
        self.on()
        self.call()
        self.settle()
        self.assertEqual(self.asked, [])
        self.assertEqual(self.cloud_rows(), [])

    def test_off_by_default_and_the_kill_switch_wins(self):
        self.call()
        self.settle()
        self.plugin.switches.set_mode("vision_cloud", "shadow", shared=True)
        self.plugin.switches.kill_switch("vision_cloud").parent.mkdir(parents=True, exist_ok=True)
        self.plugin.switches.kill_switch("vision_cloud").touch()
        self.call()
        self.settle()
        self.assertEqual(self.asked, [])

    def test_cloud_shadow_asks_and_logs_no_content(self):
        self.plugin.switches.set_mode("vision_cloud", "shadow", shared=True)
        result = self.call()
        self.settle()
        self.assertIsNone(result)
        state, questions, kwargs = self.asked[0]
        self.assertEqual(kwargs["provider"], "typesafe")
        self.assertIn(state["image"], kwargs["assets"])
        self.assertEqual(set(questions["verdict"]["criteria"]), {"Yes", "No"})
        [row] = self.cloud_rows()
        self.assertEqual((row["status"], row["jev_class"], row["agree"]), ("ok", "No", True))
        self.assertEqual(row["input_tokens"], 1200)
        text = json.dumps(row)
        for leak in ("SECRETWORD", str(self.image), QUESTION):
            self.assertNotIn(leak, text)

    def test_unusable_pictures_and_regions_are_skipped(self):
        self.plugin.switches.set_mode("vision_cloud", "shadow", shared=True)
        self.image.write_bytes(png(100, 100))
        self.call()
        self.settle()
        self.assertEqual(self.cloud_rows()[-1]["reason"], "image_side_out_of_range")
        self.image.write_bytes(png())
        self.plugin._on_post_tool_call(
            tool_name="vision_analyze", args={"image_url": str(self.image), "question": QUESTION, "region": [0, 0, 9, 9]},
            session_id="s", status="ok", result="{}", tool_call_id="c", turn_id="t")
        self.settle()
        self.assertEqual(self.cloud_rows()[-1]["reason"], "region_unsupported")
        self.assertEqual(self.asked, [])

    def test_a_jev_error_is_logged_not_raised(self):
        self.plugin.switches.set_mode("vision_cloud", "shadow", shared=True)
        with mock.patch.object(self.plugin.cloud_vision.client, "ask", side_effect=self.plugin.cloud_vision.client.JevError("http_400")):
            self.call()
            self.settle()
        self.assertEqual((self.cloud_rows()[-1]["status"], self.cloud_rows()[-1]["error"]), ("error", "http_400"))


if __name__ == "__main__":
    unittest.main()
