import argostranslate.package
import argostranslate.translate


def get_installed_languages():
    return argostranslate.translate.get_installed_languages()


def get_available_packages():
    argostranslate.package.update_package_index()
    return argostranslate.package.get_available_packages()


def install_language_pair(from_code: str, to_code: str):
    available_packages = get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code,
            available_packages
        ),
        None
    )
    if package_to_install is None:
        raise ValueError(f"No package found for {from_code} -> {to_code}")
    argostranslate.package.install_from_path(package_to_install.download())


def is_language_pair_installed(from_code: str, to_code: str) -> bool:
    installed = get_installed_languages()
    from_lang = next(filter(lambda x: x.code == from_code, installed), None)
    if from_lang is None:
        return False
    to_lang = next(filter(lambda x: x.code == to_code, installed), None)
    if to_lang is None:
        return False
    translation = from_lang.get_translation(to_lang)
    return translation is not None


def translate(text: str, from_code: str, to_code: str) -> str:
    if not is_language_pair_installed(from_code, to_code):
        install_language_pair(from_code, to_code)
    return argostranslate.translate.translate(text, from_code, to_code)
