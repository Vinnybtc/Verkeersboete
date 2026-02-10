"""
Legal Analysis Engine based on the Wet Mulder (Wahv).

Analyzes extracted traffic fine data and identifies legal grounds for appeal
(bezwaar/beroep) under Dutch administrative traffic law.
"""

import json
import logging
import re
from typing import Optional

from anthropic import Anthropic

from app.config import settings
from app.schemas.schemas import FineExtracted

logger = logging.getLogger(__name__)

# Known feitcodes and their common appeal grounds
FEITCODE_CATEGORIES = {
    # Speed violations (flitsboetes)
    "VA": "snelheidsovertreding",
    "VB": "snelheidsovertreding",
    "VC": "snelheidsovertreding",
    # Red light violations
    "R": "roodlichtovertreding",
    # Parking violations
    "K": "parkeerovertreding",
    "F": "parkeerovertreding",
    # Seatbelt / phone violations
    "E": "gordelovertreding",
    "D": "telefoongebruik",
}

SYSTEM_PROMPT = """Je bent een ervaren Nederlandse advocaat gespecialiseerd in verkeersrecht en de Wet administratiefrechtelijke handhaving verkeersvoorschriften (Wahv), ook bekend als de Wet Mulder.

Je taak is om verkeersboetes (CJIB-beschikkingen) te analyseren en juridische gronden voor bezwaar te identificeren.

Je kent de volgende juridische bezwaargronden:

1. FORMELE GEBREKEN:
   - Onjuiste tenaamstelling van de beschikking
   - Beschikking niet binnen 4 maanden na overtreding verzonden (art. 4 lid 2 Wahv)
   - Ontbrekende of onjuiste vermeldingen (feitcode, locatie, datum, tijd)
   - Gebrekkige motivering van de beschikking

2. SNELHEIDSMETINGEN (Flitsboetes):
   - Meetonnauwkeurigheid: wettelijke marge niet correct toegepast (3 km/h bij <100 km/h, 3% bij >100 km/h)
   - IJkrapport van de meetapparatuur niet geldig of verlopen
   - Verkeerd ingestelde snelheidslimiet in het systeem
   - Tijdelijke snelheidsbeperking niet correct aangegeven met bebording

3. BEBORDING EN WEGMARKERING:
   - Onduidelijke of ontbrekende verkeersborden
   - Tegenstrijdige bebording
   - Verkeersbord niet conform BABW (Besluit administratieve bepalingen inzake het wegverkeer)
   - Bord buiten de wettelijke plaatsingsrichtlijnen

4. KENTEKEN EN VOERTUIG:
   - Voertuig was niet in bezit van betrokkene ten tijde van overtreding
   - Gestolen voertuig
   - Kentekenplaat niet leesbaar of verwisseld

5. TRAJECTCONTROLE:
   - Betrokkene niet staande gehouden (relevant voor verweer)
   - Technische gebreken in het trajectcontrolesysteem
   - Berekening gemiddelde snelheid onjuist

6. PARKEERBOETES:
   - Onduidelijke parkeerzone-aanduiding
   - Defecte parkeerautomaat
   - Betrokkene was kort gestopt (laden/lossen)
   - Onvoldoende parkeerplaatsen beschikbaar (in sommige gevallen)

7. PROCEDUREFOUT:
   - Betrokkene niet in de gelegenheid gesteld te worden gehoord
   - Bezwaartermijn onjuist vermeld
   - Administratieve fouten in de procedure

Geef je analyse in het volgende JSON-formaat:
{
    "bezwaargronden": [
        {
            "grond": "Naam van de bezwaargrond",
            "toelichting": "Uitleg waarom deze grond van toepassing kan zijn",
            "wettelijke_basis": "Relevante wetsartikelen",
            "sterkte": "sterk/gemiddeld/zwak"
        }
    ],
    "slagingskans": 0.0,  // Geschatte slagingskans als percentage (0.0 tot 1.0)
    "samenvatting": "Korte samenvatting van de analyse",
    "aanbeveling": "Concreet advies over wel of niet bezwaar maken"
}

Wees eerlijk en realistisch over de slagingskans. Niet elke boete is succesvol aan te vechten.
Geef ALLEEN het JSON-object terug, zonder extra tekst."""


def determine_violation_category(feitcode: Optional[str]) -> str:
    """Determine the violation category based on the feitcode prefix."""
    if not feitcode:
        return "onbekend"
    for prefix, category in FEITCODE_CATEGORIES.items():
        if feitcode.upper().startswith(prefix):
            return category
    return "overig"


def analyze_fine(extracted_data: FineExtracted, raw_ocr_text: str = "") -> dict:
    """
    Perform legal analysis on extracted fine data.

    Uses Claude to analyze the fine against known legal grounds for appeal
    under the Wet Mulder (Wahv).

    Returns:
        Dictionary with legal analysis results including grounds for appeal,
        success probability, and recommendations.
    """
    client = Anthropic(api_key=settings.anthropic_api_key)

    category = determine_violation_category(extracted_data.feitcode)

    user_prompt = f"""Analyseer de volgende verkeersboete en identificeer mogelijke bezwaargronden:

**Beschikkingsnummer:** {extracted_data.beschikkingsnummer or "Onbekend"}
**Datum overtreding:** {extracted_data.overtreding_datum or "Onbekend"}
**Feitcode:** {extracted_data.feitcode or "Onbekend"}
**Categorie:** {category}
**Omschrijving:** {extracted_data.omschrijving or "Onbekend"}
**Locatie:** {extracted_data.locatie or "Onbekend"}
**Bedrag:** €{extracted_data.bedrag or "Onbekend"}
**Instantie:** {extracted_data.instantie or "Onbekend"}

{"Aanvullende OCR-tekst van de beschikking:" + chr(10) + raw_ocr_text[:2000] if raw_ocr_text else ""}

Analyseer deze boete en geef je juridische beoordeling."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = response.content[0].text.strip()

    # Parse JSON from response
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if not json_match:
        logger.error(f"Could not extract JSON from legal analysis: {response_text}")
        return {
            "bezwaargronden": [],
            "slagingskans": 0.0,
            "samenvatting": "Analyse kon niet worden uitgevoerd.",
            "aanbeveling": "Neem contact op met een verkeersrecht advocaat.",
        }

    try:
        analysis = json.loads(json_match.group())
        # Validate expected keys
        analysis.setdefault("bezwaargronden", [])
        analysis.setdefault("slagingskans", 0.0)
        analysis.setdefault("samenvatting", "")
        analysis.setdefault("aanbeveling", "")
        return analysis
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse legal analysis JSON: {e}")
        return {
            "bezwaargronden": [],
            "slagingskans": 0.0,
            "samenvatting": "Er is een fout opgetreden bij de analyse.",
            "aanbeveling": "Neem contact op met een verkeersrecht advocaat.",
        }


def format_legal_grounds(analysis: dict) -> str:
    """Format the legal analysis into a readable text summary."""
    lines = []
    lines.append("=" * 60)
    lines.append("JURIDISCHE ANALYSE - VERKEERSBOETE")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"Samenvatting: {analysis.get('samenvatting', 'N/A')}")
    lines.append(f"Geschatte slagingskans: {analysis.get('slagingskans', 0) * 100:.0f}%")
    lines.append("")

    grounds = analysis.get("bezwaargronden", [])
    if grounds:
        lines.append("BEZWAARGRONDEN:")
        lines.append("-" * 40)
        for i, ground in enumerate(grounds, 1):
            lines.append(f"\n{i}. {ground.get('grond', 'Onbekend')}")
            lines.append(f"   Sterkte: {ground.get('sterkte', 'onbekend')}")
            lines.append(f"   Wettelijke basis: {ground.get('wettelijke_basis', 'N/A')}")
            lines.append(f"   Toelichting: {ground.get('toelichting', 'N/A')}")
    else:
        lines.append("Geen specifieke bezwaargronden geïdentificeerd.")

    lines.append("")
    lines.append(f"Aanbeveling: {analysis.get('aanbeveling', 'N/A')}")
    lines.append("=" * 60)

    return "\n".join(lines)
