"""Tests para el motor de alertas (reglas sin Redis)."""

import re

from app.core.alert_engine import (
    DIRECTORY_TRAVERSAL_PATTERNS,
    SQL_INJECTION_PATTERNS,
    AlertEngine,
)


class TestAlertPatterns:
    """Tests de los patrones regex de detección."""

    def test_sql_injection_union_select(self):
        assert SQL_INJECTION_PATTERNS.search("UNION SELECT * FROM users")

    def test_sql_injection_or_1_equals_1(self):
        assert SQL_INJECTION_PATTERNS.search("' OR 1=1--")

    def test_sql_injection_drop_table(self):
        assert SQL_INJECTION_PATTERNS.search("DROP TABLE users")

    def test_sql_injection_insert_into(self):
        assert SQL_INJECTION_PATTERNS.search("INSERT INTO admin")

    def test_sql_injection_select_from(self):
        assert SQL_INJECTION_PATTERNS.search("SELECT username FROM users")

    def test_sql_injection_comment(self):
        assert SQL_INJECTION_PATTERNS.search("admin'--")

    def test_normal_url_no_match(self):
        assert SQL_INJECTION_PATTERNS.search("/index.html") is None
        assert SQL_INJECTION_PATTERNS.search("/api/users/123") is None

    def test_directory_traversal_dotdot(self):
        assert DIRECTORY_TRAVERSAL_PATTERNS.search("../../etc/passwd")

    def test_directory_traversal_encoded(self):
        assert DIRECTORY_TRAVERSAL_PATTERNS.search("..%2F..%2Fetc/shadow")

    def test_directory_traversal_etc_passwd(self):
        assert DIRECTORY_TRAVERSAL_PATTERNS.search("/etc/passwd")

    def test_directory_traversal_proc_self(self):
        assert DIRECTORY_TRAVERSAL_PATTERNS.search("/proc/self/environ")

    def test_normal_url_no_traversal(self):
        assert DIRECTORY_TRAVERSAL_PATTERNS.search("/index.html") is None
        assert DIRECTORY_TRAVERSAL_PATTERNS.search("/api/data") is None


class TestAlertEngineCreateAlert:
    """Tests del método _create_alert."""

    def test_create_alert_structure(self):
        engine = AlertEngine()
        event = {"source_ip": "10.0.0.1"}
        result = engine._create_alert(event, "HIGH", "brute_force_ssh", "Test alert")
        assert result["severity"] == "HIGH"
        assert result["alert_type"] == "brute_force_ssh"
        assert result["description"] == "Test alert"
        assert result["source_ip"] == "10.0.0.1"
        assert "created_at" in result

    def test_create_alert_no_ip(self):
        engine = AlertEngine()
        event = {}
        result = engine._create_alert(event, "MEDIUM", "sudo_root", "Sudo detected")
        assert result["source_ip"] is None
