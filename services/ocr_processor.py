"""
OCRProcessor service for handling OCR processing with Claude API.
"""
from anthropic import Anthropic
from services.config_loader import ConfigLoader
from services.prompt_builder import PromptBuilder


class OCRProcessor:
    """Handles OCR processing with Claude API."""

    def __init__(self, anthropic_client: Anthropic, config_loader: ConfigLoader):
        self.client = anthropic_client
        self.config_loader = config_loader
        self.prompt_builder = PromptBuilder()

    def process_document(self, base64_image: str, doc_type_id: str, file_type: str) -> str:
        """Process document with specified document type."""
        print(f"=== STARTING OCR PROCESSING for {doc_type_id} ===", flush=True)

        # Get document config
        doc_config = self.config_loader.get_document_type(doc_type_id)
        if not doc_config:
            raise ValueError(f"Unknown document type: {doc_type_id}")

        # Build prompt
        prompt = self.prompt_builder.build_prompt(doc_config)
        print(f"Prompt: {prompt[:100]}...", flush=True)

        # Determine media type
        media_type = self._get_media_type(file_type)
        print(f"Media type: {media_type}", flush=True)
        print("Calling Anthropic API...", flush=True)

        # Call Claude API
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        print("API call completed!", flush=True)
        print(f"Response: {response}", flush=True)

        # Extract and clean response
        details = response.content[0].text
        print(f"Extracted details: {details}", flush=True)

        details = self._clean_json_response(details)
        print(f"Cleaned details: {details}", flush=True)

        return details

    def _get_media_type(self, file_type: str) -> str:
        """Determine media type from file MIME type."""
        media_type = "image/jpeg"
        if "png" in file_type.lower():
            media_type = "image/png"
        elif "webp" in file_type.lower():
            media_type = "image/webp"
        elif "gif" in file_type.lower():
            media_type = "image/gif"
        return media_type

    def _clean_json_response(self, response_text: str) -> str:
        """Remove markdown code fences if present."""
        details = response_text
        if details.startswith("```"):
            # Remove opening fence (```json or ```)
            details = details.split('\n', 1)[1] if '\n' in details else details[3:]
            # Remove closing fence (```)
            if details.endswith("```"):
                details = details.rsplit('\n```', 1)[0]
            details = details.strip()
        return details
