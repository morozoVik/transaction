import logging

from src.services import investment_bank


def main():
    """
    Точка входа в приложение.
    Демонстрирует работу сервиса Инвесткопилка.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()]
    )

    transactions = [
        {"Дата операции": "2023-05-01", "Сумма операции": 1712},
        {"Дата операции": "2023-05-15", "Сумма операции": 543.21},
    ]

    print("Демонстрация работы Инвесткопилки:")
    result = investment_bank("2023-05", transactions, 50)
    print(result)


if __name__ == "__main__":
    main()
