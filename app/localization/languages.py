from typing import Dict, List

SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "uz": {"code": "uz", "name": "O'zbek", "flag": "🇺🇿", "native": "O'zbek tili"},
    "ru": {"code": "ru", "name": "Русский", "flag": "🇷🇺", "native": "Русский"},
    "en": {"code": "en", "name": "English", "flag": "🇺🇸", "native": "English"},
    "uk": {"code": "uk", "name": "Українська", "flag": "🇺🇦", "native": "Українська"},
    "be": {"code": "be", "name": "Беларускі", "flag": "🇧🇾", "native": "Беларуская"},
    "de": {"code": "de", "name": "Deutsch", "flag": "🇩🇪", "native": "Deutsch"},
    "fr": {"code": "fr", "name": "Le Français", "flag": "🇫🇷", "native": "Français"},
    "it": {"code": "it", "name": "Italiano", "flag": "🇮🇹", "native": "Italiano"},
    "es": {"code": "es", "name": "Español", "flag": "🇪🇸", "native": "Español"},
    "pl": {"code": "pl", "name": "Polski", "flag": "🇵🇱", "native": "Polski"},
    "lv": {"code": "lv", "name": "Latvian", "flag": "🇱🇻", "native": "Latviešu"},
    "cs": {"code": "cs", "name": "Čeština", "flag": "🇨🇿", "native": "Čeština"},
    "kaa": {"code": "kaa", "name": "Qaraqalpaq", "flag": "🇺🇿", "native": "Qaraqalpaqsha"},
    "az": {"code": "az", "name": "Azərbaycan", "flag": "🇦🇿", "native": "Azərbaycan dili"},
    "hy": {"code": "hy", "name": "Հայերեն", "flag": "🇦🇲", "native": "Հայերեն"},
    "ka": {"code": "ka", "name": "ქართული", "flag": "🇬🇪", "native": "ქართული"},
    "tr": {"code": "tr", "name": "Türkçe", "flag": "🇹🇷", "native": "Türkçe"},
    "tt": {"code": "tt", "name": "Татарча", "flag": "🇷🇺", "native": "Татар теле"},
    "kk": {"code": "kk", "name": "Қазақша", "flag": "🇰🇿", "native": "Қазақ тілі"},
    "ky": {"code": "ky", "name": "Кыргызча", "flag": "🇰🇬", "native": "Кыргыз тили"},
    "tg": {"code": "tg", "name": "Забони тоҷикӣ", "flag": "🇹🇯", "native": "Тоҷикӣ"},
    "ko": {"code": "ko", "name": "한국어", "flag": "🇰🇷", "native": "한국어"},
    "hi": {"code": "hi", "name": "हिन्दी", "flag": "🇮🇳", "native": "हिन्दी"},
    "zh": {"code": "zh", "name": "中文", "flag": "🇨🇳", "native": "简体中文"},
    "ar": {"code": "ar", "name": "العربية", "flag": "🇸🇦", "native": "العربية"},
    "id": {"code": "id", "name": "Indonesian", "flag": "🇮🇩", "native": "Bahasa Indonesia"},
}

DEFAULT_LANGUAGE = "uz"
