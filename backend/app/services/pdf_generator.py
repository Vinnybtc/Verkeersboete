"""
PDF Generator for bezwaarschriften (appeal documents).

Generates professional PDF documents using Jinja2 templates and WeasyPrint.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.schemas.schemas import FineExtracted

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def generate_bezwaarschrift(
    extracted_data: FineExtracted,
    legal_analysis: dict,
    user_info: dict,
    output_dir: str | None = None,
) -> str:
    """
    Generate a formal bezwaarschrift (appeal document) as PDF.

    Args:
        extracted_data: Extracted fine data from OCR.
        legal_analysis: Legal analysis results from the legal agent.
        user_info: Dictionary with user details (name, address, etc.).
        output_dir: Optional output directory. Defaults to settings.generated_dir.

    Returns:
        Path to the generated PDF file.
    """
    if output_dir is None:
        output_dir = settings.generated_dir

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Set up Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("bezwaarschrift.html")

    # Format date
    current_date = datetime.now().strftime("%d %B %Y")
    # Dutch month names
    dutch_months = {
        "January": "januari", "February": "februari", "March": "maart",
        "April": "april", "May": "mei", "June": "juni",
        "July": "juli", "August": "augustus", "September": "september",
        "October": "oktober", "November": "november", "December": "december",
    }
    for eng, nl in dutch_months.items():
        current_date = current_date.replace(eng, nl)

    overtreding_datum = extracted_data.overtreding_datum or "onbekend"

    # Prepare template context
    context = {
        "user_name": user_info.get("name", ""),
        "user_address": user_info.get("address", ""),
        "user_postal_code": user_info.get("postal_code", ""),
        "user_city": user_info.get("city", ""),
        "user_email": user_info.get("email", ""),
        "user_phone": user_info.get("phone", ""),
        "current_date": current_date,
        "beschikkingsnummer": extracted_data.beschikkingsnummer or "onbekend",
        "feitcode": extracted_data.feitcode or "onbekend",
        "overtreding_datum": overtreding_datum,
        "bedrag": f"{extracted_data.bedrag:.2f}" if extracted_data.bedrag else "onbekend",
        "omschrijving": extracted_data.omschrijving or "onbekend",
        "locatie": extracted_data.locatie or "onbekend",
        "instantie": extracted_data.instantie or "",
        "legal_grounds": legal_analysis.get("bezwaargronden", []),
    }

    # Render HTML
    html_content = template.render(**context)

    # Generate PDF
    filename = f"bezwaarschrift_{uuid.uuid4().hex[:8]}.pdf"
    output_path = str(Path(output_dir) / filename)

    try:
        from weasyprint import HTML

        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"Generated bezwaarschrift PDF: {output_path}")
    except ImportError:
        # Fallback: save as HTML if WeasyPrint is not available
        html_filename = f"bezwaarschrift_{uuid.uuid4().hex[:8]}.html"
        output_path = str(Path(output_dir) / html_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.warning(
            "WeasyPrint not available, saved as HTML instead: %s", output_path
        )

    return output_path
