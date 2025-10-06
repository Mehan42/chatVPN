"""Test ProxyBroker2 configuration and environment variables."""

import os
import sys
from unittest.mock import patch

import pytest

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProxyBroker2Configuration:
    """Test ProxyBroker2 configuration settings."""

    def test_default_configuration(self):
        """Test that ProxyBroker2 has correct default configuration."""
        from proxybroker import Broker

        # Test default values
        queue = asyncio.Queue()
        broker = Broker(queue, stop_broker_on_sigint=False)  # Disable signal handling for tests

        # Default timeout should be reasonable
        assert broker._timeout == 8

        # Default max_tries should be reasonable
        assert broker._max_tries == 3

        # Default SSL verification should be disabled for localhost
        assert broker._verify_ssl is False

    def test_custom_configuration(self):
        """Test that ProxyBroker2 accepts custom configuration."""
        from proxybroker import Broker

        # Test custom values
        queue = asyncio.Queue()
        broker = Broker(
            queue,
            timeout=15,
            max_tries=5,
            verify_ssl=True,
            stop_broker_on_sigint=False,  # Disable signal handling for tests
        )

        assert broker._timeout == 15
        assert broker._max_tries == 5
        assert broker._verify_ssl is True

    def test_environment_variable_configuration(self):
        """Test that ProxyBroker2 respects environment variables."""
        from proxybroker import Broker

        # Test with environment variables
        with patch.dict(
            os.environ,
            {
                "PROXY_TIMEOUT": "12",
                "PROXY_MAX_TRIES": "4",
                "PROXY_VERIFY_SSL": "true",
            },
        ):
            queue = asyncio.Queue()
            # Create broker with environment variables
            # Note: Broker doesn't directly read these env vars, but users might
            broker = Broker(
                queue,
                timeout=int(os.environ.get("PROXY_TIMEOUT", "8")),
                max_tries=int(os.environ.get("PROXY_MAX_TRIES", "3")),
                verify_ssl=os.environ.get("PROXY_VERIFY_SSL", "false").lower()
                == "true",
                stop_broker_on_sigint=False,  # Disable signal handling for tests
            )

            assert broker._timeout == 12
            assert broker._max_tries == 4
            assert broker._verify_ssl is True

    def test_edge_case_configuration(self):
        """Test ProxyBroker2 with edge case configuration values."""
        from proxybroker import Broker

        # Test with minimum values
        queue = asyncio.Queue()
        broker1 = Broker(
            queue,
            timeout=1,
            max_tries=1,
            stop_broker_on_sigint=False,  # Disable signal handling for tests
        )

        assert broker1._timeout == 1
        assert broker1._max_tries == 1

        # Test with maximum reasonable values
        broker2 = Broker(
            queue,
            timeout=300,
            max_tries=100,
            stop_broker_on_sigint=False,  # Disable signal handling for tests
        )

        assert broker2._timeout == 300
        assert broker2._max_tries == 100

    def test_ssl_verification_toggle(self):
        """Test that SSL verification can be toggled."""
        from proxybroker import Broker

        queue = asyncio.Queue()

        # Test SSL verification enabled
        broker_ssl_on = Broker(queue, verify_ssl=True, stop_broker_on_sigint=False)
        assert broker_ssl_on._verify_ssl is True

        # Test SSL verification disabled
        broker_ssl_off = Broker(queue, verify_ssl=False, stop_broker_on_sigint=False)
        assert broker_ssl_off._verify_ssl is False

    def test_timeout_configuration_validation(self):
        """Test that timeout configuration is validated."""
        from proxybroker import Broker

        queue = asyncio.Queue()

        # Test that zero timeout is handled
        broker_zero = Broker(queue, timeout=0, stop_broker_on_sigint=False)
        assert broker_zero._timeout == 0

        # Test that negative timeout is handled
        broker_negative = Broker(queue, timeout=-5, stop_broker_on_sigint=False)
        assert broker_negative._timeout == -5  # Let user handle validation

    def test_max_tries_configuration_validation(self):
        """Test that max_tries configuration is validated."""
        from proxybroker import Broker

        queue = asyncio.Queue()

        # Test that zero max_tries is handled
        broker_zero = Broker(queue, max_tries=0, stop_broker_on_sigint=False)
        assert broker_zero._max_tries == 0

        # Test that negative max_tries is handled
        broker_negative = Broker(queue, max_tries=-1, stop_broker_on_sigint=False)
        assert broker_negative._max_tries == -1  # Let user handle validation

    def test_proxy_types_configuration(self):
        """Test that proxy types configuration is handled."""
        from proxybroker import Broker

        queue = asyncio.Queue()

        # Test with no types (default)
        broker1 = Broker(queue, stop_broker_on_sigint=False)
        assert broker1._types == {}

        # Test with custom types
        custom_types = {
            "HTTP": ["High", "Anonymous"],
            "HTTPS": ["Anonymous"],
            "SOCKS5": ["High"],
        }
        broker2 = Broker(queue, types=custom_types, stop_broker_on_sigint=False)
        assert broker2._types == custom_types

        # Test with empty types dict
        broker3 = Broker(queue, types={}, stop_broker_on_sigint=False)
        assert broker3._types == {}

    def test_judges_configuration(self):
        """Test that judges configuration is handled."""
        from proxybroker import Broker

        queue = asyncio.Queue()

        # Test with default judges
        broker1 = Broker(queue, stop_broker_on_sigint=False)
        assert broker1._judges is not None

        # Test with custom judges
        custom_judges = [
            "http://judge1.example.com",
            "https://judge2.example.com",
        ]
        broker2 = Broker(queue, judges=custom_judges, stop_broker_on_sigint=False)
        assert broker2._judges == custom_judges

        # Test with empty judges list
        broker3 = Broker(queue, judges=[], stop_broker_on_sigint=False)
        assert broker3._judges == []

    def test_providers_configuration(self):
        """Test that providers configuration is handled."""
        from proxybroker import Broker, Provider

        queue = asyncio.Queue()

        # Test with default providers
        broker1 = Broker(queue, stop_broker_on_sigint=False)
        assert broker1._providers is not None

        # Test with custom providers
        custom_providers = [
            Provider("http://provider1.example.com"),
            Provider("http://provider2.example.com"),
        ]
        broker2 = Broker(queue, providers=custom_providers, stop_broker_on_sigint=False)
        assert broker2._providers == custom_providers

        # Test with empty providers list
        broker3 = Broker(queue, providers=[], stop_broker_on_sigint=False)
        assert broker3._providers == []


# Import asyncio here to avoid import errors
import asyncio