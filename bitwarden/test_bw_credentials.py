import subprocess
import json
import os

SESSION_FILE = os.path.join(os.path.dirname(__file__), 'session.txt')

def get_session_id():
    with open(SESSION_FILE) as f:
        return f.read().strip()

def get_credentials(domain):
    session_id = get_session_id()
    result = subprocess.run([
        "bw", "list", "items", "--search", domain, "--session", session_id
    ], capture_output=True, text=True)
    items = json.loads(result.stdout)
    if not items:
        return None
    item = items[0]
    return item['login']['username'], item['login']['password']

def test_intranet_credentials():
    creds = get_credentials("intranet")
    assert creds is not None, "Brak wpisu dla 'intranet' w sejfie Bitwarden!"
    login, password = creds
    print(f"Login: {login}\nPassword: {password}")
    assert login, "Brak loginu!"
    assert password, "Brak hasła!"

if __name__ == "__main__":
    test_intranet_credentials()
