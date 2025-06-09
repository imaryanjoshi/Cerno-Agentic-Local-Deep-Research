
from agno.agent import Agent
from agno.team import Team
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.yfinance import YFinanceTools
from api.config import default_llm, AGENT_OUTPUT_DIR, generic_file_tools
from .web_scraping_agent import web_scraping_agent
from .e2b_code_execution_agent import e2b_code_execution_agent 


def get_step_executor_team(llm_instance):
    researchagent = Agent(
        name="ResearchAgent",
        role="An agent specialized in deep research. I can save the content to a file if instructed. Limit to 5 queries in one run.",
        model=llm_instance,
        tools=[
            YFinanceTools,
            GoogleSearchTools(),
            generic_file_tools
        ],
        instructions=[
            "IMPORTANT : USE ONLY VALID UTF8 characters, USE MD outputs preferably wherever possible.",
            "Input: JSON with keys: `id`, `description`, `agent_id=\"ResearchAgent\"`, `call_name`, `inputs`, `outputs`.",
            "1. **Load Inputs:**",
            "   - For each filename in `inputs` (unless `NONE`):",
            "     • Announce “Reading input file \"<filename>\"…”",
            "     • Use your file tool to read its contents into `prepared_input`.",
            "2. **Search & Fetch Sources:**",
            "   a. Identify keywords from `prepared_input` or `description`.",
            "   b. IF NEEDED Academic Searches:",
            "      • Form 3-4 queries (e.g., Google Scholar).",
            "      • Use your search tool for each. Collect title, abstract, URL.",
            "   c. Web/News Searches:",
            "      • Form 3-4 queries (news sites, reports).",
            "      • Use your search tool. Collect title, snippet, URL.",
            "   d. Save your sources for raw_sources,json",
            "3. **Build `raw_sources.json`:**",
            "   - Create JSON array with fields: `type`, `title`, `URL`, `abstract_or_snippet`, `local_text_path`.",
            "   - Call `save_file filename: \"raw_sources.json\" content: \"<JSON>\"`.",
            "4. **Identify Claims:**",
            "   - Extract “key claims” about the research topic into `facts_list.md`.",
            "5. **Data Extraction & Analysis (if needed):**",
            "   - Scan `extracted_contents/` for tables or CSV blocks.",
            "   - If found:",
            "     • Write Python script to load into Pandas, compute summaries, save charts as `data_chartX.png`.",
            "     • Send JSON to `e2-bcode-execution-agent`: “{ \\\"call_name\\\": \\\"run_python_analysis\\\", \\\"code_to_execute\\\": \\\"<script>\\\" }”.",
            "     • On success, collect stdout or files, create `data_summary.md`, call `save_file filename: \"data_summary.md\" content: \"<contents>\"`.",
            "   - If no numeric data, create empty `data_summary.md` and save it.",
            "6. **Final Output:** Ensure `raw_sources.json`, `extracted_contents/`, `fact_check_log.md`, `data_summary.md (IF made)` exist. End with:",
            "   TASK_STEP_COMPLETED: Task \"<description>\" (ID: \"<id>\") completed. Outputs: raw_sources.json, fact_check_log.md, data_summary.md (IF made)."
        ],
        markdown=True, stream=True, stream_intermediate_steps=True,
    )
    composeragent = Agent(
        name="ComposerAgent",
        role="An agent specialized in composing the results of a research into a coherent final report. I can save the content to a file if instructed.",
        model=llm_instance,
        tools=[
            GoogleSearchTools(),
            generic_file_tools  
        ],
        instructions=[
            "Your mission is to execute the task described in the input by reading all source files and then writing one final report file. Any files you save must be MD files wherever optimal and possible.",
            "**CRITICAL RULE:** You MUST NOT generate conversational text, announcements, or status updates in your response. Your *only* valid output is a JSON object representing a call to one of your available tools (`read_file`, `save_file`).",

            "**Your Workflow:**",
            "1. **Analyze the Task:** First, understand the user's request from the `description` and identify the input files from `inputs` and the target output file from `outputs`.",
            "2. **Read All Input Files:** Use the `read_file` tool one by one for each file listed in the `inputs` array to load all necessary information into your context.",
            "3. **Synthesize and Compose:** After reading all files, formulate the complete, final report in your internal thought process. The report should be well-structured, coherent, and directly address the user's request. Do not output this thought process.",
            "4. **Save the Final Output:** Once the entire report is composed, make a *single* call to the `save_file` tool.",
            "   - The `filename` parameter must be the value from the `outputs` array (e.g., 'tesla_stock_report.md').",
            "   - The `content` parameter must contain the full, final, and complete text of the report you composed.",
            "5. Respond with a success message, stating that the research is done."
        ],
        markdown=True,
    )
    step_executor_team = Team(
        name="StepExecutorTeam",
        model=llm_instance,
        tools=[], 
        members=[
            e2b_code_execution_agent,
            composeragent,researchagent 
        ],
        instructions=[
      "/no_think. You receive one task object (JSON) with keys: `id`, `description`, `agent_id`, `call_name`, `inputs`, `outputs`.",
      "",
      "1. **Announce Task:**\n"
      "   - “Executing task \"<id>\": <description> using agent \"<agent_id>\" for \"<call_name>\".”",
      "",
      "2. **Load Inputs (if any):**\n"
      "   - For each filename in `inputs` (unless `NONE`):\n"
      "     • use your file tools to return its contents. Combine into `prepared_input`.",
      "",
      "3. **Prepare Specialist Call:**\n"
      "   - If `agent_id` == `e2-bcode-execution-agent`:\n"
      "     • Build JSON: `{ \"call_name\": \"<call_name>\", \"code_to_execute\": \"<script or description>\" }`. \n"
      "       – If `inputs` included a script file, read it and embed its text as `code_to_execute`.\n"
      "   - Else (`ResearchAgent` or `ComposerAgent`):\n"
      "     • Write a brief instruction combining `call_name`, `description`, any `prepared_input`, and the first output filename (`outputs[0]`).",
      "",
      "4. **Invoke Specialist & Save Output:**\n"
      "   - Let `raw_output` = specialist’s response.\n"
      "   - If `agent_id` == `e2-bcode-execution-agent`:\n"
      "     • Parse `raw_output` as JSON. If parse fails or `exit_code != 0`, go to error.\n"
      "     • Otherwise, set `content_to_save = parsed.stdout`.\n"
      "   - If `outputs` is non-empty:\n"
      "     • Let `filename = outputs[0]`, `content = content_to_save` (or `raw_output`).\n"
      "     • Call `file-writer-agent` with:  \n"
      "       `save_file filename: \"<filename>\" content: \"<content>\"`  \n"
      "     • Announce: “Content saved to \"<filename>\".”",
      "",
      "5. **Final Status Line:**\n"
      "   - On success:\n"
      "     `TASK_STEP_COMPLETED: Task \"<description>\" (ID: \"<id>\") completed. Output: \"<filename or N/A>\". Result: <brief summary or stdout>.`\n"
      "   - On failure (E2B parse error or `exit_code != 0`):\n"
      "     `TASK_STEP_ERROR: Task \"<description>\" (ID: \"<id>\") failed. Reason: <stderr or parse error>.`/no_think"
    ],
        expected_output="""- On success: 'TASK_STEP_COMPLETED: Task \"[task.description from input]\" completed. Output file `[task.outputs[0] if an output file was specified, else 'N/A']` processed. Result: [summary].'
    - On failure: 'TASK_STEP_ERROR: Task \"[task.description from input]\" failed. Reason: [brief reason].'""",
        markdown=True,
        show_tool_calls=True, 
        show_members_responses=True,
        add_member_tools_to_system_message=False, 
        debug_mode=True,reasoning=False,reasoning_max_steps=0
    )
    return step_executor_team