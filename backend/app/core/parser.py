"""Motor de parseo de logs multi-formato con regex compilados."""

import re
from datetime import datetime, timezone


class LogParser:
    """Parsea lineas de log de auth.log, apache access.log y syslog."""

    # Prefijo de timestamp: soporta formato clasico (Mar 27 20:25:02)
    # y formato ISO 8601 de rsyslog (2026-03-27T20:25:02.030562+00:00)
    _TS_CLASSIC = r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})"
    _TS_ISO = r"(?P<iso_ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?)"
    _TS_PREFIX = rf"(?:{_TS_ISO}|{_TS_CLASSIC})"

    # AUTH.LOG patterns — soportan ambos formatos de timestamp
    SSH_ACCEPTED = re.compile(
        _TS_PREFIX + r"\s+(?P<host>\S+)\s+sshd(?:-session)?\[\d+\]:\s+"
        r"Accepted\s+(?:password|publickey)\s+"
        r"for\s+(?P<user>\S+)\s+from\s+(?P<ip>[\d.]+)\s+port\s+(?P<port>\d+)"
    )

    SSH_FAILED = re.compile(
        _TS_PREFIX + r"\s+(?P<host>\S+)\s+sshd(?:-session)?\[\d+\]:\s+"
        r"Failed\s+password\s+"
        r"for\s+(?:invalid\s+user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>[\d.]+)"
    )

    SSH_INVALID_USER = re.compile(
        _TS_PREFIX + r"\s+(?P<host>\S+)\s+sshd(?:-session)?\[\d+\]:\s+"
        r"Invalid\s+user\s+(?P<user>\S*)\s+from\s+(?P<ip>[\d.]+)"
    )

    # Sudo: soporta formato clasico y nuevo (con indentacion)
    SUDO = re.compile(
        _TS_PREFIX + r"\s+(?P<host>\S+)\s+sudo(?:\[\d+\])?:\s+"
        r"(?P<user>\S+)\s+:\s+(?:TTY=(?P<tty>\S+)\s*;\s*)?"
        r"PWD=(?P<pwd>\S+)\s*;\s*USER=(?P<target_user>\S+)\s*;\s*COMMAND=(?P<cmd>.+)"
    )

    # APACHE ACCESS LOG (Combined Log Format)
    APACHE_ACCESS = re.compile(
        r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+-\s+(?P<user>\S+)\s+"
        r"\[(?P<timestamp>[^\]]+)\]\s+"
        r'"(?P<method>\w+)\s+(?P<url>\S+)\s+HTTP/(?P<version>[\d.]+)"\s+'
        r"(?P<status>\d{3})\s+(?P<bytes>\d+|-)"
    )

    # SSH connection closed (intentos de fuerza bruta que no llegan a auth)
    SSH_CONNECTION_CLOSED = re.compile(
        _TS_PREFIX + r"\s+(?P<host>\S+)\s+sshd(?:-session)?\[\d+\]:\s+"
        r"Connection\s+closed\s+by\s+(?:invalid\s+user\s+(?P<user>\S*)\s+)?"
        r"(?P<ip>[\d.]+)\s+port\s+(?P<port>\d+)"
    )

    # SYSLOG generico (catch-all) — ambos formatos
    SYSLOG = re.compile(
        _TS_PREFIX + r"\s+(?P<host>\S+)\s+(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.+)"
    )

    MONTH_MAP = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }

    def _parse_timestamp(self, match: re.Match) -> datetime:
        """Convierte timestamp de cualquier formato soportado a datetime UTC."""
        iso_ts = match.group("iso_ts")
        if iso_ts:
            # Formato ISO 8601: 2026-03-27T20:25:02.030562+00:00
            # Limpiar microsegundos y timezone para parsear
            clean = iso_ts
            if "+" in clean[10:] or clean.endswith("Z"):
                # Tiene timezone info
                try:
                    return datetime.fromisoformat(clean)
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(clean).replace(tzinfo=timezone.utc)
            except ValueError:
                # Fallback: parsear solo la parte principal
                return datetime.strptime(clean[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

        # Formato clasico: Mar 27 20:25:02
        month = self.MONTH_MAP.get(match.group("month"), 1)
        day = int(match.group("day"))
        time_parts = match.group("time").split(":")
        now = datetime.now(timezone.utc)
        return datetime(
            year=now.year, month=month, day=day,
            hour=int(time_parts[0]),
            minute=int(time_parts[1]),
            second=int(time_parts[2]),
            tzinfo=timezone.utc,
        )

    def parse(self, line: str, source_file: str) -> dict | None:
        """Parsea una linea de log y retorna un dict estructurado, o None."""
        line = line.strip()
        if not line:
            return None

        # SSH login exitoso
        m = self.SSH_ACCEPTED.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_timestamp(m),
                "source_file": source_file,
                "log_level": "INFO",
                "event_type": "ssh_login_accepted",
                "source_ip": m.group("ip"),
                "username": m.group("user"),
                "message_raw": line,
                "message_parsed": {"port": m.group("port"), "host": m.group("host")},
                "severity_score": 0.1,
            }

        # SSH login fallido
        m = self.SSH_FAILED.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_timestamp(m),
                "source_file": source_file,
                "log_level": "WARNING",
                "event_type": "ssh_login_failed",
                "source_ip": m.group("ip"),
                "username": m.group("user"),
                "message_raw": line,
                "message_parsed": {"host": m.group("host")},
                "severity_score": 0.4,
            }

        # SSH usuario invalido
        m = self.SSH_INVALID_USER.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_timestamp(m),
                "source_file": source_file,
                "log_level": "WARNING",
                "event_type": "ssh_invalid_user",
                "source_ip": m.group("ip"),
                "username": m.group("user") or "unknown",
                "message_raw": line,
                "message_parsed": {"host": m.group("host")},
                "severity_score": 0.5,
            }

        # SSH connection closed (intentos de escaneo/fuerza bruta)
        m = self.SSH_CONNECTION_CLOSED.search(line)
        if m:
            user = m.group("user")
            is_invalid = "invalid user" in line.lower()
            return {
                "timestamp_utc": self._parse_timestamp(m),
                "source_file": source_file,
                "log_level": "WARNING" if is_invalid else "INFO",
                "event_type": "ssh_connection_closed",
                "source_ip": m.group("ip"),
                "username": user or None,
                "message_raw": line,
                "message_parsed": {
                    "host": m.group("host"),
                    "port": m.group("port"),
                    "invalid_user": is_invalid,
                },
                "severity_score": 0.3 if is_invalid else 0.1,
            }

        # Sudo
        m = self.SUDO.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_timestamp(m),
                "source_file": source_file,
                "log_level": "WARNING",
                "event_type": "sudo_command",
                "source_ip": None,
                "username": m.group("user"),
                "message_raw": line,
                "message_parsed": {
                    "tty": m.group("tty"),
                    "pwd": m.group("pwd"),
                    "target_user": m.group("target_user"),
                    "command": m.group("cmd"),
                },
                "severity_score": 0.3,
            }

        # Apache access log
        m = self.APACHE_ACCESS.search(line)
        if m:
            status = int(m.group("status"))
            severity = 0.0
            if status >= 400:
                severity = 0.3
            if status >= 500:
                severity = 0.5

            return {
                "timestamp_utc": datetime.strptime(
                    m.group("timestamp"), "%d/%b/%Y:%H:%M:%S %z"
                ),
                "source_file": source_file,
                "log_level": "ERROR" if status >= 500 else ("WARNING" if status >= 400 else "INFO"),
                "event_type": "apache_access",
                "source_ip": m.group("ip"),
                "username": m.group("user") if m.group("user") != "-" else None,
                "message_raw": line,
                "message_parsed": {
                    "method": m.group("method"),
                    "url": m.group("url"),
                    "http_version": m.group("version"),
                    "status": status,
                    "bytes": int(m.group("bytes")) if m.group("bytes") != "-" else 0,
                },
                "severity_score": severity,
            }

        # Syslog generico (catch-all)
        m = self.SYSLOG.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_timestamp(m),
                "source_file": source_file,
                "log_level": "INFO",
                "event_type": "syslog",
                "source_ip": None,
                "username": None,
                "message_raw": line,
                "message_parsed": {
                    "host": m.group("host"),
                    "process": m.group("process"),
                    "pid": m.group("pid"),
                    "message": m.group("message"),
                },
                "severity_score": 0.0,
            }

        return None
