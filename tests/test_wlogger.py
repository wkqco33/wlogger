from __future__ import annotations

import io
import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TextIO, cast, override
from unittest.mock import patch

import wlogger
from wlogger import LogLevel
from wlogger.formatter import ColorFormatter, JsonFormatter


class _FakeStream(io.StringIO):
    """io.StringIO with a controllable isatty(), like a real terminal/pipe."""

    def __init__(self, isatty: bool) -> None:
        super().__init__()
        self._isatty: bool = isatty

    @override
    def isatty(self) -> bool:
        return self._isatty


def _json_payload(text: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads(text))


class SetupTests(unittest.TestCase):
    @override
    def tearDown(self) -> None:
        root = logging.getLogger()
        for handler in root.handlers:
            handler.close()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_invalid_level_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            wlogger.setup(level=cast(LogLevel, cast(object, "BOGUS")))

    def test_non_positive_max_bytes_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            wlogger.setup(level="INFO", log_file="app.log", max_bytes=0)

    def test_negative_backup_count_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            wlogger.setup(level="INFO", log_file="app.log", backup_count=-1)

    def test_console_handler_defaults_to_stderr(self) -> None:
        wlogger.setup(level="INFO")
        root = logging.getLogger()
        handlers = (
            cast(logging.StreamHandler[TextIO], h)
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
        )
        handler = next(h for h in handlers if h.stream is sys.stderr)
        self.assertIs(handler.stream, sys.stderr)

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
            _ = os.environ.pop("NO_COLOR", None)
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
            payload = _json_payload(line)

        self.assertEqual(payload["message"], "stored")
        self.assertEqual(payload["request_id"], "abc")

    def test_json_default_is_applied_to_file_extra_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "app.log")
            wlogger.setup(
                level="INFO",
                log_file=str(log_path),
                json_default=lambda value: f"<{value}>",
            )
            wlogger.get_logger("test.file.default").info(
                "stored", extra={"path": Path("app.log")}
            )

            line = log_path.read_text(encoding="utf-8").strip().splitlines()[-1]
            payload = _json_payload(line)

        self.assertEqual(payload["path"], "<app.log>")

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

    def test_setup_preserves_unrelated_root_handlers(self) -> None:
        stream = _FakeStream(isatty=False)
        unrelated_handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        root.addHandler(unrelated_handler)

        wlogger.setup(level="INFO", console_stream=_FakeStream(isatty=False))

        self.assertIn(unrelated_handler, root.handlers)
        wlogger.get_logger("test.unrelated").info("kept")
        self.assertIn("kept", stream.getvalue())

    def test_setup_failure_preserves_existing_configuration(self) -> None:
        stream = _FakeStream(isatty=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "app.log")
            wlogger.setup(
                level="INFO",
                log_file=str(log_path),
                console_stream=stream,
            )
            root = logging.getLogger()
            existing_handlers = list(root.handlers)

            with self.assertRaises(OSError):
                wlogger.setup(
                    level="DEBUG",
                    log_file=tmpdir,
                    console_stream=_FakeStream(isatty=False),
                )

            self.assertEqual(root.handlers, existing_handlers)
            wlogger.get_logger("test.rollback").info("still configured")
            self.assertIn("still configured", stream.getvalue())

    def test_console_and_file_levels_are_applied_independently(self) -> None:
        stream = _FakeStream(isatty=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "app.log")
            wlogger.setup(
                level="INFO",
                console_level="ERROR",
                file_level="DEBUG",
                log_file=str(log_path),
                console_stream=stream,
            )
            logger = wlogger.get_logger("test.level.split")

            logger.info("info-only-file")
            logger.error("error-both")

            file_lines = log_path.read_text(encoding="utf-8").strip().splitlines()

        self.assertNotIn("info-only-file", stream.getvalue())
        self.assertIn("error-both", stream.getvalue())
        file_payloads: list[dict[str, object]] = [
            _json_payload(line) for line in file_lines
        ]
        self.assertIn("info-only-file", [p["message"] for p in file_payloads])
        self.assertIn("error-both", [p["message"] for p in file_payloads])

    def test_root_level_uses_lowest_when_file_logging_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "app.log")
            wlogger.setup(
                level="WARNING",
                console_level="ERROR",
                file_level="DEBUG",
                log_file=str(log_path),
            )
            root = logging.getLogger()
        self.assertEqual(root.level, logging.DEBUG)

    def test_file_rotation_creates_backup_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir, "rotate.log")
            wlogger.setup(
                level="DEBUG",
                log_file=str(log_path),
                max_bytes=200,
                backup_count=2,
                console_stream=_FakeStream(isatty=False),
            )
            logger = wlogger.get_logger("test.rotation")
            for i in range(200):
                logger.info("msg-%03d %s", i, "x" * 80)

            rotated_1 = Path(tmpdir, "rotate.log.1")
            rotated_2 = Path(tmpdir, "rotate.log.2")
            self.assertTrue(rotated_1.exists())
            self.assertTrue(rotated_2.exists())


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

    def test_exc_info_is_rendered_in_console_line(self) -> None:
        formatter = ColorFormatter(use_color=False)
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            record = logging.LogRecord(
                "myapp", logging.ERROR, __file__, 10, "failed", None, sys.exc_info()
            )
        line = formatter.format(record)
        self.assertIn("Traceback", line)
        self.assertIn("RuntimeError: boom", line)

    def test_stack_info_is_rendered_in_console_line(self) -> None:
        formatter = ColorFormatter(use_color=False)
        record = self._record(logging.WARNING)
        record.stack_info = "stack line"

        line = formatter.format(record)

        self.assertIn("stack line", line)


class JsonFormatterTests(unittest.TestCase):
    def test_json_timestamp_is_utc_with_millisecond_precision(self) -> None:
        record = logging.LogRecord(
            "myapp", logging.INFO, __file__, 1, "hello", None, None
        )
        record.created = 0
        payload = _json_payload(JsonFormatter().format(record))

        self.assertEqual(payload["timestamp"], "1970-01-01T00:00:00.000Z")

    def test_json_formatter_contains_required_fields(self) -> None:
        record = logging.LogRecord(
            "myapp", logging.WARNING, __file__, 123, "hello", None, None
        )
        payload = _json_payload(JsonFormatter().format(record))

        self.assertIn("timestamp", payload)
        self.assertEqual(payload["level"], "WARNING")
        self.assertEqual(payload["logger"], "myapp")
        self.assertEqual(payload["message"], "hello")
        self.assertIsInstance(payload["process"], int)
        self.assertIsInstance(payload["thread"], str)
        self.assertIn("test_wlogger.py:123", cast(str, payload["file"]))

    def test_standard_attrs_are_not_leaked_as_extra_fields(self) -> None:
        record = logging.LogRecord(
            "myapp", logging.INFO, __file__, 1, "hello", None, None
        )
        payload = _json_payload(JsonFormatter().format(record))

        # taskName (added to LogRecord in Python 3.12) and other stdlib
        # attributes must not show up as noise in every log line.
        for noisy_key in ("taskName", "msg", "args", "levelno", "pathname"):
            self.assertNotIn(noisy_key, payload)

    def test_extra_fields_are_preserved(self) -> None:
        record = logging.LogRecord(
            "myapp", logging.INFO, __file__, 1, "hello", None, None
        )
        record.request_id = "abc-123"
        payload = _json_payload(JsonFormatter().format(record))

        self.assertEqual(payload["request_id"], "abc-123")

    def test_non_json_extra_values_are_stringified(self) -> None:
        record = logging.LogRecord(
            "myapp", logging.INFO, __file__, 1, "hello", None, None
        )
        record.path = Path("app.log")

        payload = _json_payload(JsonFormatter().format(record))

        self.assertEqual(payload["path"], "app.log")

    def test_exc_info_is_rendered_in_json_field(self) -> None:
        try:
            raise ValueError("bad-input")
        except ValueError:
            record = logging.LogRecord(
                "myapp", logging.ERROR, __file__, 33, "oops", None, sys.exc_info()
            )
        payload = _json_payload(JsonFormatter().format(record))
        self.assertIn("exc_info", payload)
        self.assertIn("ValueError: bad-input", cast(str, payload["exc_info"]))

    def test_stack_info_is_rendered_in_json_field(self) -> None:
        record = logging.LogRecord(
            "myapp", logging.WARNING, __file__, 1, "hello", None, None
        )
        record.stack_info = "stack line"

        payload = _json_payload(JsonFormatter().format(record))

        self.assertEqual(payload["stack_info"], "stack line")


if __name__ == "__main__":
    _ = unittest.main()
