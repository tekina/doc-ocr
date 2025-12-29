"""
ConfigLoader service for loading and managing document type configurations.
"""
import os
import json
from typing import Dict, List, Optional


class DocumentTypeConfig:
    """Represents a single document type configuration."""

    def __init__(self, config_dict: dict):
        self.id = config_dict['id']
        self.name = config_dict['name']
        self.country = config_dict['country']
        self.category = config_dict['category']
        self.description = config_dict.get('description', '')
        self.enabled = config_dict.get('enabled', True)
        self.version = config_dict.get('version', '1.0')
        self.processing_mode = config_dict['processing_mode']
        self.prompt_template = config_dict['prompt_template']
        self.fields = config_dict.get('fields', [])
        self.sample_file = config_dict.get('sample_file')
        self.metadata = config_dict.get('metadata', {})

    def get_field_list(self) -> str:
        """Returns comma-separated list of field IDs."""
        return ', '.join([f['id'] for f in self.fields])

    def to_dict(self) -> dict:
        """Returns dictionary representation for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country,
            'category': self.category,
            'description': self.description,
            'sample_file': self.sample_file,
            'fields': self.fields,
            'processing_mode': self.processing_mode
        }


class ConfigLoader:
    """Loads and manages document type configurations from JSON files."""

    def __init__(self, config_dir: str = 'config/document_types'):
        self.config_dir = config_dir
        self._configs: Dict[str, DocumentTypeConfig] = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """Recursively load all JSON configs from config directory."""
        if not os.path.exists(self.config_dir):
            print(f"Warning: Config directory '{self.config_dir}' does not exist")
            return

        for root, dirs, files in os.walk(self.config_dir):
            for file in files:
                if file.endswith('.json'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            doc_config = DocumentTypeConfig(config_data)
                            self._configs[doc_config.id] = doc_config
                            print(f"Loaded config: {doc_config.id} - {doc_config.name}")
                    except Exception as e:
                        print(f"Error loading config from {filepath}: {str(e)}")

    def get_document_type(self, doc_type_id: str) -> Optional[DocumentTypeConfig]:
        """Get specific document type config by ID."""
        return self._configs.get(doc_type_id)

    def get_all_document_types(self, enabled_only: bool = True) -> List[DocumentTypeConfig]:
        """Get all document type configs."""
        configs = list(self._configs.values())
        if enabled_only:
            configs = [c for c in configs if c.enabled]
        return configs

    def get_by_category(self, category: str) -> List[DocumentTypeConfig]:
        """Get document types by category."""
        return [c for c in self._configs.values()
                if c.category == category and c.enabled]

    def reload(self):
        """Reload all configurations (useful for hot-reloading)."""
        self._configs.clear()
        self._load_all_configs()
