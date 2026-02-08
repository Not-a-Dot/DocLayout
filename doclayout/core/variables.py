
import json
import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class VariableManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VariableManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._load_variables()
        return cls._instance

    def __init__(self):
        # Already initialized in __new__ or _load_variables
        if not hasattr(self, 'variables'):
             self.variables: Dict[str, str] = {}

    def _get_file_path(self):
        # Save in user's home or local dir
        # For this env, let's use the project dir
        return os.path.join(os.path.dirname(__file__), "..", "..", "variables.json")

    def _load_variables(self):
        path = self._get_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    self.variables = json.load(f)
            except Exception as e:
                logger.error("Error loading variables: %s", e, exc_info=True)
                self.variables = {}
        else:
            self.variables = {}

    def save_variables(self):
        path = self._get_file_path()
        try:
            with open(path, 'w') as f:
                json.dump(self.variables, f, indent=2)
        except Exception as e:
            logger.error("Error saving variables: %s", e, exc_info=True)

    def add_variable(self, name: str, default_value: str = ""):
        self.variables[name] = default_value
        self.save_variables()

    def get_variables(self) -> List[str]:
        return list(self.variables.keys())

    def get_value(self, name: str) -> str:
        return self.variables.get(name, "")
