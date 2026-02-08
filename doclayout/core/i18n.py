"""
Internationalization (i18n) module for DocLayout.

Provides translation support via JSON files with automatic language detection
and fallback mechanisms.
"""

import json
import logging
import os
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TranslationManager:
    """
    Singleton class for managing translations.
    
    Supports multiple languages via JSON files with automatic detection
    of system language and fallback to default language.
    
    Attributes:
        current_language (str): Currently active language code (e.g., 'pt-BR').
        default_language (str): Default fallback language ('pt-BR').
        translations (Dict): Loaded translation strings.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.default_language = "pt-BR"
        self.current_language = self.default_language
        self.translations: Dict[str, str] = {}
        self.available_languages: Dict[str, str] = {}
        
        self._load_available_languages()
        self._detect_system_language()
        self._load_translations(self.current_language)
        
        self._initialized = True
    
    def _get_translations_dir(self) -> Path:
        """Get the path to the translations directory."""
        return Path(__file__).parent.parent / "translations"
    
    def _load_available_languages(self) -> None:
        """
        Scan translations directory for available language files.
        
        Populates available_languages dict with language codes and names.
        """
        trans_dir = self._get_translations_dir()
        if not trans_dir.exists():
            logger.warning("Translations directory not found: %s", trans_dir)
            return
        
        for file_path in trans_dir.glob("*.json"):
            lang_code = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    lang_name = data.get("_language_name", lang_code)
                    self.available_languages[lang_code] = lang_name
            except Exception as e:
                logger.error("Error loading language file %s: %s", file_path, e)
    
    def _detect_system_language(self) -> None:
        """
        Detect system language and set as current if available.
        
        Falls back to default language if system language not available.
        """
        import locale
        
        try:
            # Get system locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                # Try exact match first (e.g., 'pt_BR')
                lang_code = system_locale.replace('_', '-')
                if lang_code in self.available_languages:
                    self.current_language = lang_code
                    logger.info("Detected system language: %s", lang_code)
                    return
                
                # Try language prefix (e.g., 'pt' from 'pt_BR')
                lang_prefix = system_locale.split('_')[0]
                for available_lang in self.available_languages:
                    if available_lang.startswith(lang_prefix):
                        self.current_language = available_lang
                        logger.info("Detected system language (prefix match): %s", available_lang)
                        return
        except Exception as e:
            logger.warning("Could not detect system language: %s", e)
        
        # Fallback to default
        self.current_language = self.default_language
        logger.info("Using default language: %s", self.default_language)
    
    def _load_translations(self, language: str) -> None:
        """
        Load translations for the specified language.
        
        Args:
            language (str): Language code (e.g., 'pt-BR', 'en-US').
        
        Raises:
            FileNotFoundError: If translation file doesn't exist.
        """
        trans_dir = self._get_translations_dir()
        file_path = trans_dir / f"{language}.json"
        
        if not file_path.exists():
            logger.error("Translation file not found: %s", file_path)
            # Try fallback to default language
            if language != self.default_language:
                logger.info("Falling back to default language: %s", self.default_language)
                self._load_translations(self.default_language)
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            logger.info("Loaded translations for language: %s", language)
        except Exception as e:
            logger.error("Error loading translations from %s: %s", file_path, e, exc_info=True)
            self.translations = {}
    
    def set_language(self, language: str) -> bool:
        """
        Change the current language.
        
        Args:
            language (str): Language code to switch to.
        
        Returns:
            bool: True if language was changed successfully, False otherwise.
        """
        if language not in self.available_languages:
            logger.warning("Language not available: %s", language)
            return False
        
        self.current_language = language
        self._load_translations(language)
        logger.info("Changed language to: %s", language)
        return True
    
    def get(self, key: str, **kwargs) -> str:
        """
        Get translated string for the given key.
        
        Supports string formatting with keyword arguments.
        
        Args:
            key (str): Translation key (dot-separated path, e.g., 'menu.file.new').
            **kwargs: Optional format arguments for string interpolation.
        
        Returns:
            str: Translated string, or the key itself if translation not found.
        
        Example:
            >>> t = TranslationManager()
            >>> t.get('menu.file.new')
            'Novo'
            >>> t.get('status.saved', filename='test.json')
            'Arquivo test.json salvo com sucesso'
        """
        # Navigate nested dict using dot notation
        keys = key.split('.')
        value = self.translations
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                logger.debug("Translation key not found: %s", key)
                return key  # Return key as fallback
        
        # Format string if kwargs provided
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning("Missing format argument for key %s: %s", key, e)
                return value
        
        return value if isinstance(value, str) else key
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get dictionary of available languages.
        
        Returns:
            Dict[str, str]: Mapping of language codes to language names.
        """
        return self.available_languages.copy()
    
    def get_current_language(self) -> str:
        """
        Get the current language code.
        
        Returns:
            str: Current language code (e.g., 'pt-BR').
        """
        return self.current_language


# Global convenience function
_manager = None

def tr(key: str, **kwargs) -> str:
    """
    Global convenience function for translations.
    
    Args:
        key (str): Translation key.
        **kwargs: Optional format arguments.
    
    Returns:
        str: Translated string.
    
    Example:
        >>> from doclayout.core.i18n import tr
        >>> tr('menu.file.new')
        'Novo'
    """
    global _manager
    if _manager is None:
        _manager = TranslationManager()
    return _manager.get(key, **kwargs)


def get_translation_manager() -> TranslationManager:
    """
    Get the global TranslationManager instance.
    
    Returns:
        TranslationManager: Singleton instance.
    """
    global _manager
    if _manager is None:
        _manager = TranslationManager()
    return _manager
