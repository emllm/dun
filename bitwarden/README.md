# Bitwarden (Vaultwarden) – Dokumentacja lokalnej usługi

Ten folder zawiera instrukcje do uruchomienia lokalnej usługi Bitwarden (Vaultwarden) w kontenerze Docker oraz przykłady integracji z Pythonem do pobierania loginów i haseł.

## 1. Plik `.env` i domyślna konfiguracja

W folderze znajduje się plik `.env` z domyślnymi wartościami środowiskowymi dla Vaultwarden:

- `PORT=8082` – port na którym działa Vaultwarden (domyślnie 8082)
- `ADMIN_TOKEN=admin1234` – token administratora (do panelu admin: `/admin`)
- `BW_EMAIL=test@example.com` – przykładowy email użytkownika testowego
- `BW_PASSWORD=Test123456789` – przykładowe hasło główne użytkownika testowego

Możesz zmienić te wartości przed uruchomieniem docker-compose.

## 2. Uruchomienie usługi Vaultwarden

Vaultwarden to lekka, zgodna z Bitwarden alternatywa open source, idealna do testów lokalnych.

### Krok 1: Uruchomienie kontenera

```bash
cd bitwarden
# Uruchom usługę w tle
docker-compose --env-file .env up -d
```

Panel logowania będzie dostępny pod adresem: [http://localhost:8082](http://localhost:8082)
Panel administratora: [http://localhost:8082/admin](http://localhost:8082/admin)

### Krok 2: Utwórz konto administratora lub użyj domyślnego

**Po starcie kontenera Vaultwarden zalecana jest automatyzacja:**

```bash
make up
make init-user   # tworzy domyślnego użytkownika z BW_EMAIL/BW_PASSWORD
make login       # logowanie przez CLI/skrypt
make populate    # opcjonalnie: załaduj przykładowe dane
make show        # podgląd wpisów
```

Domyślny użytkownik (`BW_EMAIL`/`BW_PASSWORD` z .env) zostanie utworzony automatycznie przez `make init-user`. Te zmienne są przekazywane do kontenera Vaultwarden przez `docker-compose.yml` i wykorzystywane przez skrypt `entrypoint-init.sh`. Nie musisz tworzyć konta ręcznie przez WWW, chyba że chcesz inne dane.

---

### Resetowanie środowiska i naprawa błędów uprawnień

Jeśli pojawi się błąd `'ContainerConfig'` lub inne problemy z uprawnieniami/kontenerem:

```bash
docker compose down
sudo rm -rf vw-data
make up
make init-user
```

**Nie używaj chmod na vw-data!**
Uprawnieniami zarządza Docker i ręczna zmiana może uszkodzić wolumin.

---

## 3. Logowanie do Bitwarden CLI i odblokowanie sejfu

**UWAGA:** Wszystkie skrypty wymagają aktywnego pliku `session.txt` (odblokowany sejf przez CLI Bitwarden). Jeśli go nie ma, zobaczysz komunikat o błędzie!

### Automatyczne logowanie i utworzenie session.txt

Możesz użyć automatycznego skryptu lub polecenia:

```bash
make login
```

**UWAGA:** Od teraz logowanie CLI jest w pełni nieinteraktywne — skrypt korzysta wyłącznie z danych w `.env` (`BW_EMAIL`, `BW_PASSWORD`). Jeśli nie są ustawione, skrypt zakończy się błędem i wyświetli czytelny komunikat.

Zmienne środowiskowe:
- `BW_SERVER` — adres serwera Bitwarden (domyślnie `http://localhost:8082`)
- `BW_EMAIL` — email do konta Bitwarden (musi być ustawiony w .env)
- `BW_PASSWORD` — hasło główne (musi być ustawione w .env)

---

Możesz też wykonać ręcznie:

```bash
bw config server http://localhost:8082  # lub inny port z .env
bw login test@example.com Test123456789      # lub własne dane
bw unlock --raw > session.txt           # zapisuje session_id do pliku
```

## 4. Automatyczne dodawanie przykładowych danych

Aby dodać przykładowe dane logowania do popularnych serwisów (intranet, gmail, outlook, github):

```bash
make populate
```

Aby dodać dane social media z .env (facebook, twitter, linkedin):

```bash
make populate_social
```

## 5. Przeglądanie danych z sejfu

Aby wyświetlić wszystkie wpisy:

```bash
make show
```

Aby wyświetlić tylko dane social media:

```bash
make show_social
```

## 6. Automatyczne dodawanie przykładowych danych

Aby dodać przykładowe dane logowania do popularnych serwisów (intranet, gmail, outlook, github), użyj skryptu:

```bash
# Najpierw zaloguj się przez CLI i odblokuj sejf:
npm install -g @bitwarden/cli
```

### Krok 1: Zaloguj się do CLI
```bash
bw config server http://localhost:8082
bw login <email> <master_password>
# Odblokuj sejf i pobierz session_id
bw unlock --raw > session.txt
```

### Krok 2: Pobierz dane do logowania przez Python

```python
import subprocess
import json

with open('session.txt') as f:
    session_id = f.read().strip()

def get_credentials(domain):
    result = subprocess.run([
        "bw", "list", "items", "--search", domain, "--session", session_id
    ], capture_output=True, text=True)
    items = json.loads(result.stdout)
    if not items:
        return None
    item = items[0]
    return item['login']['username'], item['login']['password']

login, password = get_credentials("intranet")
print("Login:", login)
print("Password:", password)
```

## 3. Testowanie

- Dodaj wpis do sejfu z URL: `https://intranet`, loginem i hasłem.
- Uruchom powyższy skrypt – powinien wypisać login i hasło.

## 4. Pliki w folderze

- `docker-compose.yml` – konfiguracja Vaultwarden
- `test_bw_credentials.py` – przykładowy test integracyjny
- `session.txt` – plik z session_id po odblokowaniu sejfu (nie commituj do repo!)

---

**Uwaga:** Vaultwarden to projekt społecznościowy, nieoficjalny. Do produkcji zalecany jest oryginalny Bitwarden.
