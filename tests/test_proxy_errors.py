"""Test ProxyBroker2 error handling."""

import asyncio
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


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_proxy_error_inheritance_hierarchy(self):
        """Test that proxy errors follow correct inheritance hierarchy."""
        # All proxy errors should inherit from Exception
        assert issubclass(ProxyConnError, Exception)
        assert issubclass(ProxyRecvError, Exception)
        assert issubclass(ProxySendError, Exception)
        assert issubclass(ProxyTimeoutError, Exception)
        assert issubclass(ProxyEmptyRecvError, Exception)
        assert issubclass(BadStatusError, Exception)
        assert issubclass(BadResponseError, Exception)
        assert issubclass(ResolveError, Exception)

        # Specific proxy errors should inherit from ProxyError
        from proxybroker.errors import ProxyError

        assert issubclass(ProxyConnError, ProxyError)
        assert issubclass(ProxyRecvError, ProxyError)
        assert issubclass(ProxySendError, ProxyError)
        assert issubclass(ProxyTimeoutError, ProxyError)
        assert issubclass(ProxyEmptyRecvError, ProxyError)
        assert issubclass(BadStatusError, ProxyError)
        assert issubclass(BadResponseError, ProxyError)

        # ResolveError should inherit from Exception but not ProxyError
        assert issubclass(ResolveError, Exception)
        # Note: ResolveError does not inherit from ProxyError in current implementation

    def test_proxy_error_messages(self):
        """Test that proxy errors have descriptive messages."""
        # Test each error type has meaningful error message
        errors = [
            (ProxyConnError, "connection_failed"),
            (ProxyRecvError, "connection_is_reset"),
            (ProxySendError, "connection_is_reset"),
            (ProxyTimeoutError, "connection_timeout"),
            (ProxyEmptyRecvError, "empty_response"),
            (BadStatusError, "bad_status"),
            (BadResponseError, "bad_response"),
            (ResolveError, "Resolve error"),
        ]

        for error_class, expected_message in errors:
            error_instance = error_class("Test error")
            assert str(error_instance) == "Test error"
            assert hasattr(error_instance, "errmsg")
            assert error_instance.errmsg is not None

    def test_proxy_error_attributes(self):
        """Test that proxy errors have required attributes."""
        # All proxy errors should have errmsg attribute
        error_classes = [
            ProxyConnError,
            ProxyRecvError,
            ProxySendError,
            ProxyTimeoutError,
            ProxyEmptyRecvError,
            BadStatusError,
            BadResponseError,
            ResolveError,
        ]

        for error_class in error_classes:
            error_instance = error_class("Test error")
            assert hasattr(error_instance, "errmsg")
            # errmsg should be a string
            assert isinstance(error_instance.errmsg, str)

    def test_proxy_connection_error_scenarios(self):
        """Test proxy connection error scenarios."""
        # Test various connection error scenarios
        connection_errors = [
            ConnectionRefusedError("Connection refused"),
            OSError("Network is unreachable"),
            BrokenPipeError("Broken pipe"),
        ]

        for error in connection_errors:
            proxy_error = ProxyConnError(str(error))
            assert proxy_error.errmsg == "connection_failed"
            assert str(proxy_error) == str(error)

    def test_proxy_receive_error_scenarios(self):
        """Test proxy receive error scenarios."""
        # Test various receive error scenarios
        receive_errors = [
            ConnectionResetError("Connection reset by peer"),
            OSError("Network is unreachable"),
        ]

        for error in receive_errors:
            proxy_error = ProxyRecvError(str(error))
            assert proxy_error.errmsg == "connection_is_reset"
            assert str(proxy_error) == str(error)

    def test_proxy_send_error_scenarios(self):
        """Test proxy send error scenarios."""
        # Test various send error scenarios
        send_errors = [
            ConnectionResetError("Connection reset by peer"),
            BrokenPipeError("Broken pipe"),
        ]

        for error in send_errors:
            proxy_error = ProxySendError(str(error))
            assert proxy_error.errmsg == "connection_is_reset"
            assert str(proxy_error) == str(error)

    def test_proxy_timeout_error_scenarios(self):
        """Test proxy timeout error scenarios."""
        # Test timeout error scenarios
        timeout_errors = [
            asyncio.TimeoutError("Connection timeout"),
            TimeoutError("Operation timeout"),
        ]

        for error in timeout_errors:
            proxy_error = ProxyTimeoutError(str(error))
            assert proxy_error.errmsg == "connection_timeout"
            assert str(proxy_error) == str(error)

    def test_proxy_empty_receive_error_scenarios(self):
        """Test proxy empty receive error scenarios."""
        # Test empty receive error scenarios
        empty_errors = [
            ValueError("Empty response"),
            EOFError("End of file"),
        ]

        for error in empty_errors:
            proxy_error = ProxyEmptyRecvError(str(error))
            assert proxy_error.errmsg == "empty_response"
            assert str(proxy_error) == str(error)

    def test_bad_status_error_scenarios(self):
        """Test bad status error scenarios."""
        # Test bad status error scenarios
        status_errors = [
            ValueError("Bad status line"),
            Exception("Invalid HTTP status"),
        ]

        for error in status_errors:
            bad_status_error = BadStatusError(str(error))
            assert bad_status_error.errmsg == "bad_status"
            assert str(bad_status_error) == str(error)

    def test_bad_response_error_scenarios(self):
        """Test bad response error scenarios."""
        # Test bad response error scenarios
        response_errors = [
            ValueError("Bad response"),
            Exception("Invalid response format"),
        ]

        for error in response_errors:
            bad_response_error = BadResponseError(str(error))
            assert bad_response_error.errmsg == "bad_response"
            assert str(bad_response_error) == str(error)

    def test_resolve_error_scenarios(self):
        """Test resolve error scenarios."""
        # Test resolve error scenarios
        resolve_errors = [
            ValueError("Cannot resolve hostname"),
            Exception("DNS resolution failed"),
        ]

        for error in resolve_errors:
            resolve_error = ResolveError(str(error))
            assert resolve_error.errmsg == "Resolve error"
            assert str(resolve_error) == str(error)

    def test_proxy_error_comparison(self):
        """Test that proxy errors can be compared."""
        # Test equality comparison
        error1 = ProxyConnError("Connection failed")
        error2 = ProxyConnError("Connection failed")
        error3 = ProxyRecvError("Connection reset")

        # Same type and message should be equal
        assert error1 == error2

        # Different types should not be equal
        assert error1 != error3

        # Different messages should not be equal
        error4 = ProxyConnError("Different message")
        assert error1 != error4

    def test_proxy_error_hashing(self):
        """Test that proxy errors can be hashed."""
        # Test hashing for use in sets and dicts
        error1 = ProxyConnError("Connection failed")
        error2 = ProxyConnError("Connection failed")
        error3 = ProxyRecvError("Connection reset")

        # Same errors should have same hash
        assert hash(error1) == hash(error2)

        # Different errors should have different hashes
        assert hash(error1) != hash(error3)

        # Should be usable in sets
        error_set = {error1, error2, error3}
        assert len(error_set) == 2  # error1 and error2 are considered the same

        # Should be usable as dict keys
        error_dict = {error1: "first", error3: "second"}
        assert len(error_dict) == 2
        assert error_dict[error1] == "first"
        assert error_dict[error3] == "second"

    def test_proxy_error_pickling(self):
        """Test that proxy errors can be pickled."""
        import pickle

        # Test that errors can be pickled and unpickled
        original_error = ProxyConnError("Connection failed")

        # Pickle the error
        pickled_data = pickle.dumps(original_error)

        # Unpickle the error
        unpickled_error = pickle.loads(pickled_data)

        # Should be equivalent
        assert isinstance(unpickled_error, ProxyConnError)
        assert str(unpickled_error) == str(original_error)
        assert unpickled_error.errmsg == original_error.errmsg

    def test_proxy_error_traceback_preservation(self):
        """Test that proxy errors preserve traceback information."""
        import traceback

        try:
            # Raise a proxy error
            raise ProxyConnError("Connection failed")
        except ProxyConnError as e:
            # Capture traceback
            tb = traceback.format_exc()

            # Should contain error information
            assert "ProxyConnError" in tb
            assert "Connection failed" in tb

    def test_proxy_error_chaining(self):
        """Test that proxy errors can be chained."""
        # Test exception chaining
        try:
            # Raise underlying error
            raise ConnectionRefusedError("Connection refused")
        except ConnectionRefusedError as underlying_error:
            # Chain proxy error
            proxy_error = ProxyConnError("Failed to connect") from underlying_error

            # Should preserve chain
            assert proxy_error.__cause__ is underlying_error
            assert isinstance(proxy_error.__cause__, ConnectionRefusedError)
            assert str(proxy_error.__cause__) == "Connection refused"

    def test_proxy_error_context(self):
        """Test that proxy errors preserve context."""
        # Test implicit exception chaining
        try:
            # Raise underlying error
            raise ValueError("Invalid value")
        except ValueError:
            # Raise proxy error in except block
            raise ProxyConnError("Connection failed")

        # Note: This test is incomplete as it doesn't actually catch the chained exception
        # In practice, implicit chaining would be tested by catching the final exception
        # and checking its __context__ attribute

    def test_proxy_error_formatting(self):
        """Test that proxy errors format correctly."""
        # Test string representation
        error = ProxyConnError("Connection to 127.0.0.1:8080 failed")

        # Should include error message
        error_str = str(error)
        assert "Connection to 127.0.0.1:8080 failed" in error_str

        # Should be readable
        assert isinstance(error_str, str)
        assert len(error_str) > 0

    def test_proxy_error_repr(self):
        """Test that proxy errors have proper repr."""
        # Test repr representation
        error = ProxyConnError("Connection failed")

        # Should include class name and message
        error_repr = repr(error)
        assert "ProxyConnError" in error_repr
        assert "Connection failed" in error_repr

    def test_proxy_error_inheritance_from_builtin(self):
        """Test that proxy errors inherit properly from builtin exceptions."""
        # All proxy errors should be instances of Exception
        error = ProxyConnError("Test error")
        assert isinstance(error, Exception)

        # Should also be instances of their specific error class
        assert isinstance(error, ProxyConnError)

        # Should not be instances of unrelated error classes
        assert not isinstance(error, ValueError)
        assert not isinstance(error, TypeError)

    def test_proxy_error_args(self):
        """Test that proxy errors handle arguments correctly."""
        # Test single argument
        error1 = ProxyConnError("Single argument")
        assert str(error1) == "Single argument"

        # Test multiple arguments
        error2 = ProxyConnError("Multiple", "arguments")
        assert "Multiple" in str(error2)
        assert "arguments" in str(error2)

        # Test keyword arguments
        error3 = ProxyConnError(message="Keyword argument")
        assert "message" in str(error3)
        assert "Keyword argument" in str(error3)