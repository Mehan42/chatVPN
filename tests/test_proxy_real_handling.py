"""Test ProxyBroker2 real proxy handling."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from proxybroker import Proxy
from proxybroker.errors import (
    BadResponseError,
    BadStatusError,
    ProxyConnError,
    ProxyEmptyRecvError,
    ProxyRecvError,
    ProxySendError,
    ProxyTimeoutError,
    ResolveError,
)


class TestRealProxyHandling:
    """Test real proxy handling scenarios."""

    def test_proxy_creation_with_valid_ip(self):
        """Test creating proxy with valid IP address."""
        # Valid IPv4 addresses
        valid_ips = [
            "127.0.0.1",
            "8.8.8.8",
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
        ]

        for ip in valid_ips:
            proxy = Proxy(ip, 8080)
            assert proxy.host == ip
            assert proxy.port == 8080

    def test_proxy_creation_with_invalid_ip(self):
        """Test creating proxy with invalid IP address."""
        # Invalid IP addresses
        invalid_ips = [
            "256.0.0.1",  # Invalid octet
            "192.168.1.256",  # Invalid octet
            "192.168.1",  # Missing octet
            "192.168.1.1.1",  # Too many octets
            "not.an.ip.address",  # Invalid format
            "",  # Empty string
        ]

        for ip in invalid_ips:
            with pytest.raises(ValueError):
                Proxy(ip, 8080)

    def test_proxy_creation_with_valid_ports(self):
        """Test creating proxy with valid port numbers."""
        # Valid port numbers
        valid_ports = [1, 80, 443, 8080, 3128, 1080, 65535]

        for port in valid_ports:
            proxy = Proxy("127.0.0.1", port)
            assert proxy.host == "127.0.0.1"
            assert proxy.port == port

    def test_proxy_creation_with_invalid_ports(self):
        """Test creating proxy with invalid port numbers."""
        # Invalid port numbers
        invalid_ports = [-1, 0, 65536, 100000]

        for port in invalid_ports:
            with pytest.raises(ValueError):
                Proxy("127.0.0.1", port)

    def test_proxy_json_output_format(self):
        """Test that proxy JSON output follows expected format."""
        proxy = Proxy("8.8.8.8", 3128)
        proxy._runtimes = [1.5, 2.0, 2.5]
        proxy.types.update({"HTTP": "Anonymous", "HTTPS": None})

        json_output = proxy.as_json()

        # Check required fields
        required_fields = [
            "host",
            "port",
            "geo",
            "types",
            "avg_resp_time",
            "error_rate",
        ]

        for field in required_fields:
            assert field in json_output, f"Missing required field: {field}"

        # Check geo structure
        assert "country" in json_output["geo"]
        assert "code" in json_output["geo"]["country"]
        assert "name" in json_output["geo"]["country"]

        # Check types structure
        assert isinstance(json_output["types"], list)
        if json_output["types"]:  # If there are types
            first_type = json_output["types"][0]
            assert "type" in first_type
            assert "level" in first_type

        # Check numeric fields
        assert isinstance(json_output["avg_resp_time"], (int, float))
        assert isinstance(json_output["error_rate"], (int, float))
        assert json_output["avg_resp_time"] >= 0
        assert 0 <= json_output["error_rate"] <= 1

    def test_proxy_text_output_format(self):
        """Test that proxy text output follows expected format."""
        proxy = Proxy("8.8.8.8", 3128)

        text_output = proxy.as_text()

        # Should be in host:port format with newline
        assert text_output == "8.8.8.8:3128\n"

    def test_proxy_repr_format(self):
        """Test that proxy __repr__ follows expected format."""
        proxy = Proxy("8.8.8.8", 3128)
        proxy._runtimes = [1, 3, 3]
        proxy.types.update({"HTTP": "Anonymous", "HTTPS": None})

        repr_output = repr(proxy)

        # Should contain host:port
        assert "8.8.8.8:3128" in repr_output

        # Should contain types
        assert "HTTP: Anonymous" in repr_output

        # Should contain average response time
        assert "2.33s" in repr_output  # (1+3+3)/3 = 2.33

        # Should contain country code
        assert "US" in repr_output  # Default country for 8.8.8.8

    def test_proxy_geo_information(self):
        """Test that proxy provides geo information."""
        proxy = Proxy("8.8.8.8", 80)

        # Should have geo information
        geo = proxy.geo
        assert geo is not None
        assert hasattr(geo, "code")
        assert hasattr(geo, "name")
        assert hasattr(geo, "region_code")
        assert hasattr(geo, "region_name")
        assert hasattr(geo, "city_name")

        # For 8.8.8.8, should be US
        assert geo.code == "US"
        assert "United States" in geo.name

    def test_proxy_avg_resp_time_calculation(self):
        """Test that proxy calculates average response time correctly."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty runtimes should give 0
        assert proxy.avg_resp_time == 0.0

        # Add some runtimes
        proxy._runtimes = [1.0, 2.0, 3.0]

        # Should calculate average
        assert proxy.avg_resp_time == 2.0  # (1+2+3)/3

        # Add more runtimes
        proxy._runtimes.extend([4.0, 5.0])

        # Should recalculate average
        assert proxy.avg_resp_time == 3.0  # (1+2+3+4+5)/5

    def test_proxy_error_rate_calculation(self):
        """Test that proxy calculates error rate correctly."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty stats should give 0 error rate
        assert proxy.error_rate == 0.0

        # Add some stats
        proxy.stat["requests"] = 10
        proxy.stat["errors"] = {"timeout": 2, "connection": 3}

        # Should calculate error rate
        # Total errors = 2 + 3 = 5
        # Error rate = 5/10 = 0.5
        assert proxy.error_rate == 0.5

        # Add more requests without errors
        proxy.stat["requests"] = 20
        # Error rate should decrease
        assert proxy.error_rate == 0.25  # 5/20

    def test_proxy_schemes_property(self):
        """Test that proxy provides supported schemes."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty types should give empty schemes
        assert proxy.schemes == ()

        # Add HTTP type
        proxy.types.update({"HTTP": "Anonymous"})
        assert "HTTP" in proxy.schemes

        # Add HTTPS type
        proxy.types.update({"HTTPS": None})
        assert "HTTPS" in proxy.schemes

        # Should return tuple of unique schemes
        schemes = proxy.schemes
        assert isinstance(schemes, tuple)
        assert "HTTP" in schemes
        assert "HTTPS" in schemes

    def test_proxy_is_working_property(self):
        """Test that proxy tracks working status."""
        proxy = Proxy("127.0.0.1", 8080)

        # Initially should not be working
        assert proxy.is_working is False

        # Can be set to working
        proxy.is_working = True
        assert proxy.is_working is True

        # Can be set back to not working
        proxy.is_working = False
        assert proxy.is_working is False

    def test_proxy_types_property_getter_setter(self):
        """Test that proxy types property works correctly."""
        proxy = Proxy("127.0.0.1", 8080)

        # Getter should return empty dict initially
        assert proxy.types == {}

        # Setter should accept dict
        new_types = {"HTTP": "Anonymous", "HTTPS": None}
        proxy.types = new_types
        assert proxy.types == new_types

        # Setter should accept None (reset to empty dict)
        proxy.types = None
        assert proxy.types == {}

        # Setter should accept empty dict
        proxy.types = {}
        assert proxy.types == {}

        # Setter should reject invalid types
        with pytest.raises(TypeError):
            proxy.types = "invalid"  # String instead of dict

        with pytest.raises(TypeError):
            proxy.types = ["invalid"]  # List instead of dict

        with pytest.raises(TypeError):
            proxy.types = 123  # Number instead of dict

    def test_proxy_log_method(self):
        """Test that proxy log method works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Should be able to log messages
        proxy.log("Test message")

        # Should be able to log with start time
        import time

        start_time = time.time()
        proxy.log("Test message with timing", start_time)

        # Should be able to log with error
        proxy.log("Test error message", err=Exception("Test error"))

        # Should accumulate logs
        logs = proxy.get_log()
        assert len(logs) > 0

        # Logs should have expected structure
        for log_entry in logs:
            assert len(log_entry) == 3  # (negotiator, message, runtime)
            neg, msg, runtime = log_entry
            assert isinstance(neg, str)
            assert isinstance(msg, str)
            assert isinstance(runtime, (int, float))

    def test_proxy_get_log_method(self):
        """Test that proxy get_log method works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Initially should be empty
        assert proxy.get_log() == []

        # After logging should have entries
        proxy.log("Test message")
        logs = proxy.get_log()
        assert len(logs) == 1

        # Should accumulate logs
        proxy.log("Another message")
        logs = proxy.get_log()
        assert len(logs) == 2

        # Logs should be in chronological order
        first_log = logs[0]
        second_log = logs[1]
        assert first_log[1] == "Test message"
        assert second_log[1] == "Another message"

    def test_proxy_priority_calculation(self):
        """Test that proxy calculates priority correctly."""
        proxy = Proxy("127.0.0.1", 8080)

        # Should have priority property
        assert hasattr(proxy, "priority")
        priority = proxy.priority

        # Should be tuple of (error_rate, avg_resp_time)
        assert isinstance(priority, tuple)
        assert len(priority) == 2
        error_rate, avg_resp_time = priority
        assert isinstance(error_rate, (int, float))
        assert isinstance(avg_resp_time, (int, float))

        # Should reflect current values
        assert error_rate == proxy.error_rate
        assert avg_resp_time == proxy.avg_resp_time

    def test_proxy_ngtr_property(self):
        """Test that proxy negotiator property works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Should have ngtr property
        assert hasattr(proxy, "ngtr")

        # Initially should be None
        assert proxy.ngtr is None

        # Can be set to negotiator
        from proxybroker.negotiators import HttpsNgtr

        mock_negotiator = Mock(spec=HttpsNgtr)
        mock_negotiator.name = "HTTPS"
        proxy.ngtr = mock_negotiator
        assert proxy.ngtr == mock_negotiator

        # Can be set back to None
        proxy.ngtr = None
        assert proxy.ngtr is None

    def test_proxy_reader_writer_properties(self):
        """Test that proxy reader/writer properties work."""
        proxy = Proxy("127.0.0.1", 8080)

        # Should have reader and writer properties
        assert hasattr(proxy, "reader")
        assert hasattr(proxy, "writer")

        # Initially should be None
        assert proxy.reader is None
        assert proxy.writer is None

        # These properties are used internally and set during connection
        # We don't need to test setting them directly as that's internal logic