from typing import Optional, Dict, Any
from app.localization.languages import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from app.localization.translations import TRANSLATIONS

class LocalizationManager:
    """Manages string translation with graceful fallback across all 26 supported languages."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, str]] = TRANSLATIONS

    def get(self, key: str, lang: Optional[str] = None, **kwargs: Any) -> str:
        if not lang or lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE

        # Try user language
        lang_dict = self._cache.get(lang, {})
        text = lang_dict.get(key)
        
        # Fallback to Uzbek (uz), then English (en), then Russian (ru)
        if not text:
            text = self._cache.get("uz", {}).get(key)
        if not text:
            text = self._cache.get("en", {}).get(key)
        if not text:
            text = self._cache.get("ru", {}).get(key, key)

        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def get_supported_languages(self) -> Dict[str, Dict[str, str]]:
        return SUPPORTED_LANGUAGES

i18n = LocalizationManager()
