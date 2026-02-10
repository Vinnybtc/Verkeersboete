# Verkeersboete AI Agent

Autonome AI-agent voor het analyseren van Nederlandse verkeersboetes (CJIB-beschikkingen) en het genereren van bezwaarschriften op basis van de Wet Mulder (Wahv).

## Architectuur

```
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Core business logic
│   │   │   ├── ocr_service.py      # OCR & document parsing
│   │   │   ├── legal_agent.py      # Legal analysis engine
│   │   │   └── pdf_generator.py    # Bezwaarschrift PDF generation
│   │   └── templates/    # Jinja2 HTML templates
│   ├── alembic/          # Database migrations
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   └── src/
│       ├── app/          # Next.js app router pages
│       └── components/   # React components
└── docker-compose.yml
```

## Modules

### Module A: Document Intake & OCR
Accepteert JPEG, PNG, TIFF en PDF documenten. Extraheert tekst via Tesseract OCR (of Google Cloud Vision) en gebruikt Claude om gestructureerde velden te herkennen:
- Beschikkingsnummer, datum overtreding, feitcode, locatie, bedrag, instantie

### Module B: Juridische Analyse Engine
Analyseert de boete-data tegen bekende bezwaargronden onder de Wahv:
- Flitsfouten en margeberekening
- Bebording en wegmarkering
- Formele gebreken in de beschikking
- Trajectcontrole-verweer
- Parkeerboete-verweer
- Procedurefouten

### Module C: Bezwaarschrift Generator
Genereert een formeel PDF-document gericht aan de Officier van Justitie (Parket CVOM) met juridische onderbouwing en verzoek om proceskostenvergoeding.

## Vereisten

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Tesseract OCR met Nederlandse taaldata (`tesseract-ocr-nld`)
- Anthropic API key (Claude)

## Installatie

### Met Docker (aanbevolen)

```bash
# Kopieer en configureer environment
cp backend/.env.example backend/.env
# Vul uw ANTHROPIC_API_KEY in

# Start alle services
docker-compose up --build
```

### Handmatig

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configureer .env
uvicorn app.main:app --reload

# Frontend (in een andere terminal)
cd frontend
npm install
npm run dev
```

## Gebruik

1. Open `http://localhost:3000`
2. Registreer en onderteken de machtiging
3. Upload een foto of PDF van uw CJIB-boete
4. De agent analyseert automatisch de boete en genereert een bezwaarschrift

## API Endpoints

| Methode | Endpoint | Beschrijving |
|---------|----------|-------------|
| POST | `/api/users` | Registreer gebruiker |
| POST | `/api/users/authorize` | Onderteken machtiging |
| POST | `/api/upload-fine` | Upload boete-document |
| POST | `/api/process-fine` | Volledige analyse pipeline |
| GET | `/api/cases/{id}` | Zaak details ophalen |
| GET | `/api/users/{id}/cases` | Alle zaken van gebruiker |
| PATCH | `/api/cases/{id}/status` | Status bijwerken |

Interactieve API-documentatie: `http://localhost:8000/docs`

## Disclaimer

Dit is een hulpmiddel en geen vervanging voor professioneel juridisch advies. Raadpleeg een advocaat voor persoonlijke begeleiding.
