"""Fixtures compartidos para tests."""

import pytest


@pytest.fixture
def sample_auth_log_lines():
    """Líneas de ejemplo de auth.log."""
    return [
        'Mar 20 10:30:00 server sshd[1234]: Failed password for root from 45.33.32.156 port 54321 ssh2',
        'Mar 20 10:30:01 server sshd[1235]: Accepted password for jzambrano from 192.168.1.10 port 45000 ssh2',
        'Mar 20 10:30:02 server sshd[1236]: Invalid user admin from 185.220.101.34 port 33333',
        'Mar 20 10:30:03 server sudo: jzambrano : TTY=pts/0 ; PWD=/home/jzambrano ; USER=root ; COMMAND=/bin/systemctl restart nginx',
    ]


@pytest.fixture
def sample_apache_log_lines():
    """Líneas de ejemplo de Apache access.log."""
    return [
        '192.168.1.10 - - [20/Mar/2026:10:30:00 +0000] "GET /index.html HTTP/1.1" 200 1234',
        '45.33.32.156 - - [20/Mar/2026:10:30:01 +0000] "GET /../../etc/passwd HTTP/1.1" 403 287',
        "103.253.41.98 - - [20/Mar/2026:10:30:02 +0000] \"GET /search?q=1' OR 1=1-- HTTP/1.1\" 500 0",
    ]
