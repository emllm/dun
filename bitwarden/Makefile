# Makefile — zarządzanie Vaultwarden i Bitwarden CLI
#
# make login           — automatyczne logowanie do Bitwarden CLI i utworzenie session.txt
# make up/down/restart — kontrola kontenera Vaultwarden
# make populate        — załaduj przykładowe dane do sejfu
# make populate_social — załaduj dane social media z .env
# make show/show_social— wyświetl dane z sejfu
# make init-user       — utwórz domyślnego użytkownika w Vaultwarden (automatycznie po starcie)

PORT ?= 8082

# Logowanie do Bitwarden CLI (nieinteraktywne, wymaga BW_EMAIL i BW_PASSWORD w .env)
login:
	python3 login_bitwarden_cli.py

init-user:
	@if docker ps | grep -q vaultwarden; then \
	  docker cp entrypoint-init.sh vaultwarden:/data/entrypoint-init.sh; \
	  docker exec vaultwarden chmod +x /data/entrypoint-init.sh; \
	  docker exec vaultwarden /bin/sh /data/entrypoint-init.sh; \
	else \
	  echo "Vaultwarden nie działa. Uruchom najpierw: make up"; \
	fi

up:
	docker-compose --env-file .env up -d

down:
	docker-compose --env-file .env down

restart:
	$(MAKE) down
	$(MAKE) up

logs:
	docker-compose --env-file .env logs -f

status:
	docker-compose --env-file .env ps

shell:
	docker-compose --env-file .env exec vaultwarden /bin/sh

clean:
	docker-compose --env-file .env down -v
	rm -rf vw-data

show:
	@if [ -f session.txt ]; then \
	  SESSION_ID=$$(cat session.txt); \
	  bw list items --session "$$SESSION_ID" | jq '.'; \
	else \
	  echo "Brak session.txt. Zaloguj się do Bitwarden CLI i odblokuj sejf."; \
	fi

# Dodaj przykładowe dane do sejfu (intranet, gmail, outlook, github)
populate:
	@if [ -f session.txt ]; then \
	  python3 populate_bitwarden.py; \
	else \
	  echo "Brak session.txt. Zaloguj się do Bitwarden CLI i odblokuj sejf."; \
	fi

# Dodaj dane social media z .env do sejfu
populate_social:
	@if [ -f session.txt ]; then \
	  python3 populate_social_media.py; \
	else \
	  echo "Brak session.txt. Zaloguj się do Bitwarden CLI i odblokuj sejf."; \
	fi

# Wyświetl dane social media
show_social:
	@if [ -f session.txt ]; then \
	  python3 show_social_media.py; \
	else \
	  echo "Brak session.txt. Zaloguj się do Bitwarden CLI i odblokuj sejf."; \
	fi
