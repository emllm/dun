PORT ?= 8082

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
