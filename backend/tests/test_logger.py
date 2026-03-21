"""Tests para la configuración de logging."""

import logging

from app.utils.logger import setup_logging


class TestLogger:

    def test_setup_logging_creates_handler(self):
        setup_logging("INFO")
        root = logging.getLogger()
        assert len(root.handlers) > 0

    def test_setup_logging_accepts_levels(self):
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            setup_logging(level)  # no debe lanzar excepción
