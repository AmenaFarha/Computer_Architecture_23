class SimpleBank:
    def __init__(self, filename):
        self.balances = {}
        self.load_balances_from_file(filename)

    def load_balances_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                for line in file:
                    account, balance_str = line.strip().split()
                    balance = int(balance_str)
                    self.balances[account] = balance
        except FileNotFoundError:
            print(f"File {filename} not found. Starting with empty balances.")

    def execute_transaction(self, account, action, amount, to_account):
        if action == 'Deposit':
            result = self.deposit(account, amount)
            return result
        elif action == 'Withdraw':
            result = self.withdraw(account, amount)
            return result
        elif action == 'Transfer':
            result = self.transfer(account, to_account, amount)
            return result
        else:
            print(f"Unsupported action: {action}")

    def deposit(self, account, amount):
        assert amount > 0, "Deposit amount must be greater than 0"
        assert account in self.balances, "Account not found"
        return True

    def withdraw(self, account, amount):
        assert amount > 0, "Withdrawal amount must be greater than 0"
        assert account in self.balances, "Account not found"
        assert self.balances[account] >= amount, "Insufficient funds"
        return True

    def transfer(self, from_account, to_account, amount):
        assert from_account in self.balances, "Sender account not found"
        assert to_account in self.balances, "Recipient account not found"
        assert amount > 0, "Transfer amount must be greater than 0"
        assert self.balances[from_account] >= amount, "Insufficient funds"
        return True
    
    
    def committ_transaction(self, account, action, amount, to_account):
        if action == 'Deposit':
            self.balances[account] += amount
        elif action == 'Withdraw':
            self.balances[account] -= amount
        elif action == 'Transfer':
            self.balances[account] -= amount
            self.balances[to_account] += amount
        else:
            print(f"Unsupported action: {action}")

        # Use the same filename for reading and writing
        filename = "balan.txt"
        with open(filename, "w") as output_file:
            for account, balance in self.balances.items():
                output_file.write(f"{account} {balance}\n")
