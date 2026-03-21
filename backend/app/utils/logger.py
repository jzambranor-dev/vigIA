"""Configuración de logging centralizada."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configura el logging del proyecto."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
