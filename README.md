# Trading Backend

Backend σύστημα αυτοματοποιημένων συναλλαγών (**paper trading μόνο**) στην αγορά
κρυπτονομισμάτων, με αξιοποίηση δεδομένων από κεντρικοποιημένο exchange (Binance)
και από το blockchain του Ethereum. Πτυχιακή εργασία — Τμήμα Πληροφορικής, ΑΠΘ.

> Το σύστημα **δεν εκτελεί πραγματικές συναλλαγές**. Η λειτουργία περιορίζεται σε
> προσομοίωση εκτέλεσης (paper trading) για λόγους ασφάλειας.

## Επισκόπηση

Το σύστημα συλλέγει δεδομένα αγοράς σε πραγματικό χρόνο, τα αποθηκεύει, εφαρμόζει
μια στρατηγική **mean reversion** (Bollinger Bands / z-score), αξιολογεί τη
στρατηγική με backtesting, και την εκτελεί live σε καθεστώς paper trading — όλα
εκτεθειμένα μέσω REST API.

## Αρχιτεκτονική

Το σύστημα είναι οργανωμένο σε επίπεδα, με ροή δεδομένων από τις εξωτερικές πηγές
προς την έκθεση μέσω API:

```
Εξωτερικές πηγές   ─►  Collectors        ─►  Αποθήκευση        ─►  Strategy Engine
(Binance, Ethereum)    (CEX, on-chain)       (PostgreSQL,          (κοινός πυρήνας)
                                              Redis)                     │
                                                          ┌──────────────┴──────────────┐
                                                          ▼                              ▼
                                                    Backtesting                   Paper Executor
                                                          └──────────────┬──────────────┘
                                                                         ▼
                                                                  REST API (FastAPI)
```

**Κεντρική σχεδιαστική αρχή:** το `Strategy Engine` είναι ένας **κοινός πυρήνας
καθαρής λογικής** — μια ντετερμινιστική συνάρτηση των δεδομένων, χωρίς I/O. Το ίδιο
ακριβώς αντικείμενο χρησιμοποιείται σε τρία σημεία: το endpoint σημάτων, το
backtesting, και τον live paper executor. Έτσι τα αποτελέσματα του backtest είναι
συνεπή με τη live συμπεριφορά.

## Στοίβα τεχνολογιών

- **Python 3.12**, **FastAPI**, **asyncio**
- **ccxt** (Binance REST + WebSocket), **web3.py** (Ethereum)
- **PostgreSQL** (ιστορικά δεδομένα & συναλλαγές), **Redis** (live cache/state)
- **Docker** / docker-compose

## Δομή project

```
app/
├── main.py            # FastAPI entry point
├── config.py          # ρυθμίσεις (pydantic-settings)
├── api/               # REST endpoints (health, market, onchain, strategy, backtest, paper)
├── core/              # lifespan: εκκίνηση/τερματισμός πόρων & background tasks
├── infra/             # database (Postgres), cache (Redis), repositories
├── collectors/        # CEX (Binance) & on-chain (Ethereum) συλλογή
├── models/            # domain (Pydantic) & ORM (SQLAlchemy) μοντέλα
├── strategy/          # mean reversion — ο κοινός, καθαρός πυρήνας
├── backtesting/       # engine & μετρικές αξιολόγησης
└── execution/         # paper trading executor & position store
tests/                 # σουίτα αυτοματοποιημένων tests (pytest)
```

## Εγκατάσταση & εκτέλεση

**Προαπαιτούμενο:** [Docker Desktop](https://www.docker.com/) (περιλαμβάνει Docker
Compose). Δεν χρειάζεται τοπική εγκατάσταση Python/PostgreSQL/Redis.

```bash
# 1. Ρυθμίσεις
cp .env.example .env

# 2. Εκκίνηση όλου του stack
docker compose up --build
```

Έλεγχος:
- `http://localhost:8000/health` — κατάσταση εξαρτήσεων
- `http://localhost:8000/docs` — διαδραστικό OpenAPI (Swagger UI)

### On-chain δεδομένα (προαιρετικό)

Για τη συλλογή δεδομένων Ethereum, πάρε ένα δωρεάν HTTPS endpoint από
[Infura](https://infura.io) ή [Alchemy](https://alchemy.com) και όρισέ το στο
`.env`:

```
ETH_RPC_URL=https://mainnet.infura.io/v3/<ΤΟ_ΚΛΕΙΔΙ_ΣΟΥ>
```

Αν μείνει κενό, η on-chain συλλογή απενεργοποιείται και το υπόλοιπο σύστημα τρέχει
κανονικά.

## REST API

| Method | Endpoint | Περιγραφή |
|--------|----------|-----------|
| GET  | `/health`             | Κατάσταση συνδεσιμότητας (Postgres, Redis) |
| GET  | `/market/ohlcv`       | Ιστορικά κεριά από τη βάση |
| POST | `/market/backfill`    | Άντληση & αποθήκευση ιστορικών (idempotent) |
| GET  | `/market/latest`      | Τελευταίες live τιμές (Redis) |
| GET  | `/onchain/gas`        | Πιο πρόσφατο gas/block snapshot |
| GET  | `/onchain/transfers`  | Πρόσφατες μεγάλες μεταφορές stablecoins |
| GET  | `/strategy/signal`    | Τρέχον σήμα στρατηγικής για ένα σύμβολο |
| POST | `/backtest/run`       | Backtest με μετρικές (`format=json\|csv`) |
| GET  | `/paper/positions`    | Ανοιχτές paper θέσεις (mark-to-market) |
| GET  | `/paper/trades`       | Ιστορικό κλεισμένων paper συναλλαγών |
| GET  | `/paper/summary`      | Σύνοψη realized PnL & win rate |

## Tests

Η σουίτα τρέχει **χωρίς εξωτερικές υπηρεσίες** (χρησιμοποιεί in-memory fakes):

```bash
pip install -r requirements-dev.txt
pytest
```

Καλύπτει: τον καθαρό πυρήνα στρατηγικής, τις μετρικές backtesting, την
αποκωδικοποίηση on-chain events, τις μετατροπές μοντέλων, και τη λογική του paper
executor.

## Σχεδιαστικές αρχές

- **Κοινός πυρήνας στρατηγικής:** μία υλοποίηση της λογικής, κοινή σε API,
  backtesting και live executor — εγγυάται συνέπεια backtest ≡ live.
- **Ασύγχρονη επεξεργασία:** ο φόρτος είναι I/O-bound (δίκτυο, βάση), οπότε το
  `asyncio` επιτρέπει πολλές ταυτόχρονες εργασίες χωρίς threads.
- **Διαχωρισμός αποθήκευσης:** PostgreSQL για μόνιμα/ιστορικά δεδομένα, Redis για
  πτητική live κατάσταση.
- **Idempotency:** τα σύνθετα κλειδιά και το `ON CONFLICT DO NOTHING` επιτρέπουν
  ασφαλή επανάληψη συλλογής χωρίς διπλότυπα.
- **Graceful degradation:** προαιρετικές εξαρτήσεις (on-chain) και προσωρινές
  αστοχίες δικτύου δεν ρίχνουν το σύστημα.

## Περιορισμοί & μελλοντικές επεκτάσεις

- Migrations βάσης με Alembic (αντί για `create_all` στο startup).
- Βαθύτερο ιστορικό με pagination στο REST της Binance.
- Επιπλέον στρατηγικές, dashboard, υποστήριξη DEX.
- Ενεργοποίηση σημάτων στο κλείσιμο κεριού (αντί για polling).
