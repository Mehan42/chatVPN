"""Test ProxyBroker2 proxy type handling."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from proxybroker import Proxy
from proxybroker.errors import ProxyConnError, ProxyTimeoutError
from proxybroker.negotiators import NGTRS


class TestProxyTypeHandling:
    """Test various proxy type handling scenarios."""

    def test_proxy_type_recognition(self):
        """Test that proxy correctly recognizes different types."""
        # Test HTTP proxy
        proxy = Proxy("127.0.0.1", 8080)
        proxy.types = {"HTTP": "Anonymous"}
        assert "HTTP" in proxy.types
        assert proxy.types["HTTP"] == "Anonymous"

        # Test HTTPS proxy
        proxy.types = {"HTTPS": None}
        assert "HTTPS" in proxy.types
        assert proxy.types["HTTPS"] is None

        # Test SOCKS proxy
        proxy.types = {"SOCKS4": "High", "SOCKS5": "Anonymous"}
        assert "SOCKS4" in proxy.types
        assert "SOCKS5" in proxy.types
        assert proxy.types["SOCKS4"] == "High"
        assert proxy.types["SOCKS5"] == "Anonymous"

        # Test CONNECT proxy
        proxy.types = {"CONNECT:80": "Transparent", "CONNECT:25": None}
        assert "CONNECT:80" in proxy.types
        assert "CONNECT:25" in proxy.types
        assert proxy.types["CONNECT:80"] == "Transparent"
        assert proxy.types["CONNECT:25"] is None

    def test_proxy_type_combinations(self):
        """Test that proxy handles multiple types correctly."""
        proxy = Proxy("127.0.0.1", 8080)

        # Test combination of all types
        proxy.types = {
            "HTTP": "Anonymous",
            "HTTPS": None,
            "SOCKS4": "High",
            "SOCKS5": "Anonymous",
            "CONNECT:80": "Transparent",
            "CONNECT:25": None,
        }

        # All types should be present
        assert len(proxy.types) == 6
        assert "HTTP" in proxy.types
        assert "HTTPS" in proxy.types
        assert "SOCKS4" in proxy.types
        assert "SOCKS5" in proxy.types
        assert "CONNECT:80" in proxy.types
        assert "CONNECT:25" in proxy.types

        # Check values
        assert proxy.types["HTTP"] == "Anonymous"
        assert proxy.types["HTTPS"] is None
        assert proxy.types["SOCKS4"] == "High"
        assert proxy.types["SOCKS5"] == "Anonymous"
        assert proxy.types["CONNECT:80"] == "Transparent"
        assert proxy.types["CONNECT:25"] is None

    def test_proxy_type_validation(self):
        """Test that proxy validates type assignments."""
        proxy = Proxy("127.0.0.1", 8080)

        # Valid type assignments
        valid_types = [
            {"HTTP": "Anonymous"},
            {"HTTPS": None},
            {"SOCKS4": "High"},
            {"SOCKS5": "Anonymous"},
            {"CONNECT:80": "Transparent"},
            {"CONNECT:25": None},
            {},  # Empty dict
            None,  # None value
        ]

        for types in valid_types:
            try:
                proxy.types = types
                if types is None:
                    assert proxy.types == {}
                else:
                    assert proxy.types == types
            except Exception as e:
                pytest.fail(f"Valid types {types} caused exception: {e}")

        # Invalid type assignments should raise TypeError
        invalid_types = [
            "string",  # String instead of dict
            ["list"],  # List instead of dict
            ("tuple",),  # Tuple instead of dict
            123,  # Number instead of dict
            set(),  # Set instead of dict
        ]

        for types in invalid_types:
            with pytest.raises(TypeError):
                proxy.types = types

    def test_proxy_type_clearing(self):
        """Test that proxy can clear types."""
        proxy = Proxy("127.0.0.1", 8080)

        # Set some types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}
        assert len(proxy.types) == 2

        # Clear types with empty dict
        proxy.types = {}
        assert len(proxy.types) == 0
        assert proxy.types == {}

        # Set types again
        proxy.types = {"SOCKS5": "High"}
        assert len(proxy.types) == 1
        assert "SOCKS5" in proxy.types

        # Clear types with None
        proxy.types = None
        assert len(proxy.types) == 0
        assert proxy.types == {}

    def test_proxy_type_updating(self):
        """Test that proxy can update types incrementally."""
        proxy = Proxy("127.0.0.1", 8080)

        # Start with empty types
        assert proxy.types == {}

        # Add HTTP type
        proxy.types.update({"HTTP": "Anonymous"})
        assert len(proxy.types) == 1
        assert proxy.types["HTTP"] == "Anonymous"

        # Add HTTPS type
        proxy.types.update({"HTTPS": None})
        assert len(proxy.types) == 2
        assert proxy.types["HTTPS"] is None

        # Update existing type
        proxy.types.update({"HTTP": "High"})
        assert len(proxy.types) == 2
        assert proxy.types["HTTP"] == "High"

        # Add multiple types
        proxy.types.update({"SOCKS4": "Anonymous", "SOCKS5": None})
        assert len(proxy.types) == 4
        assert proxy.types["SOCKS4"] == "Anonymous"
        assert proxy.types["SOCKS5"] is None

    def test_proxy_type_removal(self):
        """Test that proxy can remove types."""
        proxy = Proxy("127.0.0.1", 8080)

        # Set multiple types
        proxy.types = {
            "HTTP": "Anonymous",
            "HTTPS": None,
            "SOCKS4": "High",
            "SOCKS5": "Anonymous",
        }
        assert len(proxy.types) == 4

        # Remove one type
        del proxy.types["HTTP"]
        assert len(proxy.types) == 3
        assert "HTTP" not in proxy.types

        # Remove another type
        del proxy.types["SOCKS4"]
        assert len(proxy.types) == 2
        assert "SOCKS4" not in proxy.types

        # Try to remove non-existent type (should raise KeyError)
        with pytest.raises(KeyError):
            del proxy.types["NONEXISTENT"]

    def test_proxy_type_iteration(self):
        """Test that proxy types can be iterated."""
        proxy = Proxy("127.0.0.1", 8080)

        # Set multiple types
        types = {
            "HTTP": "Anonymous",
            "HTTPS": None,
            "SOCKS4": "High",
            "SOCKS5": "Anonymous",
        }
        proxy.types = types

        # Should be able to iterate over keys
        keys = list(proxy.types.keys())
        assert len(keys) == 4
        assert "HTTP" in keys
        assert "HTTPS" in keys
        assert "SOCKS4" in keys
        assert "SOCKS5" in keys

        # Should be able to iterate over values
        values = list(proxy.types.values())
        assert len(values) == 4
        assert "Anonymous" in values
        assert None in values
        assert "High" in values

        # Should be able to iterate over items
        items = list(proxy.types.items())
        assert len(items) == 4
        assert ("HTTP", "Anonymous") in items
        assert ("HTTPS", None) in items
        assert ("SOCKS4", "High") in items
        assert ("SOCKS5", "Anonymous") in items

    def test_proxy_type_membership(self):
        """Test that proxy type membership works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Set types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}
        assert len(proxy.types) == 2

        # Test membership
        assert "HTTP" in proxy.types
        assert "HTTPS" in proxy.types
        assert "SOCKS4" not in proxy.types
        assert "SOCKS5" not in proxy.types

        # Test membership with get
        assert proxy.types.get("HTTP") == "Anonymous"
        assert proxy.types.get("HTTPS") is None
        assert proxy.types.get("SOCKS4") is None
        assert proxy.types.get("SOCKS5", "default") == "default"

    def test_proxy_type_equality(self):
        """Test that proxy types equality works."""
        proxy1 = Proxy("127.0.0.1", 8080)
        proxy2 = Proxy("127.0.0.1", 8080)

        # Empty types should be equal
        assert proxy1.types == proxy2.types

        # Same types should be equal
        proxy1.types = {"HTTP": "Anonymous"}
        proxy2.types = {"HTTP": "Anonymous"}
        assert proxy1.types == proxy2.types

        # Different types should not be equal
        proxy2.types = {"HTTPS": None}
        assert proxy1.types != proxy2.types

        # Same types with different values should not be equal
        proxy2.types = {"HTTP": "High"}
        assert proxy1.types != proxy2.types

        # Different lengths should not be equal
        proxy1.types = {"HTTP": "Anonymous", "HTTPS": None}
        proxy2.types = {"HTTP": "Anonymous"}
        assert proxy1.types != proxy2.types

    def test_proxy_type_copying(self):
        """Test that proxy types can be copied."""
        import copy

        proxy = Proxy("127.0.0.1", 8080)

        # Set types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}

        # Shallow copy
        types_copy = copy.copy(proxy.types)
        assert types_copy == proxy.types

        # Deep copy
        types_deepcopy = copy.deepcopy(proxy.types)
        assert types_deepcopy == proxy.types

        # Modifications to copy should not affect original
        types_copy["SOCKS4"] = "High"
        assert "SOCKS4" not in proxy.types
        assert "SOCKS4" in types_copy

    def test_proxy_type_json_serialization(self):
        """Test that proxy types can be serialized to JSON."""
        import json

        proxy = Proxy("127.0.0.1", 8080)

        # Set types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}

        # Convert to JSON-serializable format
        json_ready = []
        for proto, anon_lvl in proxy.types.items():
            json_ready.append({"type": proto, "level": anon_lvl or ""})

        # Should be serializable
        json_str = json.dumps(json_ready)
        assert isinstance(json_str, str)
        assert "HTTP" in json_str
        assert "Anonymous" in json_str
        assert "HTTPS" in json_str

        # Should be deserializable
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_proxy_type_string_representation(self):
        """Test that proxy types have proper string representation."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty types
        assert str(proxy.types) == "{}"

        # Single type
        proxy.types = {"HTTP": "Anonymous"}
        assert "HTTP" in str(proxy.types)
        assert "Anonymous" in str(proxy.types)

        # Multiple types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}
        assert "HTTP" in str(proxy.types)
        assert "HTTPS" in str(proxy.types)
        assert "Anonymous" in str(proxy.types)

    def test_proxy_type_repr(self):
        """Test that proxy types have proper repr."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty types
        assert repr(proxy.types) == "{}"

        # Single type
        proxy.types = {"HTTP": "Anonymous"}
        assert "HTTP" in repr(proxy.types)
        assert "Anonymous" in repr(proxy.types)

        # Multiple types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}
        assert "HTTP" in repr(proxy.types)
        assert "HTTPS" in repr(proxy.types)
        assert "Anonymous" in repr(proxy.types)

    def test_proxy_type_len(self):
        """Test that proxy types length works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty types
        assert len(proxy.types) == 0

        # Single type
        proxy.types = {"HTTP": "Anonymous"}
        assert len(proxy.types) == 1

        # Multiple types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None, "SOCKS4": "High"}
        assert len(proxy.types) == 3

        # Clear types
        proxy.types = {}
        assert len(proxy.types) == 0

    def test_proxy_type_bool(self):
        """Test that proxy types boolean conversion works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Empty types should be falsy
        assert not proxy.types

        # Non-empty types should be truthy
        proxy.types = {"HTTP": "Anonymous"}
        assert proxy.types

        # Cleared types should be falsy
        proxy.types = {}
        assert not proxy.types

    def test_proxy_type_pop(self):
        """Test that proxy types pop method works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Set types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None}

        # Pop existing key
        value = proxy.types.pop("HTTP")
        assert value == "Anonymous"
        assert "HTTP" not in proxy.types
        assert len(proxy.types) == 1

        # Pop with default
        value = proxy.types.pop("NONEXISTENT", "default")
        assert value == "default"

        # Pop without default for non-existent key should raise KeyError
        with pytest.raises(KeyError):
            proxy.types.pop("NONEXISTENT")

        # Pop last item
        value = proxy.types.pop("HTTPS")
        assert value is None
        assert len(proxy.types) == 0

    def test_proxy_type_clear(self):
        """Test that proxy types clear method works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Set types
        proxy.types = {"HTTP": "Anonymous", "HTTPS": None, "SOCKS4": "High"}
        assert len(proxy.types) == 3

        # Clear all types
        proxy.types.clear()
        assert len(proxy.types) == 0
        assert proxy.types == {}

        # Clear empty types should work
        proxy.types.clear()
        assert proxy.types == {}

    def test_proxy_type_setdefault(self):
        """Test that proxy types setdefault method works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Setdefault on empty types
        value = proxy.types.setdefault("HTTP", "Anonymous")
        assert value == "Anonymous"
        assert proxy.types["HTTP"] == "Anonymous"

        # Setdefault on existing key should return existing value
        value = proxy.types.setdefault("HTTP", "High")
        assert value == "Anonymous"  # Should return existing value
        assert proxy.types["HTTP"] == "Anonymous"  # Should not change

        # Setdefault on non-existing key should set and return default
        value = proxy.types.setdefault("HTTPS", None)
        assert value is None
        assert proxy.types["HTTPS"] is None

    def test_proxy_type_update_with_kwargs(self):
        """Test that proxy types update method works with kwargs."""
        proxy = Proxy("127.0.0.1", 8080)

        # Update with kwargs
        proxy.types.update(HTTP="Anonymous", HTTPS=None)
        assert len(proxy.types) == 2
        assert proxy.types["HTTP"] == "Anonymous"
        assert proxy.types["HTTPS"] is None

        # Update existing with kwargs
        proxy.types.update(HTTP="High", SOCKS4="Anonymous")
        assert len(proxy.types) == 3
        assert proxy.types["HTTP"] == "High"
        assert proxy.types["SOCKS4"] == "Anonymous"

    def test_proxy_type_fromkeys(self):
        """Test that proxy types fromkeys method works."""
        proxy = Proxy("127.0.0.1", 8080)

        # Create types from keys with default value
        keys = ["HTTP", "HTTPS", "SOCKS4"]
        proxy.types = dict.fromkeys(keys, "Anonymous")
        assert len(proxy.types) == 3
        for key in keys:
            assert proxy.types[key] == "Anonymous"

        # Create types from keys with None default
        proxy.types = dict.fromkeys(keys)
        assert len(proxy.types) == 3
        for key in keys:
            assert proxy.types[key] is None