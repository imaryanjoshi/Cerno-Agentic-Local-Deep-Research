# api/management/commands/test_stream.py
from django.core.management.base import BaseCommand
import asyncio
from api.agents.orchestrator_team import orchestrator_team # Adjust import if needed
import json
import inspect # For inspecting async generator properties

async def test_agno_stream_logic():
    print("Starting Agno stream test (debug iteration)...")
    prompt = "Plan a simple one-step task to find the capital of France and then execute it."
    print(f"\n>>> PROMPT: {prompt}\n")
    
    try:
        print("Attempting to await orchestrator_team.arun...")
        # Ensure this is an `async def` method in `agno`'s Team class
        async_iterator_obj = await orchestrator_team.arun(
            prompt, 
            stream=True, 
            stream_intermediate_steps=True
        )
        print(f"Awaited arun. Object type: {type(async_iterator_obj)}")
        print(f"Is it an async generator? {inspect.isasyncgen(async_iterator_obj)}")
        print(f"Does it have __aiter__? {hasattr(async_iterator_obj, '__aiter__')}")
        print(f"Does it have __anext__? {hasattr(async_iterator_obj, '__anext__')}")

        if not (hasattr(async_iterator_obj, '__aiter__') and hasattr(async_iterator_obj, '__anext__')):
            print("!!! ERROR: orchestrator_team.arun did not return a valid async iterator object.")
            print(f"Object dir: {dir(async_iterator_obj)}")
            return

        chunk_counter = 0
        # This is the standard way to iterate an async generator
        async for chunk in async_iterator_obj:
            chunk_counter += 1
            print(f"\n--- CHUNK {chunk_counter} ---")
            print(f"CHUNK TYPE: {type(chunk)}")

            event_name = "N/A"
            if hasattr(chunk, 'event'):
                event_name = chunk.event
                print(f"EVENT NAME: {event_name}")

            content_preview = "N/A"
            if hasattr(chunk, 'content') and chunk.content is not None:
                if isinstance(chunk.content, str):
                    content_preview = chunk.content[:150] + ('...' if len(chunk.content) > 150 else '')
                else:
                    content_preview = str(chunk.content)
                print(f"CONTENT PREVIEW: {content_preview}")
            
            # (Rest of the interesting_attrs printing logic from previous version can go here)
            interesting_attrs = ['tool_name', 'tool_input', 'tool_output', 'member_id', 'task_description', 'thinking', 'formatted_tool_calls', 'metrics']
            extra_details = {}
            for attr in interesting_attrs:
                if hasattr(chunk, attr) and getattr(chunk, attr) is not None:
                    attr_value = getattr(chunk, attr)
                    if hasattr(attr_value, 'to_dict'): extra_details[attr] = attr_value.to_dict()
                    elif isinstance(attr_value, (dict, list)): extra_details[attr] = attr_value
                    elif isinstance(attr_value, str) and len(attr_value) > 100: extra_details[attr] = attr_value[:100] + "..."
                    else: extra_details[attr] = str(attr_value)
            if extra_details: print(f"OTHER DETAILS: {json.dumps(extra_details, indent=2, default=str)}")

            await asyncio.sleep(0.01) 
    except TypeError as te:
        print(f"\n!!! TypeError during streaming: {te} !!!")
        print("This often means the object being iterated is not a proper async generator.")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n!!! An unexpected error occurred during streaming: {e} !!!")
        import traceback
        traceback.print_exc() 
    finally:
        print("\n--- Agno stream test finished. ---")

class Command(BaseCommand):
    help = 'Tests the Agno streaming output with intermediate steps (debug iteration version).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Running Agno stream test (debug iteration)...'))
        asyncio.run(test_agno_stream_logic())
        self.stdout.write(self.style.SUCCESS('Test finished.'))