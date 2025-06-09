
from agno.agent import Agent
from agno.tools.file import FileTools
from api.config import default_llm, AGENT_OUTPUT_DIR 
import json
import uuid 
import os


os.makedirs(AGENT_OUTPUT_DIR, exist_ok=True)
EXPECTED_PLANNER_OUTPUT_JSON_STRUCTURE = """
{
  "acknowledgment_message": "string - A brief, polite acknowledgment for the user.",
  "plan_files_created": "boolean - True if both master_plan.md and master_plan.json were successfully saved.",
  "markdown_plan_filename": "master_plan.md",
  "json_plan_filename": "master_plan.json",
  "error_message": "string - An error message if any issues occurred, otherwise an empty string or null."
}
"""

planner_file_tools = FileTools(base_dir=AGENT_OUTPUT_DIR, save_files=True, read_files=False, list_files=False)
def get_planner_agent(llm_instance):
  initial_response_and_planner_agent = Agent(
      name="InitialResponseAndPlannerAgent",
      role="An AI assistant that provides an initial acknowledgment, then creates and SAVES a detailed execution plan in Markdown and JSON formats. It then reports success and the acknowledgment in a specific JSON format.",
      model=llm_instance,
      tools=[planner_file_tools],
      instructions=[
    "Input: `user_prompt`.",
    "1. **Acknowledge User:** Generate a brief acknowledgment message.",
    "2. **Create Execution Plan:**\n"
    "   - Divide the research request into a few detailed phases. Each phase should represent significant work, and the final phase must be the summary/report. File outputs should be MD files if text based.\n"
    "   - Assign each phase to exactly one of: `ResearchAgent`, `ComposerAgent`, or (only if needed) `e2-bcode-execution-agent`.\n"
    "   - **YOU MUST IN THIS TURN Produce `master_plan.md`:**\n"
    "       • One checklist item (`- [ ]`) per phase, including all context from `user_prompt`.\n"
    "   - **YOU MUST IN THIS TURN Produce `master_plan.json`:**\n"
    "       • JSON array. Each object must contain:\n"
    "         - `id` (unique string)\n"
    "         - `description` (exact text from the Markdown phase)\n"
    "         - `call_name` (short verb phrase)\n"
    "         - `input` (array of filenames or `NONE`)\n"
    "         - `agent_id` (one of `ResearchAgent`, `ComposerAgent`, `e2-bcode-execution-agent`)\n"
    "         - `outputs` (array of filenames)\n"
    "         - `status`: set to `\"pending\"`.\n"
    "       • Use line breaks in the JSON so it’s human-readable.",
    "3. **YOU MUST IN THIS TURN Save Plans:**\n"
    "   - Invoke the `save_file` tool twice, with these exact arguments:\n"
    "       • `save_file filename: \"master_plan.md\" contents: \"<entire Markdown contents>\"`\n"
    "       • `save_file filename: \"master_plan.json\" contents: \"<entire JSON contents>\"`\n"
    " YOU WILL PROCEED WITH RESPONSE ONLY AFTER MAKING AND SAVING THE PLANS.YOU WILL NOT MERELY SAY THAT YOU WILL MAKE THE PLANS AND END TURN. MAKING AND SAVING THE PLANS MUST BE IN THIS TURN."
    "4. **Final Output:**\n"
    "   - Return exactly this JSON:\n"
    "     {\n"
    "       \"acknowledgment_message\": string,\n"
    "       \"plan_files_created\": boolean,\n"
    "       \"markdown_plan_filename\": \"master_plan.md\",\n"
    "       \"json_plan_filename\": \"master_plan.json\",\n"
    "       \"error_message\": string|null\n"
    "     }\n"
    "   - Do not include file contents—only this wrapper.\n",
    "Goal: Generate a concise yet thorough plan in both Markdown and JSON, call `save_file` to write them, and return the specified JSON object. /no_think"
  ],
      expected_output=EXPECTED_PLANNER_OUTPUT_JSON_STRUCTURE,
      show_tool_calls=True, debug_mode=True,reasoning=False,reasoning_max_steps=0, success_criteria="Produced and SAVED a concise, logically ordered plan (in both Markdown and JSON)"
  )
  return initial_response_and_planner_agent