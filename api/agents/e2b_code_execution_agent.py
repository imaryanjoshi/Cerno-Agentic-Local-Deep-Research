
from agno.agent import Agent
from api.config import default_llm
from agno.tools.python import PythonTools
import os

e2b_python_tools = PythonTools(
    pip_install=True 
)


EXPECTED_E2B_SCRIPT_JSON_OUTPUT = """
{
  "e2b_sandbox_id": "string - ID of the sandbox used or null if setup failed",
  "exit_code": "integer - 0 for success, non-zero for errors, -1 for pre-execution failure",
  "final_stdout_summary": "string - A very brief summary of stdout if applicable, or empty",
  "final_stderr_summary": "string - A very brief summary of stderr if applicable, or empty",
  "error_message": "string - Null or empty if successful, or an error message if E2B setup/execution itself failed (not for code errors, those are in stderr/exit_code)."
}
"""

e2b_code_execution_agent = Agent(
    name="E2BCodeExecutionAgent",
    role="An agent that WRITES AND EXECUTES Python scripts using the E2B SDK to run code (Python/shell) in secure E2B cloud sandboxes, streaming stdout/stderr.",
    model=default_llm,
    tools=[e2b_python_tools],
    instructions=[
        "You will receive a task object with `call_name` ('run_python_in_e2b' or 'run_shell_in_e2b') and `code_to_execute` (the script or command string).",
        "Your primary task is to **generate a Python script** that uses the E2B SDK to perform the requested execution and streams its stdout/stderr. Then, you will use your `run_python_code` tool to execute this generated script.",
        "The generated Python script MUST:",
        "  1. Import `Sandbox`, `ProcessMessage` from `e2b`, `os`, `json`, `asyncio`.",
        "  2. Retrieve the E2B_API_KEY: `api_key = os.getenv('E2B_API_KEY')`.",
        "  3. Define an `async def main():` function.",
        "  4. Inside `main()`:",
        "     a. Initialize an E2B sandbox: `sandbox = Sandbox(api_key=api_key, template='base')`. Handle potential errors during sandbox creation.",
        "     b. Store `sandbox.id`.",
        "     c. If `call_name` is 'run_python_in_e2b':",
        "        i.  Write the `code_to_execute` to a file inside the sandbox (e.g., `await sandbox.filesystem.write('script.py', code_to_execute)`).",
        "        ii. Define the command: `cmd = 'python script.py'`.",
        "     d. If `call_name` is 'run_shell_in_e2b':",
        "        i.  Define the command: `cmd = code_to_execute` (the shell command string).",
        "     e. Start the process: `process = await sandbox.process.start(cmd)`.",
        "     f. **Stream stdout/stderr:** Iterate through `process.output_messages` (which is an async iterator of `ProcessMessage` objects).",
        "        - For each `msg` in `process.output_messages`:",
        "          - If `msg.type == 'stdout'`, print `f\"E2B_STDOUT: {msg.line}\"`.",
        "          - If `msg.type == 'stderr'`, print `f\"E2B_STDERR: {msg.line}\"`.",
        "     g. Wait for process completion: `await process.wait()` to ensure it finishes.",
        "     h. Get `exit_code = process.exit_code`.",
        "     i. Close the sandbox: `await sandbox.close()`.",
        "     j. Prepare a final JSON summary dictionary with keys: `e2b_sandbox_id`, `exit_code`, `final_stdout_summary` (e.g., first few lines or 'See stream'), `final_stderr_summary`, `error_message` (for E2B setup issues).",
        "  5. The script must print this final JSON summary as its VERY LAST output: `print(json.dumps(summary_dict))`.",
        "  6. The script should handle exceptions during sandbox operations and populate `error_message` in the final JSON if they occur.",
        "  7. Use `asyncio.run(main())` to run the async main function.",
        "After generating this Python script, you will then use your `run_python_code` tool to execute this script you just generated.",
        "Your final response (from your LLM turn) to the StepExecutorTeam should be the direct JSON output string produced by the execution of your generated E2B-interacting Python script. Do not add any conversational wrappers around it.",
    ],
    expected_output=EXPECTED_E2B_SCRIPT_JSON_OUTPUT, 
    markdown=False,
)