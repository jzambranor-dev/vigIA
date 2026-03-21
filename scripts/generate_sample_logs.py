#!/usr/bin/env python3
"""Genera logs de prueba con ataques simulados para testing y demo."""

import random
from datetime import datetime, timedelta

OUTPUT_FILE = "sample_logs.log"

# IPs de ejemplo
NORMAL_IPS = ["192.168.1.10", "192.168.1.20", "10.0.0.5", "10.0.0.15"]
ATTACKER_IPS = ["45.33.32.156", "185.220.101.34", "103.253.41.98"]
USERS = ["admin", "jzambrano", "webmaster", "deploy", "backup"]


def random_timestamp(base: datetime, offset_minutes: int = 0) -> str:
    """Genera un timestamp syslog."""
    ts = base + timedelta(minutes=offset_minutes, seconds=random.randint(0, 59))
    return ts.strftime("%b %d %H:%M:%S")


def random_apache_timestamp(base: datetime, offset_minutes: int = 0) -> str:
    """Genera un timestamp Apache."""
    ts = base + timedelta(minutes=offset_minutes, seconds=random.randint(0, 59))
    return ts.strftime("%d/%b/%Y:%H:%M:%S +0000")


def generate():
    """Genera el archivo de logs de prueba."""
    lines = []
    base = datetime(2026, 3, 20, 8, 0, 0)

    # --- 500 líneas Apache access normal ---
    urls = ["/", "/index.html", "/login", "/dashboard", "/api/status", "/css/style.css",
            "/js/app.js", "/images/logo.png", "/about", "/contact"]
    methods = ["GET", "POST", "GET", "GET", "GET"]
    for i in range(500):
        ip = random.choice(NORMAL_IPS)
        url = random.choice(urls)
        method = random.choice(methods)
        status = random.choice([200, 200, 200, 200, 301, 304])
        size = random.randint(200, 50000)
        ts = random_apache_timestamp(base, i // 5)
        lines.append(f'{ip} - - [{ts}] "{method} {url} HTTP/1.1" {status} {size}')

    # --- 50 líneas brute force SSH (misma IP, usuario root) ---
    attacker = ATTACKER_IPS[0]
    for i in range(50):
        ts = random_timestamp(base + timedelta(hours=2), i)
        lines.append(f"{ts} server sshd[{random.randint(1000, 9999)}]: "
                     f"Failed password for root from {attacker} port {random.randint(40000, 65000)} ssh2")

    # --- 20 líneas auth.log normal (logins exitosos) ---
    for i in range(20):
        user = random.choice(USERS)
        ip = random.choice(NORMAL_IPS)
        ts = random_timestamp(base + timedelta(hours=1), i * 5)
        port = random.randint(40000, 65000)
        lines.append(f"{ts} server sshd[{random.randint(1000, 9999)}]: "
                     f"Accepted password for {user} from {ip} port {port} ssh2")

    # --- 10 líneas directory traversal ---
    traversal_urls = [
        "/../../etc/passwd",
        "/..%2F..%2Fetc/shadow",
        "/files/../../../etc/passwd",
        "/download?file=../../../etc/passwd",
        "/view?path=....//....//etc/passwd",
    ]
    attacker2 = ATTACKER_IPS[1]
    for i in range(10):
        url = random.choice(traversal_urls)
        ts = random_apache_timestamp(base + timedelta(hours=3), i)
        lines.append(f'{attacker2} - - [{ts}] "GET {url} HTTP/1.1" 403 287')

    # --- 5 líneas SQL injection ---
    sqli_urls = [
        "/search?q=1' OR 1=1--",
        "/login?user=admin' UNION SELECT * FROM users--",
        "/api/data?id=1; DROP TABLE users;--",
        "/products?cat=1 UNION SELECT username,password FROM users",
        "/page?id=1' AND 1=1 UNION SELECT NULL,table_name FROM information_schema.tables--",
    ]
    attacker3 = ATTACKER_IPS[2]
    for i in range(5):
        url = sqli_urls[i]
        ts = random_apache_timestamp(base + timedelta(hours=4), i)
        lines.append(f'{attacker3} - - [{ts}] "GET {url} HTTP/1.1" 500 0')

    # --- Mezclar y escribir ---
    random.shuffle(lines)
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Generadas {len(lines)} líneas en {OUTPUT_FILE}")
    print(f"  - 500 Apache access normal")
    print(f"  - 50 brute force SSH")
    print(f"  - 20 auth.log exitosos")
    print(f"  - 10 directory traversal")
    print(f"  - 5 SQL injection")


if __name__ == "__main__":
    generate()
