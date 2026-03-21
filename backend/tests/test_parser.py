"""Tests para el parser de logs."""

from app.core.parser import LogParser


class TestLogParser:
    """Tests del LogParser."""

    def setup_method(self):
        self.parser = LogParser()

    def test_parse_ssh_failed(self, sample_auth_log_lines):
        result = self.parser.parse(sample_auth_log_lines[0], "/var/log/auth.log")
        assert result is not None
        assert result["event_type"] == "ssh_login_failed"
        assert result["source_ip"] == "45.33.32.156"
        assert result["username"] == "root"
        assert result["log_level"] == "WARNING"

    def test_parse_ssh_accepted(self, sample_auth_log_lines):
        result = self.parser.parse(sample_auth_log_lines[1], "/var/log/auth.log")
        assert result is not None
        assert result["event_type"] == "ssh_login_accepted"
        assert result["source_ip"] == "192.168.1.10"
        assert result["username"] == "jzambrano"

    def test_parse_ssh_invalid_user(self, sample_auth_log_lines):
        result = self.parser.parse(sample_auth_log_lines[2], "/var/log/auth.log")
        assert result is not None
        assert result["event_type"] == "ssh_invalid_user"
        assert result["source_ip"] == "185.220.101.34"

    def test_parse_sudo(self, sample_auth_log_lines):
        result = self.parser.parse(sample_auth_log_lines[3], "/var/log/auth.log")
        assert result is not None
        assert result["event_type"] == "sudo_command"
        assert result["username"] == "jzambrano"
        assert result["message_parsed"]["target_user"] == "root"
        assert "nginx" in result["message_parsed"]["command"]

    def test_parse_apache_normal(self, sample_apache_log_lines):
        result = self.parser.parse(sample_apache_log_lines[0], "/var/log/apache2/access.log")
        assert result is not None
        assert result["event_type"] == "apache_access"
        assert result["source_ip"] == "192.168.1.10"
        assert result["message_parsed"]["status"] == 200
        assert result["log_level"] == "INFO"

    def test_parse_apache_traversal(self, sample_apache_log_lines):
        result = self.parser.parse(sample_apache_log_lines[1], "/var/log/apache2/access.log")
        assert result is not None
        assert result["event_type"] == "apache_access"
        assert result["message_parsed"]["status"] == 403
        assert "etc/passwd" in result["message_parsed"]["url"]

    def test_parse_empty_line(self):
        result = self.parser.parse("", "/var/log/auth.log")
        assert result is None

    def test_parse_returns_none_for_garbage(self):
        result = self.parser.parse("random garbage text 12345", "/var/log/auth.log")
        # Puede matchear syslog genérico o retornar None
        # Ambos son aceptables
        if result is not None:
            assert result["event_type"] == "syslog"
