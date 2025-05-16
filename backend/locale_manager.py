import gettext
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class LocaleInfo:
    code: str  # 'en', 'de'
    display_name: str  # 'English', 'German'
    native_name: str  # 'English', 'Deutsch'


class LocaleManager:
    LOCALES: Dict[str, LocaleInfo] = {
        'English': LocaleInfo('en', 'English', 'English'),
        'German': LocaleInfo('de', 'German', 'Deutsch'),
    }

    def __init__(self):
        """Centralized locale management"""
        self._current_locale: LocaleInfo = self.LOCALES['English'] # todo change back to german
        self._setup_gettext()
        self.set_locale(self._current_locale.display_name)

    @staticmethod
    def _setup_gettext():
        gettext.bindtextdomain('messages', 'locales')
        gettext.textdomain('messages')

    @property
    def available_locales(self) -> list[LocaleInfo]:
        return list(self.LOCALES.values())

    @property
    def current_locale(self) -> LocaleInfo:
        return self._current_locale

    def set_locale(self, locale_display_name: str) -> None:
        if locale_display_name not in self.LOCALES:
            raise ValueError(f"Unsupported locale: {locale_display_name}")

        self._current_locale = self.LOCALES[locale_display_name]
        lang = gettext.translation(
            'messages',
            localedir='locales',
            languages=[locale_display_name]
        )
        lang.install()
