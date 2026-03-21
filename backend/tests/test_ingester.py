"""Tests para el ingester de logs."""

import os
import tempfile

from app.core.ingester import LogFileHandler, LogIngester


class TestLogFileHandler:

    def test_read_new_lines(self):
        """Verifica que lee solo líneas nuevas."""
        collected = []

        def callback(line, filepath):
            collected.append((line, filepath))

        handler = LogFileHandler(callback)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("line 1\nline 2\n")
            f.flush()
            path = f.name

        try:
            handler._read_new_lines(path)
            assert len(collected) == 2
            assert collected[0][0] == "line 1"
            assert collected[1][0] == "line 2"

            # Agregar más líneas
            with open(path, "a") as f:
                f.write("line 3\n")

            collected.clear()
            handler._read_new_lines(path)
            assert len(collected) == 1
            assert collected[0][0] == "line 3"
        finally:
            os.unlink(path)

    def test_read_empty_lines_skipped(self):
        """No procesa líneas vacías."""
        collected = []

        def callback(line, filepath):
            collected.append(line)

        handler = LogFileHandler(callback)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("line 1\n\n\nline 2\n")
            f.flush()
            path = f.name

        try:
            handler._read_new_lines(path)
            assert len(collected) == 2
        finally:
            os.unlink(path)

    def test_read_nonexistent_file(self):
        """No crashea con archivo inexistente."""
        handler = LogFileHandler(lambda l, f: None)
        handler._read_new_lines("/nonexistent/file.log")  # no debe lanzar

    def test_on_modified_skips_directory(self):
        """on_modified ignora eventos de directorio."""
        handler = LogFileHandler(lambda l, f: None)

        class FakeEvent:
            is_directory = True
            src_path = "/tmp"

        handler.on_modified(FakeEvent())  # no debe lanzar


class TestLogIngester:

    def test_init(self):
        ingester = LogIngester(lambda l, f: None)
        assert ingester.observer is not None

    def test_start_nonexistent_paths(self):
        """No crashea con paths que no existen."""
        from unittest.mock import patch

        with patch("app.core.ingester.settings") as mock_settings:
            mock_settings.log_paths_list = ["/nonexistent/path/file.log"]
            ingester = LogIngester(lambda l, f: None)
            ingester.start()
            ingester.stop()
