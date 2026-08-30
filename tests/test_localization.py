import unittest
from app.localization.languages import SUPPORTED_LANGUAGES
from app.localization.translations import TRANSLATIONS

class TestLocalizationCompleteness(unittest.TestCase):
    def test_all_supported_languages_exist_in_translations(self):
        """Checks that all 26 declared languages are in TRANSLATIONS dictionary."""
        for lang_code in SUPPORTED_LANGUAGES:
            self.assertIn(
                lang_code, 
                TRANSLATIONS, 
                f"Language '{lang_code}' defined in SUPPORTED_LANGUAGES is missing in TRANSLATIONS"
            )

    def test_all_keys_exist_in_all_languages(self):
        """Checks that every key defined in base language exists in all 26 languages."""
        base_keys = set(TRANSLATIONS["uz"].keys())
        missing_report = {}

        for lang_code in SUPPORTED_LANGUAGES:
            lang_dict = TRANSLATIONS.get(lang_code, {})
            missing = base_keys - set(lang_dict.keys())
            if missing:
                missing_report[lang_code] = list(missing)

        self.assertEqual(
            missing_report, 
            {}, 
            f"Some languages are missing translation keys: {missing_report}"
        )

if __name__ == "__main__":
    unittest.main()
