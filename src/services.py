import json
import logging
from datetime import datetime
from typing import Any, Dict, List


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> str:
    """
    Основная функция сервиса 'Инвесткопилка' для расчета накоплений через округление транзакций.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Запуск расчета для {month} с лимитом {limit}")

    # Валидация входных данных
    try:
        target_year, target_month = map(int, month.split("-"))
        datetime.strptime(month, "%Y-%m")
    except ValueError as e:
        error_msg = f"Неверный формат месяца: {month}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    if limit <= 0:
        error_msg = f"Лимит округления должен быть > 0, получено: {limit}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Расчет накоплений
    total_saved = 0.0
    for transaction in transactions:
        try:
            if not all(key in transaction for key in ["Дата операции", "Сумма операции"]):
                continue

            trans_date = datetime.strptime(transaction["Дата операции"], "%Y-%m-%d")
            if trans_date.year == target_year and trans_date.month == target_month:
                amount = float(transaction["Сумма операции"])
                if amount <= 0:
                    continue

                # Точный расчет округления с учетом дробных частей
                rounded = ((amount // limit) + 1) * limit if amount % limit != 0 else amount
                difference = rounded - amount
                if difference > 0:
                    total_saved += difference
                    logger.debug(f"Округление: {amount} → {rounded} (+{difference})")

        except (ValueError, TypeError) as e:
            logger.warning(f"Пропуск невалидной транзакции: {transaction}. Ошибка: {e}")
            continue

    # Формирование результата
    result = {"month": month, "limit": limit, "total_saved": round(total_saved, 2)}

    logger.info(f"Итого накоплено: {result['total_saved']:.2f} руб.")
    return json.dumps(result, ensure_ascii=False, indent=2)
