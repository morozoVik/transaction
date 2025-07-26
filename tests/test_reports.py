import json

import pandas as pd
import pytest

from src.reports import get_spending_by_weekday_report, report_to_file, report_to_file_with_name, spending_by_weekday


@pytest.fixture
def sample_transactions():
    """Фикстура с тестовыми транзакциями."""
    return pd.DataFrame(
        {
            "Дата операции": [
                "01.01.2023 12:00:00",  # Воскресенье
                "02.01.2023 12:00:00",  # Понедельник
                "03.01.2023 12:00:00",  # Вторник
                "10.01.2023 12:00:00",  # Вторник
                "15.01.2023 12:00:00",  # Воскресенье
                "20.02.2023 12:00:00",  # Понедельник
                "25.02.2023 12:00:00",  # Суббота
                "01.03.2023 12:00:00",  # Среда
                "10.03.2023 12:00:00",  # Пятница
                "15.03.2023 12:00:00",  # Среда
            ],
            # Делаем суммы отрицательными (траты)
            "Сумма платежа": [-100, -200, -300, -400, -500, -600, -700, -800, -900, -1000],
        }
    )


class TestSpendingAnalysis:
    """Тесты анализа трат по дням недели"""

    def test_spending_by_weekday(self, sample_transactions):
        """Тест корректного расчета средних трат."""
        result = spending_by_weekday(sample_transactions, "2023-03-15")

        expected_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        assert all(day in result for day in expected_days)

        assert result["Понедельник"] == pytest.approx(400.0)
        assert result["Среда"] == pytest.approx(800.0)
        assert result["Четверг"] == pytest.approx(0.0)  # Нет данных

    @pytest.mark.parametrize(
        "date,expected", [(None, "current date"), ("2023-03-15", "specified date"), ("invalid-date", "error handling")]
    )
    def test_spending_parametrized(self, sample_transactions, date, expected):
        """Параметризованный тест для разных входных данных."""
        result = spending_by_weekday(sample_transactions, date)
        assert isinstance(result, dict)
        assert len(result) == 7


class TestReportDecorators:
    """Тесты декораторов отчетов"""

    def test_report_to_file(self, tmp_path, sample_transactions):
        """Тест декоратора report_to_file."""
        test_file = tmp_path / "test_report.json"

        @report_to_file
        def test_func(data, output_file=None, **kwargs):
            return {"result": "test"}

        test_func(sample_transactions, output_file=str(test_file))
        assert test_file.exists()

    def test_report_to_file_with_name(self, tmp_path, sample_transactions):
        """Тест декоратора с указанием имени файла."""
        test_file = tmp_path / "custom_report.json"

        @report_to_file_with_name(str(test_file))
        def test_func(data, **kwargs):
            return {"result": "named_test"}

        test_func(sample_transactions)
        assert test_file.exists()


class TestFullReport:
    """Тесты полного цикла формирования отчета"""

    def test_get_spending_report(self, tmp_path, sample_transactions):
        """Тест формирования и сохранения отчета."""
        test_file = tmp_path / "full_report.json"
        result = get_spending_by_weekday_report(sample_transactions, output_file=str(test_file))

        assert test_file.exists()
        with open(test_file, "r", encoding="utf-8") as f:
            assert json.load(f) == result
