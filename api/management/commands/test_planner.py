# api/management/commands/test_planner.py
from django.core.management.base import BaseCommand
import asyncio
import os
from django.conf import settings # To get AGENT_OUTPUT_DIR if defined globally

# Adjust the import path according to your project structure
from api.agents.planner_agent import planner_agent
AGENT_OUTPUT_DIR = settings.BASE_DIR / "agent_outputs"
# Ensure AGENT_OUTPUT_DIR (used by FileTools in PlannerAgent) exists
os.makedirs(AGENT_OUTPUT_DIR, exist_ok=True)

# The complex prompt for testing
JAPAN_TRIP_PROMPT = (
    "I need a 7-day Japan itinerary for April 15-23 from Seattle, "
    "with a $2500-5000 budget for my fiancée and me. "
    "We love historical sites, hidden gems, and Japanese culture "
    "(kendo, tea ceremonies, Zen meditation). We want to see Nara's deer "
    "and explore cities on foot. I plan to propose during this trip "
    "and need a special location recommendation. Please provide a detailed itinerary, "
    "a research summary, and a to-do checklist."
)

MASTER_PLAN_FILENAME = "master_plan.md" # Consistent filename

def run_planner_test_logic():
    print(f"--- Starting PlannerAgent Test ---")
    print(f"Target output file: {os.path.join(AGENT_OUTPUT_DIR, MASTER_PLAN_FILENAME)}")
    
    # Simulate the Orchestrator delegating the task to the PlannerAgent
    # The PlannerAgent's instructions expect the user goal.
    # In a real scenario, the Orchestrator would pass this.
    # Here, we are directly giving the PlannerAgent the user's high-level goal.
    
    # The PlannerAgent's instructions say:
    # "You receive a high-level user goal from the Orchestrator."
    # "Your SOLE TASK is to create a meta-execution plan and save it to 'master_plan.md'."
    # So, the prompt to the planner should be the user's goal.
    
    planner_task_description = (
        f"Based on the following user goal: '{JAPAN_TRIP_PROMPT}'. "
        f"Create a meta-execution plan as '{MASTER_PLAN_FILENAME}'. This plan is a Markdown checklist "
        f"detailing all steps, agents, and RELATIVE I/O filenames required to produce the user's "
        f"final requested deliverables (itinerary, research summary, to-do checklist). "
        f"Each step in '{MASTER_PLAN_FILENAME}' must start with an unchecked checkbox (`- [ ]`). "
        f"Save this plan using your file saving tool."
    )

    print(f"\n--- Prompting PlannerAgent with Task Description ---")
    # We use `arun` because the agent might be async internally, even if we don't stream its direct output here.
    # We are interested in the side effect (file creation) and its confirmation message.
    # We set stream=False because we just want the final confirmation, not token-by-token of its thought process.
    # stream_intermediate_steps=False is also fine here as we are not debugging its internal tool calls for this test.
    
    try:
        # The PlannerAgent should ideally just take the user_goal as its main input.
        # Its instructions already tell it to save to "master_plan.md".
        # So, the prompt to the planner_agent should be the user's high-level goal.
        response = planner_agent.run(
            JAPAN_TRIP_PROMPT, # The core user goal
            stream=False, # We want the final confirmation message
            stream_intermediate_steps=False 
        )
        
        print(f"\n--- PlannerAgent Final Confirmation Message ---")
        if response and hasattr(response, 'content'):
            print(response.content)
        else:
            print(f"PlannerAgent response object: {response}")

        # Check if the file was created
        master_plan_path = os.path.join(AGENT_OUTPUT_DIR, MASTER_PLAN_FILENAME)
        if os.path.exists(master_plan_path):
            print(f"\n--- SUCCESS: '{MASTER_PLAN_FILENAME}' was created at '{master_plan_path}' ---")
            print(f"\n--- Contents of '{MASTER_PLAN_FILENAME}' ---")
            with open(master_plan_path, 'r', encoding='utf-8') as f:
                print(f.read())
            print(f"\n--- End of '{MASTER_PLAN_FILENAME}' Contents ---")
        else:
            print(f"\n--- FAILURE: '{MASTER_PLAN_FILENAME}' was NOT created at '{master_plan_path}' ---")

    except Exception as e:
        print(f"\n--- ERROR during PlannerAgent execution ---")
        import traceback
        traceback.print_exc()
    
    print(f"\n--- PlannerAgent Test Finished ---")


class Command(BaseCommand):
    help = 'Tests the PlannerAgent in isolation to generate master_plan.md.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Running PlannerAgent Isolation Test...'))
        run_planner_test_logic()
        self.stdout.write(self.style.SUCCESS('PlannerAgent Isolation Test finished. Please check the console output and agent_outputs/master_plan.md.'))