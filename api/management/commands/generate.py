
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.llm_registry import get_available_models  # We will temporarily use the old function

class Command(BaseCommand):
    help = 'Discovers all available LLM models from configured providers and saves them to a static JSON file.'

    def handle(self, *args, **options):
        self.stdout.write("Starting model discovery from all providers...")
        self.stdout.write("NOTE: This requires all relevant API keys (OPENAI_API_KEY, GEMINI_API_KEY, etc.) to be set in your environment.")

        # This function still makes the live API calls
        all_models_list = get_available_models()

        # Group the flat list into the desired {provider: [models]} structure
        grouped_models = {}
        for model in all_models_list:
            provider = model.get("provider")
            if provider not in grouped_models:
                grouped_models[provider] = []
            grouped_models[provider].append(model)

        # Define the output path
        output_dir = os.path.join(settings.BASE_DIR, 'api', 'data')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'available_models.json')

        # Write the data to the JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(grouped_models, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Successfully saved {len(all_models_list)} models to {output_path}"))