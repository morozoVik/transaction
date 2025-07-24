import json
import os
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.utils import get_currency_rates, get_greeting, get_stock_prices, load_user_settings, process_transactions_data


class TestGetGreeting:
    """Тесты для функции get_greeting"""

    @pytest.mark.parametrize(
        "time_str, expected",
        [
            ("2023-01-01 06:00:00", "Доброе утро"),
            ("2023-01-01 12:00:00", "Добрый день"),
            ("2023-01-01 18:00:00", "Добрый вечер"),
            ("2023-01-01 00:00:00", "Доброй ночи"),
        ],
    )
    def test_get_greeting(self, time_str, expected):
        assert get_greeting(time_str) == expected

    def test_invalid_format(self):
        result = get_greeting("invalid-date")
        assert result == "Добрый день"


class TestLoadUserSettings:
    """Тесты для функции load_user_settings"""

    def test_load_settings(self, tmp_path):
        # Создаем временный файл настроек
        settings = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}
        settings_file = tmp_path / "user_settings.json"
        settings_file.write_text(json.dumps(settings), encoding="utf-8")

        # Временная замена функции для использования тестового файла
        original_func = load_user_settings
        try:
            import sys

            from src.utils import load_user_settings as original_load

            sys.modules["src.utils"].load_user_settings = lambda: json.loads(settings_file.read_text(encoding="utf-8"))

            result = original_load()
            assert result == settings
        finally:
            # Восстанавливаем оригинальную функцию
            sys.modules["src.utils"].load_user_settings = original_func

    def test_missing_file(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = load_user_settings()
        assert result == {"user_currencies": [], "user_stocks": []}


class TestGetCurrencyRates:
    """Тесты для функции get_currency_rates"""

    @patch("requests.get")
    def test_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"Valute": {"USD": {"Value": 75.50}, "EUR": {"Value": 89.20}}}
        mock_get.return_value = mock_response

        result = get_currency_rates(["USD", "EUR"])
        assert result == {"USD": 75.50, "EUR": 89.20}

    @patch("requests.get", side_effect=Exception("API error"))
    def test_api_error(self, mock_get):
        result = get_currency_rates(["USD", "EUR"])
        assert result == {"USD": 0.0, "EUR": 0.0}


class TestGetStockPrices:
    """Тесты для функции get_stock_prices"""

    @patch("requests.get")
    @patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": "test-key"})
    def test_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"Global Quote": {"05. price": "170.50"}}
        mock_get.return_value = mock_response

        result = get_stock_prices(["AAPL"])
        assert result == {"AAPL": 170.50}

    @patch("requests.get", side_effect=Exception("API error"))
    def test_api_error(self, mock_get):
        result = get_stock_prices(["AAPL"])
        assert result == {"AAPL": 0.0}


class TestProcessTransactionsData:
    """Тесты для функции process_transactions_data"""

    @patch("pandas.read_excel")
    def test_success(self, mock_read_excel):
        # Создаем тестовые данные
        test_data = {
            "Дата операции": pd.to_datetime(["2023-01-10", "2023-01-12", "2023-01-14"]),
            "Номер карты": ["1234567890", "1234567890", "9876543210"],
            "Сумма платежа": [1000, 500, 2000],
            "Описание": ["Магазин", "Кафе", "Техника"],
            "Категория": ["Продукты", "Ресторан", "Электроника"],
        }
        test_df = pd.DataFrame(test_data)

        # Мокируем read_excel
        mock_read_excel.return_value = test_df

        # Вызываем тестируемую функцию
        result = process_transactions_data("2023-01-15 12:00:00")

        # Проверяем результаты
        assert isinstance(result, dict)
        assert "cards" in result
        assert "top_transactions" in result

        # Проверяем данные по картам
        assert len(result["cards"]) == 2  # Две карты
        assert "7890" in result["cards"]  # Последние 4 цифры первой карты
        assert "3210" in result["cards"]  # Последние 4 цифры второй карты
        assert result["cards"]["7890"]["total_amount"] == 1500  # 1000 + 500
        assert result["cards"]["7890"]["cashback"] == 15  # 1500 / 100

        # Проверяем топ транзакций
        assert len(result["top_transactions"]) == 3  # Всего 3 транзакции
        assert result["top_transactions"][0]["amount"] == 2000  # Самая большая транзакция
        assert result["top_transactions"][0]["description"] == "Техника"

    @patch("pandas.read_excel", side_effect=Exception("File error"))
    def test_file_error(self, mock_read_excel):
        result = process_transactions_data("2023-01-15 12:00:00")
        assert result == {"cards": {}, "top_transactions": []}
