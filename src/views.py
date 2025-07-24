import logging
from datetime import datetime
from typing import Any, Dict

from .utils import get_currency_rates, get_greeting, get_stock_prices, load_user_settings, process_transactions_data


def main_page(date_time_str: str) -> Dict[str, Any]:
    """
    Основная функция для страницы "Главная".
    """
    try:
        # Валидация входных данных
        datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

        result = {
            "greeting": get_greeting(date_time_str),
            **process_transactions_data(date_time_str),
            "currency_rates": get_currency_rates(load_user_settings().get("user_currencies", [])),
            "stock_prices": get_stock_prices(load_user_settings().get("user_stocks", [])),
        }

        return result
    except ValueError as e:
        logging.error(f"Неверный формат даты: {date_time_str}. Ошибка: {e}")
        return {"error": "Неверный формат даты. Используйте YYYY-MM-DD HH:MM:SS"}
    except Exception as e:
        logging.error(f"Ошибка в main_page: {e}")
        return {"error": "Внутренняя ошибка сервера"}
