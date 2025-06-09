from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.spider import SpiderTools
from agno.tools.yfinance import YFinanceTools

from api.config import default_llm, generic_file_tools  
import os


if not os.getenv("SPIDER_API_KEY"):
    print("Warning: SPIDER_API_KEY environment variable not set. SpiderTools may fail.")

researchagent = Agent(
    name="ResearchAgent",
    role="An agent specialized in deep research. I can save the content to a file if instructed. Limit to 5 queries in one run.",
    model=default_llm,
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
  "3. **MUST Build `raw_sources.json`:**",
  "   - MUST Create JSON array with fields: `type`, `title`, `URL`, `abstract_or_snippet`, `local_text_path`.",
  "   - MUST Call `save_file filename: \"raw_sources.json\" content: \"<JSON>\"`.",
  "4. **Identify Claims:**",
  "   - Extract “key claims” about the research topic into `facts_list.md`.",
  "5. **Data Extraction & Analysis (if needed):**",
  "   - Scan `extracted_contents/` for tables or CSV blocks.",
  "   - If found:",
  "     • Write Python script to load into Pandas, compute summaries, save charts as `data_chartX.png`.",
  "     • Send JSON to `e2-bcode-execution-agent`: “{ \\\"call_name\\\": \\\"run_python_analysis\\\", \\\"code_to_execute\\\": \\\"<script>\\\" }”.",
  "     • On success, collect stdout or files, create `data_summary.md`, call `save_file filename: \"data_summary.md\" content: \"<contents>\"`.",
  "   - If no numeric data, create empty `data_summary.md` and save it.",
  "6. **Final Output:** Ensure `raw_sources.json`, `extracted_contents/`, `fact_check_log.md`, `data_summary.md (IF made)` exist. Make raw sources without exception if any sources are used. End with:",
  "   TASK_STEP_COMPLETED: Task \"<description>\" (ID: \"<id>\") completed. Outputs: raw_sources.json, fact_check_log.md, data_summary.md (IF made)."
],
    markdown=True,stream=True,stream_intermediate_steps=True,
)
