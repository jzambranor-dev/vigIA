"""Motor de parseo de logs multi-formato con regex compilados."""

import re
from datetime import datetime


class LogParser:
    """Parsea líneas de log de auth.log, apache access.log y syslog."""

    # AUTH.LOG patterns
    SSH_ACCEPTED = re.compile(
        r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+sshd\[\d+\]:\s+Accepted\s+(?:password|publickey)\s+"
        r"for\s+(?P<user>\S+)\s+from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+port\s+(?P<port>\d+)"
    )

    SSH_FAILED = re.compile(
        r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+sshd\[\d+\]:\s+Failed\s+password\s+"
        r"for\s+(?:invalid\s+user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)"
    )

    SSH_INVALID_USER = re.compile(
        r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+sshd\[\d+\]:\s+Invalid\s+user\s+(?P<user>\S+)\s+"
        r"from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)"
    )

    SUDO = re.compile(
        r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+sudo:\s+(?P<user>\S+)\s+:\s+TTY=(?P<tty>\S+)\s*;\s*"
        r"PWD=(?P<pwd>\S+)\s*;\s*USER=(?P<target_user>\S+)\s*;\s*COMMAND=(?P<cmd>.+)"
    )

    # APACHE ACCESS LOG (Combined Log Format)
    APACHE_ACCESS = re.compile(
        r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+-\s+(?P<user>\S+)\s+"
        r"\[(?P<timestamp>[^\]]+)\]\s+"
        r'"(?P<method>\w+)\s+(?P<url>\S+)\s+HTTP/(?P<version>[\d.]+)"\s+'
        r"(?P<status>\d{3})\s+(?P<bytes>\d+|-)"
    )

    # SYSLOG genérico
    SYSLOG = re.compile(
        r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.+)"
    )

    MONTH_MAP = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }

    def _parse_syslog_timestamp(self, match: re.Match) -> datetime:
        """Convierte timestamp de syslog (Mmm dd HH:MM:SS) a datetime."""
        month = self.MONTH_MAP.get(match.group("month"), 1)
        day = int(match.group("day"))
        time_parts = match.group("time").split(":")
        now = datetime.utcnow()
        return datetime(
            year=now.year, month=month, day=day,
            hour=int(time_parts[0]),
            minute=int(time_parts[1]),
            second=int(time_parts[2]),
        )

    def parse(self, line: str, source_file: str) -> dict | None:
        """Parsea una línea de log y retorna un dict estructurado, o None."""
        line = line.strip()
        if not line:
            return None

        # SSH login exitoso
        m = self.SSH_ACCEPTED.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_syslog_timestamp(m),
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
                "timestamp_utc": self._parse_syslog_timestamp(m),
                "source_file": source_file,
                "log_level": "WARNING",
                "event_type": "ssh_login_failed",
                "source_ip": m.group("ip"),
                "username": m.group("user"),
                "message_raw": line,
                "message_parsed": {"host": m.group("host")},
                "severity_score": 0.4,
            }

        # SSH usuario inválido
        m = self.SSH_INVALID_USER.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_syslog_timestamp(m),
                "source_file": source_file,
                "log_level": "WARNING",
                "event_type": "ssh_invalid_user",
                "source_ip": m.group("ip"),
                "username": m.group("user"),
                "message_raw": line,
                "message_parsed": {"host": m.group("host")},
                "severity_score": 0.5,
            }

        # Sudo
        m = self.SUDO.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_syslog_timestamp(m),
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

        # Syslog genérico (catch-all)
        m = self.SYSLOG.search(line)
        if m:
            return {
                "timestamp_utc": self._parse_syslog_timestamp(m),
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
