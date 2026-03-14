from __future__ import annotations

from unittest.mock import patch, MagicMock

from app.nut_client import _parse_list_var, query_ups


def test_parse_list_var():
    data = """\
BEGIN LIST VAR eaton
VAR eaton battery.charge "100"
VAR eaton battery.runtime "2340"
VAR eaton ups.status "OL"
VAR eaton ups.load "23.0"
VAR eaton input.voltage "121.5"
VAR eaton output.voltage "121.5"
VAR eaton output.current "1.2"
VAR eaton ups.power "138"
VAR eaton ups.realpower "120"
VAR eaton ups.temperature "29.0"
END LIST VAR eaton
"""
    result = _parse_list_var(data, "eaton")
    assert result["battery.charge"] == "100"
    assert result["ups.status"] == "OL"
    assert result["ups.load"] == "23.0"
    assert result["input.voltage"] == "121.5"
    assert len(result) == 10


def test_parse_list_var_ignores_non_var_lines():
    data = """\
BEGIN LIST VAR eaton
VAR eaton ups.status "OB"
some garbage line
END LIST VAR eaton
"""
    result = _parse_list_var(data, "eaton")
    assert result == {"ups.status": "OB"}


def test_query_ups_returns_typed_values():
    raw_response = """\
BEGIN LIST VAR eaton
VAR eaton battery.charge "95"
VAR eaton battery.runtime "1800"
VAR eaton ups.status "OL"
VAR eaton ups.load "23.5"
VAR eaton input.voltage "121.5"
VAR eaton output.voltage "121.5"
END LIST VAR eaton
"""
    mock_sock = MagicMock()
    mock_sock.recv.side_effect = [raw_response.encode(), b""]
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)

    with patch("app.nut_client.socket.create_connection", return_value=mock_sock):
        result = query_ups()

    assert result["battery_charge"] == 95.0
    assert result["battery_runtime"] == 1800.0
    assert result["ups_status"] == "OL"
    assert result["ups_load"] == 23.5
    assert "timestamp" in result


def test_query_ups_connection_refused():
    import socket
    with patch("app.nut_client.socket.create_connection", side_effect=ConnectionRefusedError("refused")):
        result = query_ups()
    assert result["status"] == "error"
    assert result["retryable"] is True
    assert "ConnectionRefusedError" in result["message"]


def test_query_ups_timeout():
    import socket
    with patch("app.nut_client.socket.create_connection", side_effect=socket.timeout("timed out")):
        result = query_ups()
    assert result["status"] == "error"
    assert result["retryable"] is True
