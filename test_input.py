import random

transactions = {}

for i in range(1, 100, 10):
    for j in range(i, i + 10):
        account_num = random.randint(1, 10)
        transactions[j] = {
            "TransactionId": str(j),
            "Account": f"account{account_num}",
            "Operation": "Deposit",
            "Amount": "10",
            "To": "None",
            "Dependency": []
        }

        if j > i + 1:
            transactions[j]["Dependency"] = list(range(i + 1, j))


def get_transaction_info(transaction_id):
    if transaction_id in transactions:
        transaction = transactions[transaction_id]
        return (
            transaction.get("Account"),
            transaction.get("Operation"),
            transaction.get("Amount"),
            transaction.get("To"),
        )
