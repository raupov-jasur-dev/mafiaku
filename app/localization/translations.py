"""
Master multi-language translation storage with 26 natural languages support.
"""
from typing import Dict
from app.localization.locales_core import LOCALES_CORE
from app.localization.locales_turkic import LOCALES_TURKIC
from app.localization.locales_slavic_caucasus import LOCALES_SLAVIC_CAUCASUS
from app.localization.locales_west_world import LOCALES_WEST_WORLD

TRANSLATIONS: Dict[str, Dict[str, str]] = {}
TRANSLATIONS.update(LOCALES_CORE)
TRANSLATIONS.update(LOCALES_TURKIC)
TRANSLATIONS.update(LOCALES_SLAVIC_CAUCASUS)
TRANSLATIONS.update(LOCALES_WEST_WORLD)
