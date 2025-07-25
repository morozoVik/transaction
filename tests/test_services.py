import json
import logging
from typing import Any, Dict, List

import pytest

from src.services import investment_bank


@pytest.fixture
def valid_transactions() -> List[Dict[str, Any]]:
    return [
        {"Дата операции": "2023-05-01", "Сумма операции": 1712},
        {"Дата операции": "2023-05-15", "Сумма операции": 543.21},
        {"Дата операции": "2023-05-30", "Сумма операции": 399.50},
    ]


def test_normal_case(valid_transactions: List[Dict[str, Any]]):
    """Тест основного функционала сервиса"""
    result = investment_bank("2023-05", valid_transactions, 50)
    data = json.loads(result)

    assert data["month"] == "2023-05"
    assert data["limit"] == 50
    assert data["total_saved"] == pytest.approx(45.29)


@pytest.mark.parametrize(
    "month,limit,expected",
    [
        ("2023-05", 10, 15.29),
        ("2023-05", 100, 145.29),
        ("2023-06", 50, 0.0),
    ],
)
def test_with_parameters(month: str, limit: int, expected: float, valid_transactions: List[Dict[str, Any]]):
    """Параметризованные тесты разных сценариев"""
    result = investment_bank(month, valid_transactions, limit)
    assert json.loads(result)["total_saved"] == pytest.approx(expected)


def test_invalid_month_format():
    """Тест невалидного формата месяца"""
    with pytest.raises(ValueError, match="Неверный формат месяца"):
        investment_bank("2023", [], 50)


def test_invalid_limit_value():
    """Тест отрицательного лимита"""
    with pytest.raises(ValueError, match="Лимит округления должен быть > 0"):
        investment_bank("2023-05", [], -10)


def test_logging_output(caplog: pytest.LogCaptureFixture, valid_transactions: List[Dict[str, Any]]):
    """Тест вывода логов"""
    with caplog.at_level(logging.INFO):
        investment_bank("2023-05", valid_transactions, 50)

    assert "Запуск расчета для 2023-05" in caplog.text
    assert "Итого накоплено: 45.29 руб." in caplog.text
