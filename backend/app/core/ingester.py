"""Watchdog file watcher para ingestar logs en tiempo real."""

import asyncio
import logging

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings

logger = logging.getLogger(__name__)


class LogFileHandler(FileSystemEventHandler):
    """Handler que detecta cambios en archivos de log."""

    def __init__(self, callback):
        self.callback = callback
        self._file_positions: dict[str, int] = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        self._read_new_lines(event.src_path)

    def _read_new_lines(self, filepath: str) -> None:
        """Lee solo las líneas nuevas del archivo."""
        try:
            pos = self._file_positions.get(filepath, 0)
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                f.seek(pos)
                new_lines = f.readlines()
                self._file_positions[filepath] = f.tell()

            for line in new_lines:
                line = line.strip()
                if line:
                    self.callback(line, filepath)
        except Exception:
            logger.exception(f"Error leyendo {filepath}")


class LogIngester:
    """Monitorea archivos de log usando watchdog."""

    def __init__(self, callback):
        self.callback = callback
        self.observer = Observer()

    def start(self) -> None:
        """Inicia el monitoreo de archivos de log."""
        import os

        handler = LogFileHandler(self.callback)
        scheduled = set()

        for log_path in settings.log_paths_list:
            try:
                directory = os.path.dirname(log_path) or "."
                if not os.path.isdir(directory):
                    logger.warning(f"Directorio no existe, omitiendo: {directory}")
                    continue
                if directory not in scheduled:
                    self.observer.schedule(handler, directory, recursive=False)
                    scheduled.add(directory)
                # Inicializar posición al final del archivo para no reprocesar
                if os.path.isfile(log_path):
                    handler._file_positions[log_path] = os.path.getsize(log_path)
                logger.info(f"Monitoreando: {log_path}")
            except Exception:
                logger.exception(f"No se pudo monitorear: {log_path}")

        self.observer.start()
        logger.info(f"Ingester iniciado, {len(scheduled)} directorios monitoreados")

    def stop(self) -> None:
        """Detiene el monitoreo."""
        self.observer.stop()
        self.observer.join()
        logger.info("Ingester detenido")
