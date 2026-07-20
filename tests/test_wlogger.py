from __future__ import annotations

import io
import json
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import wlogger
from wlogger.formatter import ColorFormatter, JsonFormatter


class _FakeStream(io.StringIO):
    """io.StringIO with a controllable isatty(), like a real terminal/pipe."""

    def __init__(self, isatty: bool) -> None:
        super().__init__()
        self._isatty = isatty

    def isatty(self) -> bool:
        return self._isatty


class SetupTests(unittest.TestCase):
    def tearDown(self) -> None:
        root = logging.getLogger()
        for handler in root.handlers:
            handler.close()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_invalid_level_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            wlogger.setup(level="BOGUS")

    def test_console_handler_defaults_to_stderr(self) -> None:
        wlogger.setup(level="INFO")
        root = logging.getLogger()
        handler = next(h for h in root.handlers if isinstance(h, logging.StreamHandler))
        self.assertIs(handler.stream, __import__("sys").stderr)

    def test_console_stream_override_is_used(self) -> None:
        stream = _FakeStream(isatty=False)
        wlogger.setup(level="DEBUG", console_stream=stream)

        logger = wlogger.get_logger("test.override")
        logger.info("hello")

        self.assertIn("hello", stream.getvalue())
        self.assertIn("[INFO", stream.getvalue())

    def test_color_disabled_for_non_tty_stream(self) -> None:
        stream = _FakeStream(isatty=False)
        wlogger.setup(level="INFO", console_stream=stream)

        wlogger.get_logger("test.color").warning("careful")

        self.assertNotIn("\033[", stream.getvalue())

    def test_color_enabled_for_tty_stream(self) -> None:
        stream = _FakeStream(isatty=True)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NO_COLOR", None)
            wlogger.setup(level="INFO", console_stream=stream)
            wlogger.get_logger("test.color.tty").warning("careful")

        self.assertIn("\033[", stream.getvalue())

    def test_no_color_env_var_disables_color_even_on_tty(self) -> None:
        stream = _FakeStream(isatty=True)
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            wlogger.setup(level="INFO", console_stream=stream)
            wlogger.get_logger("test.no_color").warning("careful")

        self.assertNotIn("\033[", stream.getvalue())

    def test_file_handler_writes_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "app.log")
            wlogger.setup(level="INFO", log_file=str(log_path))
            wlogger.get_logger("test.file").info("stored", extra={"request_id": "abc"})

            line = log_path.read_text(encoding="utf-8").strip().splitlines()[-1]
            payload = json.loads(line)

        self.assertEqual(payload["message"], "stored")
        self.assertEqual(payload["request_id"], "abc")

    def test_get_logger_returns_stdlib_logger(self) -> None:
        logger = wlogger.get_logger("test.named")
        self.assertIs(logger, logging.getLogger("test.named"))

    def test_reconfiguring_closes_previous_file_handler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "app.log")
            wlogger.setup(level="INFO", log_file=str(log_path))
            root = logging.getLogger()
            first_handler = next(
                h for h in root.handlers if isinstance(h, logging.FileHandler)
            )

            wlogger.setup(level="INFO", log_file=str(log_path))

            self.assertIsNone(first_handler.stream)


class ColorFormatterTests(unittest.TestCase):
    def _record(self, level: int = logging.DEBUG) -> logging.LogRecord:
        return logging.LogRecord("myapp", level, __file__, 1, "hello", None, None)

    def test_level_names_are_padded_for_alignment(self) -> None:
        formatter = ColorFormatter(use_color=False)
        info_line = formatter.format(self._record(logging.INFO))
        critical_line = formatter.format(self._record(logging.CRITICAL))

        self.assertIn("[INFO    ]", info_line)
        self.assertIn("[CRITICAL]", critical_line)

    def test_use_color_false_emits_no_ansi_codes(self) -> None:
        formatter = ColorFormatter(use_color=False)
        line = formatter.format(self._record())
        self.assertNotIn("\033[", line)

    def test_use_color_true_emits_ansi_codes(self) -> None:
        formatter = ColorFormatter(use_color=True)
        line = formatter.format(self._record())
        self.assertIn("\033[", line)


class JsonFormatterTests(unittest.TestCase):
    def test_standard_attrs_are_not_leaked_as_extra_fields(self) -> None:
        record = logging.LogRecord("myapp", logging.INFO, __file__, 1, "hello", None, None)
        payload = json.loads(JsonFormatter().format(record))

        # taskName (added to LogRecord in Python 3.12) and other stdlib
        # attributes must not show up as noise in every log line.
        for noisy_key in ("taskName", "msg", "args", "levelno", "pathname"):
            self.assertNotIn(noisy_key, payload)

    def test_extra_fields_are_preserved(self) -> None:
        record = logging.LogRecord("myapp", logging.INFO, __file__, 1, "hello", None, None)
        record.request_id = "abc-123"
        payload = json.loads(JsonFormatter().format(record))

        self.assertEqual(payload["request_id"], "abc-123")


if __name__ == "__main__":
    unittest.main()
