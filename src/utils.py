import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_greeting(time_str: str) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.
    """
    try:
        hour = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").hour
        if 5 <= hour < 12:
            return "Доброе утро"
        elif 12 <= hour < 17:
            return "Добрый день"
        elif 17 <= hour < 23:
            return "Добрый вечер"
        else:
            return "Доброй ночи"
    except ValueError as e:
        logging.error(f"Ошибка определения приветствия: {e}")
        return "Добрый день"


def load_user_settings() -> Dict[str, List[str]]:
    """
    Загружает пользовательские настройки из user_settings.json.
    """
    default = {"user_currencies": [], "user_stocks": []}
    try:
        with open("user_settings.json", "r", encoding="utf-8") as f:
            return {**default, **json.load(f)}
    except Exception as e:
        logging.error(f"Ошибка загрузки настроек: {e}")
        return default


def get_currency_rates(currencies: List[str]) -> Dict[str, Optional[float]]:
    """
    Получает курсы валют через API Центробанка.
    """
    if not currencies:
        return {}

    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        response.raise_for_status()
        data = response.json()
        return {curr: data["Valute"][curr]["Value"] for curr in currencies if curr in data["Valute"]}
    except Exception as e:
        logging.error(f"Ошибка получения курсов: {e}")
        return {curr: 0.0 for curr in currencies}


def get_stock_prices(stocks: List[str]) -> Dict[str, Optional[float]]:
    """
    Получает цены акций через Alpha Vantage API.
    """
    if not stocks:
        return {}

    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        logging.error("API ключ не найден")
        return {stock: 0.0 for stock in stocks}

    prices = {}
    for stock in stocks:
        try:
            params = {"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": API_KEY}
            response = requests.get("https://www.alphavantage.co/query", params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            prices[stock] = float(data["Global Quote"]["05. price"])
            time.sleep(12)  # Соблюдаем лимит API
        except Exception as e:
            logging.error(f"Ошибка получения цены {stock}: {e}")
            prices[stock] = 0.0

    return prices


def process_transactions_data(date_str: str) -> Optional[Dict[str, Any]]:
    """Обрабатывает данные транзакций за период с начала месяца до указанной даты."""
    try:
        end_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_date = end_date.replace(day=1)

        # Чтение Excel с указанием используемых колонок
        df = pd.read_excel(
            "data/operations.xlsx", usecols=["Дата операции", "Номер карты", "Сумма платежа", "Категория", "Описание"]
        )

        # Преобразование дат с явным указанием формата
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True)

        # Фильтрация по дате (с начала месяца до указанной даты)
        period_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

        # Обработка данных по картам
        cards_data = {}
        for card, group in period_df.groupby("Номер карты"):
            # Берем абсолютное значение суммы (так как в файле они отрицательные)
            total = group["Сумма платежа"].abs().sum()
            last_4_digits = str(card).strip("*")[-4:]  # Извлекаем последние 4 цифры
            cards_data[last_4_digits] = {"total_amount": round(total, 2), "cashback": int(total // 100)}  # 1% кэшбэка

        # Топ-5 транзакций по сумме (по модулю)
        top_trans = (
            period_df.assign(abs_amount=period_df["Сумма платежа"].abs()).nlargest(5, "abs_amount").to_dict("records")
        )

        return {
            "cards": cards_data,
            "top_transactions": [
                {
                    "description": t["Описание"],
                    "amount": abs(t["Сумма платежа"]),  # Положительная сумма
                    "date": t["Дата операции"].strftime("%Y-%m-%d %H:%M:%S"),
                    "category": t["Категория"],
                }
                for t in top_trans
            ],
        }
    except Exception as e:
        logging.error(f"Ошибка обработки транзакций: {e}")
        return {"cards": {}, "top_transactions": []}


def validate_transaction(transaction: Dict[str, Any]) -> bool:
    """
    Проверяет валидность структуры и данных транзакции.
    """
    try:
        if not isinstance(transaction, dict):
            return False

        required = {"Дата операции", "Сумма операции"}
        if not all(key in transaction for key in required):
            return False

        datetime.strptime(transaction["Дата операции"], "%Y-%m-%d")
        float(transaction["Сумма операции"])
        return True

    except (ValueError, TypeError):
        return False


def filter_by_month(transactions: List[Dict[str, Any]], month: str) -> List[Dict[str, Any]]:
    """
    Фильтрует транзакции по указанному месяцу.
    """
    try:
        year, month = map(int, month.split("-"))
        return [
            t
            for t in transactions
            if validate_transaction(t)
            and datetime.strptime(t["Дата операции"], "%Y-%m-%d").year == year
            and datetime.strptime(t["Дата операции"], "%Y-%m-%d").month == month
        ]
    except ValueError:
        return []
