import os
import subprocess
from getpass import getpass

# Pobierz dane z .env lub poproś użytkownika
BW_SERVER = os.environ.get("BW_SERVER", f"http://localhost:{os.environ.get('PORT', '8082')}")
BW_EMAIL = os.environ.get("BW_EMAIL") or input("Podaj email do Bitwarden: ")
BW_PASSWORD = os.environ.get("BW_PASSWORD") or getpass("Podaj hasło główne do Bitwarden: ")

print(f"Konfiguracja CLI Bitwarden na serwer: {BW_SERVER}")
subprocess.run(["bw", "config", "server", BW_SERVER], check=True)

print(f"Logowanie do Bitwarden jako {BW_EMAIL}...")
subprocess.run(["bw", "login", BW_EMAIL, BW_PASSWORD], check=True)

print("Odblokowywanie sejfu i zapisywanie session.txt...")
session_id = subprocess.check_output(["bw", "unlock", "--raw"], input=BW_PASSWORD.encode(), text=True)
with open("session.txt", "w") as f:
    f.write(session_id.strip())

print("Gotowe! Plik session.txt został utworzony. Możesz korzystać ze wszystkich poleceń make i skryptów Bitwarden.")
