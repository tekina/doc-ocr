"""
PromptBuilder service for building prompts from templates and field schemas.
"""
from services.config_loader import DocumentTypeConfig


class PromptBuilder:
    """Builds prompts from templates and field schemas."""

    @staticmethod
    def build_prompt(document_config: DocumentTypeConfig) -> str:
        """Build complete prompt from document config."""
        if document_config.processing_mode == 'generic':
            # For generic mode, return template as-is
            return document_config.prompt_template

        # For structured mode, inject field list into template
        field_list = document_config.get_field_list()
        prompt = document_config.prompt_template.replace('{{field_list}}', field_list)
        return prompt

    @staticmethod
    def build_custom_prompt(template: str, **kwargs) -> str:
        """Build prompt with custom variables."""
        for key, value in kwargs.items():
            placeholder = f'{{{{{key}}}}}'
            template = template.replace(placeholder, str(value))
        return template
