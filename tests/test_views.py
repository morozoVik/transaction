from unittest.mock import patch

from src.views import main_page


class TestMainPage:
    """Тесты для главной функции main_page"""

    @patch("src.views.get_greeting")
    @patch("src.views.load_user_settings")
    @patch("src.views.process_transactions_data")
    @patch("src.views.get_currency_rates")
    @patch("src.views.get_stock_prices")
    def test_success(self, mock_stocks, mock_currency, mock_transactions, mock_settings, mock_greeting):
        # Настраиваем моки
        mock_greeting.return_value = "Добрый день"
        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_transactions.return_value = {
            "cards": {"1234": {"total_amount": 1000, "cashback": 10}},
            "top_transactions": [{"amount": 500}],
        }
        mock_currency.return_value = {"USD": 75.50}
        mock_stocks.return_value = {"AAPL": 170.50}

        result = main_page("2023-01-15 12:00:00")

        assert result == {
            "greeting": "Добрый день",
            "cards": {"1234": {"total_amount": 1000, "cashback": 10}},
            "top_transactions": [{"amount": 500}],
            "currency_rates": {"USD": 75.50},
            "stock_prices": {"AAPL": 170.50},
        }

    def test_invalid_date_format(self):
        result = main_page("invalid-date")
        assert "error" in result
