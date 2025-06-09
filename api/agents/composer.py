

from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.spider import SpiderTools
from api.config import default_llm, generic_file_tools  
import os


if not os.getenv("SPIDER_API_KEY"):
    print("Warning: SPIDER_API_KEY environment variable not set. SpiderTools may fail.")

composeragent = Agent(
    name="ComposerAgent",
    role="An agent specialized in composing the results of a research into a coherent final report. I can save the content to a file if instructed.",
    model=default_llm,
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
