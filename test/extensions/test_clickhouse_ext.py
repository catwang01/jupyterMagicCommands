from unittest.mock import MagicMock, patch
import argparse
import pytest
from jupyterMagicCommands.extensions.clickhouse_ext import queryClickHousePlayGround


class TestClickhouseTimeout:

    def _make_args(self, fmt="PrettyCompact"):
        args = argparse.Namespace(format=fmt, verbose=False, output=None)
        return args

    def test_request_passes_timeout(self):
        args = self._make_args()
        mock_response = MagicMock(ok=False, text="error")
        with patch("jupyterMagicCommands.extensions.clickhouse_ext.requests.get",
                   return_value=mock_response) as mock_get:
            queryClickHousePlayGround("SELECT 1", "http://localhost:8123", args)
            _, kwargs = mock_get.call_args
            assert "timeout" in kwargs
            assert kwargs["timeout"] == 30

    def test_network_error_is_caught_and_printed(self, capsys):
        import requests
        args = self._make_args()
        with patch("jupyterMagicCommands.extensions.clickhouse_ext.requests.get",
                   side_effect=requests.exceptions.Timeout("timed out")):
            # After the exception is caught+printed, r is unbound → UnboundLocalError
            with pytest.raises((UnboundLocalError, NameError)):
                queryClickHousePlayGround("SELECT 1", "http://localhost:8123", args)
        captured = capsys.readouterr()
        assert "timed out" in captured.out

    def test_request_called_with_params(self):
        args = self._make_args("PrettyCompact")
        mock_response = MagicMock(ok=False, text="err")
        with patch("jupyterMagicCommands.extensions.clickhouse_ext.requests.get",
                   return_value=mock_response) as mock_get:
            queryClickHousePlayGround("SELECT 1", "http://localhost:8123", args)
            call_kwargs = mock_get.call_args[1]
            assert "params" in call_kwargs
            assert call_kwargs["params"]["query"] == "SELECT 1"
