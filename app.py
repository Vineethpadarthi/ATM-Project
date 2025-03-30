import sqlite3
import hashlib

# Database Setup
def create_database():
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        pin TEXT,
                        balance REAL DEFAULT 0.0,
                        is_admin INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        type TEXT,
                        amount REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    conn.commit()
    conn.close()

# User Registration
def register_user(username, password, pin, is_admin=0):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    hashed_pin = hashlib.sha256(pin.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password, pin, is_admin) VALUES (?, ?, ?, ?)", (username, hashed_password, hashed_pin, is_admin))
        conn.commit()
        print("User registered successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists.")
    conn.close()

# User Authentication
def authenticate_user(username, password):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT id, is_admin FROM users WHERE username=? AND password=?", (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user if user else None

# PIN Authentication
def authenticate_pin(user_id, pin):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    hashed_pin = hashlib.sha256(pin.encode()).hexdigest()
    cursor.execute("SELECT id FROM users WHERE id=? AND pin=?", (user_id, hashed_pin))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Check Balance
def check_balance(user_id):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()
    return balance

# Deposit Money
def deposit_money(user_id, amount):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)", (user_id, 'Deposit', amount))
    conn.commit()
    conn.close()
    print("Deposit successful!")

# Withdraw Money
def withdraw_money(user_id, amount):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    balance = cursor.fetchone()[0]
    if balance >= amount:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)", (user_id, 'Withdrawal', amount))
        conn.commit()
        print("Withdrawal successful!")
    else:
        print("Insufficient funds!")
    conn.close()

# Transfer Money
def transfer_money(sender_id, receiver_username, amount):
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id=?", (sender_id,))
    sender_balance = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE username=?", (receiver_username,))
    receiver = cursor.fetchone()
    if receiver and sender_balance >= amount:
        receiver_id = receiver[0]
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, sender_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, receiver_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)", (sender_id, 'Transfer Out', amount))
        cursor.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)", (receiver_id, 'Transfer In', amount))
        conn.commit()
        print("Transfer successful!")
    else:
        print("Transfer failed. Check username or balance.")
    conn.close()

# Admin Functions
def view_all_transactions():
    conn = sqlite3.connect("atm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    conn.close()
    return transactions

# Main Execution
if __name__ == "__main__":
    create_database()
    while True:
        print("\n--- ATM System ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            username = input("Enter username: ")
            password = input("Enter password: ")
            pin = input("Enter 4-digit PIN: ")
            register_user(username, password, pin)
        elif choice == "2":
            username = input("Enter username: ")
            password = input("Enter password: ")
            user = authenticate_user(username, password)
            if user:
                user_id, is_admin = user
                pin = input("Enter PIN: ")
                if authenticate_pin(user_id, pin):
                    if is_admin:
                        print("Admin Access Granted")
                        transactions = view_all_transactions()
                        for t in transactions:
                            print(t)
                    else:
                        while True:
                            print("\n1. Check Balance\n2. Deposit\n3. Withdraw\n4. Transfer\n5. Logout")
                            option = input("Choose an option: ")
                            if option == "1":
                                print("Balance:", check_balance(user_id))
                            elif option == "2":
                                amount = float(input("Enter amount to deposit: "))
                                deposit_money(user_id, amount)
                            elif option == "3":
                                amount = float(input("Enter amount to withdraw: "))
                                withdraw_money(user_id, amount)
                            elif option == "4":
                                receiver = input("Enter receiver's username: ")
                                amount = float(input("Enter amount to transfer: "))
                                transfer_money(user_id, receiver, amount)
                            elif option == "5":
                                break
                            else:
                                print("Invalid option!")
                else:
                    print("Invalid PIN!")
            else:
                print("Invalid credentials!")
        elif choice == "3":
            break
        else:
            print("Invalid choice!")
