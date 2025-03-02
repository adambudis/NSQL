# KI/LTP

# Nasazení aplikace

## 1. Požadavky před nasazením

### Systémové požadavky

- Operační systém: Linux/macOS/Windows s WSL
- Nainstalovaný **Docker** a **Docker Compose**
- Připojení k internetu pro stažení závislostí

### Předběžná konfigurace

- Ujistěte se, že máte povolený port **5000** pro Flask aplikaci a **27017** pro MongoDB.

---

## 2. Instalace a nasazení aplikace

### Nastavení proměnných prostředí

Vytvořte soubor **.env** podle příkladu **.env.example** a upravte hodnoty:

```sh
cp .env.example .env
```

Upravte soubor **.env** a nastavte správné hodnoty:

```
MONGO_USER=<your_username>
MONGO_PASSWORD=<your_password>
```

### Spuštění pomocí Docker Compose

1. Ujistěte se, že v kořenovém adresáři máte soubory `Dockerfile` a `docker-compose.yml`.
2. Spusťte sestavení a nasazení kontejnerů příkazem:

```sh
docker-compose up -d --build
```

3. Ověřte, zda jsou kontejnery běžící:

```sh
docker ps
```

Pokud je vše správně nastavené, aplikace poběží na **http://localhost:5000**.

---

## 3. Použité technologie

| Technologie    | Role                    |
| -------------- | ----------------------- |
| Flask          | Backend aplikace        |
| MongoDB        | Databázový systém       |
| Docker         | Kontejnerizace aplikace |
| Docker Compose | Správa více kontejnerů  |

---

## 4. Závislosti mezi komponentami

- **Flask** běží v kontejneru `flask`.
- **MongoDB** běží v kontejneru `mongodb`.
- Flask komunikuje s MongoDB přes síť Dockeru.
- Služba `flask` závisí na `mongodb`, což je definováno v `docker-compose.yml` pomocí `depends_on`.

---

## 5. Struktura projektu

```
.
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── requirements.txt
├── README.md
├── code/
│   ├── app.py
│   └── ... další soubory aplikace
```

---
