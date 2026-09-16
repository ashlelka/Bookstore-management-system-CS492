"""
Bookstore Management System
Sprint 2 - T2-008
Developer: Ashley Lindamood

Tests for receipt generation and email receipt functionality.
"""

import os
from unittest.mock import patch, MagicMock

from sales_app import (
    app,
    generate_receipt,
    generate_historical_receipt,
    send_receipt_email,
)


def sample_sale():
    """Create sample sale data for receipt testing."""
    return {
        "id": "SALE-TEST-001",
        "timestamp": "2026-09-16T13:52:51",
        "items": [
            {
                "name": "1984",
                "qty": 1,
                "unitPrice": 11.99,
                "lineTotal": 11.99,
                "exempt": False,
            }
        ],
        "subtotal": 11.99,
        "tax": 0.84,
        "total": 12.83,
        "taxLabel": "IN tax (7%)",
    }


def test_receipt_generation():
    """Test that a normal receipt contains expected sale information."""
    receipt = generate_receipt(sample_sale())

    assert "SALE-TEST-001" in receipt
    assert "1984" in receipt
    assert "$11.99" in receipt
    assert "$0.84" in receipt
    assert "$12.83" in receipt


def test_historical_receipt_generation():
    """Test receipt generation from stored sales history."""
    sale = {
        "sale_id": "SALE-HISTORY-001",
        "date": "2026-09-16T12:20:00",
        "items": [
            {
                "name": "Betrayal at Falador",
                "quantity": 1,
                "price": 30.00,
                "line_total": 30.00,
            }
        ],
        "subtotal": 30.00,
        "tax": 1.80,
        "total": 31.80,
    }

    receipt = generate_historical_receipt(sale)

    assert "SALE-HISTORY-001" in receipt
    assert "Betrayal at Falador" in receipt
    assert "$30.00" in receipt
    assert "$1.80" in receipt
    assert "$31.80" in receipt


def test_email_not_configured():
    """Test safe failure when email environment variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        success, message = send_receipt_email(
            "customer@example.com",
            "TEST RECEIPT",
            "SALE-TEST-001",
        )

    assert success is False
    assert message == "Email service is not configured."


@patch("sales_app.smtplib.SMTP_SSL")
def test_email_receipt_success(mock_smtp):
    """Test successful email without contacting Yahoo."""
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    with patch.dict(
        os.environ,
        {
            "BMS_EMAIL": "bookstore@yahoo.com",
            "BMS_EMAIL_PASSWORD": "test-app-password",
        },
    ):
        success, message = send_receipt_email(
            "customer@example.com",
            "TEST RECEIPT",
            "SALE-TEST-001",
        )

    assert success is True
    assert message == "Receipt emailed successfully."

    mock_server.login.assert_called_once()
    mock_server.send_message.assert_called_once()


def test_receipt_route_without_receipt():
    """Test that receipt page redirects when no receipt exists."""
    app.config["TESTING"] = True

    with app.test_client() as client:
        with client.session_transaction() as session:
            session.clear()

        response = client.get("/receipt")

        assert response.status_code == 302