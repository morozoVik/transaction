import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional

import pandas as pd

from src.utils import parse_date, save_to_json, validate_dataframe

logger = logging.getLogger(__name__)


def report_to_file(func: Callable) -> Callable:
    """
    Декоратор для сохранения результата функции в JSON-файл.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        output_file = kwargs.pop("output_file", f"{func.__name__}_report.json")
        result = func(*args, **kwargs)
        save_to_json(result, output_file)
        logger.info(f"Отчет сохранен в файл: {output_file}")
        return result

    return wrapper


def report_to_file_with_name(filename: str) -> Callable:
    """
    Декоратор с параметром для сохранения результата в указанный файл.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs["output_file"] = filename
            result = func(*args, **kwargs)
            save_to_json(result, filename)
            return result

        return wrapper

    return decorator


def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> Dict[str, float]:
    """
    Анализирует средние траты по дням недели за последние 3 месяца.
    """
    weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    analysis_date = parse_date(date) or datetime.now()
    three_months_ago = analysis_date - timedelta(days=90)

    if not validate_dataframe(transactions, {"Дата операции", "Сумма платежа"}):
        logger.warning("Невалидный DataFrame")
        return {day: 0.0 for day in weekdays}

    try:
        df = transactions.copy()
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True)

        period_df = df[
            (df["Дата операции"] >= three_months_ago)
            & (df["Дата операции"] <= analysis_date)
            & (df["Сумма платежа"] < 0)
        ].copy()

        period_df["День недели"] = period_df["Дата операции"].dt.day_name("ru_RU")
        period_df["Сумма"] = period_df["Сумма платежа"].abs()

        avg_spending = period_df.groupby("День недели")["Сумма"].mean().round(2)
        return {day: float(avg_spending.get(day, 0.0)) for day in weekdays}

    except Exception as e:
        logger.error(f"Ошибка анализа трат: {e}")
        return {day: 0.0 for day in weekdays}


@report_to_file
def get_spending_by_weekday_report(
    transactions: pd.DataFrame, date: Optional[str] = None, **kwargs: Any
) -> Dict[str, float]:
    """
    Генерирует и сохраняет отчет о средних тратах по дням недели.
    """
    return spending_by_weekday(transactions, date)
