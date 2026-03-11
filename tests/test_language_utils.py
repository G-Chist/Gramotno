import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from language_logic.language_utils import (
    get_installed_languages,
    get_available_packages,
    install_language_pair,
    is_language_pair_installed,
    translate,
)


class TestGetInstalledLanguages(unittest.TestCase):
    @patch("language_logic.language_utils.argostranslate.translate.get_installed_languages")
    def test_returns_list_of_languages(self, mock_get_installed):
        mock_lang = MagicMock()
        mock_lang.code = "en"
        mock_get_installed.return_value = [mock_lang]

        result = get_installed_languages()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "en")


class TestGetAvailablePackages(unittest.TestCase):
    @patch("language_logic.language_utils.argostranslate.package.update_package_index")
    @patch("language_logic.language_utils.argostranslate.package.get_available_packages")
    def test_returns_available_packages(self, mock_get_packages, mock_update):
        mock_package = MagicMock()
        mock_package.from_code = "en"
        mock_package.to_code = "es"
        mock_get_packages.return_value = [mock_package]

        result = get_available_packages()

        mock_update.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].from_code, "en")
        self.assertEqual(result[0].to_code, "es")


class TestInstallLanguagePair(unittest.TestCase):
    @patch("language_logic.language_utils.get_available_packages")
    @patch("language_logic.language_utils.argostranslate.package.install_from_path")
    def test_installs_package(self, mock_install, mock_get_packages):
        mock_package = MagicMock()
        mock_package.from_code = "en"
        mock_package.to_code = "es"
        mock_package.download.return_value = "/path/to/package"
        mock_get_packages.return_value = [mock_package]

        install_language_pair("en", "es")

        mock_install.assert_called_once_with("/path/to/package")

    @patch("language_logic.language_utils.get_available_packages")
    def test_raises_error_when_package_not_found(self, mock_get_packages):
        mock_get_packages.return_value = []

        with self.assertRaises(ValueError) as ctx:
            install_language_pair("en", "es")

        self.assertIn("No package found", str(ctx.exception))


class TestIsLanguagePairInstalled(unittest.TestCase):
    @patch("language_logic.language_utils.get_installed_languages")
    def test_returns_true_when_pair_installed(self, mock_get_installed):
        from_lang = MagicMock()
        from_lang.code = "en"
        to_lang = MagicMock()
        to_lang.code = "es"
        from_lang.get_translation.return_value = MagicMock()
        mock_get_installed.return_value = [from_lang, to_lang]

        result = is_language_pair_installed("en", "es")

        self.assertTrue(result)

    @patch("language_logic.language_utils.get_installed_languages")
    def test_returns_false_when_from_lang_missing(self, mock_get_installed):
        to_lang = MagicMock()
        to_lang.code = "es"
        mock_get_installed.return_value = [to_lang]

        result = is_language_pair_installed("en", "es")

        self.assertFalse(result)

    @patch("language_logic.language_utils.get_installed_languages")
    def test_returns_false_when_to_lang_missing(self, mock_get_installed):
        from_lang = MagicMock()
        from_lang.code = "en"
        mock_get_installed.return_value = [from_lang]

        result = is_language_pair_installed("en", "es")

        self.assertFalse(result)

    @patch("language_logic.language_utils.get_installed_languages")
    def test_returns_false_when_translation_none(self, mock_get_installed):
        from_lang = MagicMock()
        from_lang.code = "en"
        to_lang = MagicMock()
        to_lang.code = "es"
        from_lang.get_translation.return_value = None
        mock_get_installed.return_value = [from_lang, to_lang]

        result = is_language_pair_installed("en", "es")

        self.assertFalse(result)


class TestTranslate(unittest.TestCase):
    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_translates_when_pair_installed(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Hola"

        result = translate("Hello", "en", "es")

        self.assertEqual(result, "Hola")
        mock_translate.assert_called_once_with("Hello", "en", "es")

    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.install_language_pair")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_installs_and_translates_when_pair_not_installed(
        self, mock_translate, mock_install, mock_is_installed
    ):
        mock_is_installed.return_value = False
        mock_translate.return_value = "Hola"

        result = translate("Hello", "en", "es")

        mock_install.assert_called_once_with("en", "es")
        mock_translate.assert_called_once_with("Hello", "en", "es")
        self.assertEqual(result, "Hola")


class TestTurkishTranslations(unittest.TestCase):
    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_english_to_turkish(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Merhaba"

        result = translate("Hello", "en", "tr")

        self.assertEqual(result, "Merhaba")
        mock_translate.assert_called_once_with("Hello", "en", "tr")

    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_turkish_to_english(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Hello"

        result = translate("Merhaba", "tr", "en")

        self.assertEqual(result, "Hello")
        mock_translate.assert_called_once_with("Merhaba", "tr", "en")

    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.install_language_pair")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_installs_turkish_pair_if_not_installed(
        self, mock_translate, mock_install, mock_is_installed
    ):
        mock_is_installed.return_value = False
        mock_translate.return_value = "Merhaba"

        result = translate("Hello", "en", "tr")

        mock_install.assert_called_once_with("en", "tr")
        self.assertEqual(result, "Merhaba")


class TestRussianTranslations(unittest.TestCase):
    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_english_to_russian(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Привет"

        result = translate("Hello", "en", "ru")

        self.assertEqual(result, "Привет")
        mock_translate.assert_called_once_with("Hello", "en", "ru")

    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_russian_to_english(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Hello"

        result = translate("Привет", "ru", "en")

        self.assertEqual(result, "Hello")
        mock_translate.assert_called_once_with("Привет", "ru", "en")

    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.install_language_pair")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_installs_russian_pair_if_not_installed(
        self, mock_translate, mock_install, mock_is_installed
    ):
        mock_is_installed.return_value = False
        mock_translate.return_value = "Привет"

        result = translate("Hello", "en", "ru")

        mock_install.assert_called_once_with("en", "ru")
        self.assertEqual(result, "Привет")


class TestTurkishRussianTranslations(unittest.TestCase):
    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_turkish_to_russian(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Привет"

        result = translate("Merhaba", "tr", "ru")

        self.assertEqual(result, "Привет")
        mock_translate.assert_called_once_with("Merhaba", "tr", "ru")

    @patch("language_logic.language_utils.is_language_pair_installed")
    @patch("language_logic.language_utils.argostranslate.translate.translate")
    def test_russian_to_turkish(self, mock_translate, mock_is_installed):
        mock_is_installed.return_value = True
        mock_translate.return_value = "Merhaba"

        result = translate("Привет", "ru", "tr")

        self.assertEqual(result, "Merhaba")
        mock_translate.assert_called_once_with("Привет", "ru", "tr")


if __name__ == "__main__":
    unittest.main()
