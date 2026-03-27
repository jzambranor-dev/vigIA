"""Watchdog file watcher para ingestar logs en tiempo real."""

import logging
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from app.config import settings

logger = logging.getLogger(__name__)

# Intervalo de polling en segundos
POLL_INTERVAL = 2


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
        """Lee solo las lineas nuevas del archivo."""
        try:
            current_size = os.path.getsize(filepath)
            pos = self._file_positions.get(filepath, 0)

            # Si el archivo se roto (tamano menor), resetear posicion
            if current_size < pos:
                pos = 0

            if current_size == pos:
                return

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                f.seek(pos)
                new_lines = f.readlines()
                self._file_positions[filepath] = f.tell()

            count = 0
            for line in new_lines:
                line = line.strip()
                if line:
                    self.callback(line, filepath)
                    count += 1

            if count > 0:
                logger.debug("Procesadas %d lineas de %s", count, filepath)
        except Exception:
            logger.exception("Error leyendo %s", filepath)


class LogIngester:
    """Monitorea archivos de log usando polling (compatible con Docker bind mounts)."""

    def __init__(self, callback):
        self.callback = callback
        self.observer = PollingObserver(timeout=POLL_INTERVAL)

    def start(self) -> None:
        """Inicia el monitoreo de archivos de log."""
        handler = LogFileHandler(self.callback)
        scheduled = set()

        for log_path in settings.log_paths_list:
            try:
                directory = os.path.dirname(log_path) or "."
                if not os.path.isdir(directory):
                    logger.warning("Directorio no existe, omitiendo: %s", directory)
                    continue
                if directory not in scheduled:
                    self.observer.schedule(handler, directory, recursive=False)
                    scheduled.add(directory)
                # Inicializar posicion al final del archivo para no reprocesar
                if os.path.isfile(log_path):
                    handler._file_positions[log_path] = os.path.getsize(log_path)
                logger.info("Monitoreando: %s", log_path)
            except Exception:
                logger.exception("No se pudo monitorear: %s", log_path)

        self.observer.start()
        logger.info("Ingester iniciado (polling cada %ds), %d directorios monitoreados", POLL_INTERVAL, len(scheduled))

    def stop(self) -> None:
        """Detiene el monitoreo."""
        self.observer.stop()
        self.observer.join()
        logger.info("Ingester detenido")
