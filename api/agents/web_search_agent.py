
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.googlesearch import GoogleSearchTools

from api.config import default_llm,default_llm3, generic_file_tools 

web_search_agent = Agent(
    name="WebSearchAgent",
    role="An expert web researcher using DuckDuckGo. I can save my findings to a file if instructed.",
    model=default_llm,
    tools=[
        GoogleSearchTools(),
        generic_file_tools 
    ],
    instructions=[
        "You receive a task from the Orchestrator, which may include a query. The task description may contain an input filename. If it does, you must read the input filename using your filetools, and use that data to improve your research. The task_description will also contain an output_filename for your output.",
        "Perform the web search using your DuckDuckGo tools based on the query in the task description. Be detailed, but not make an excessive amount of API calls, only the minimum needed. Try to find multiple things in one API call if possible. Maximum 6 search api calls in one run. ",
        "Compile your findings into a comprehensive text.",
        "Then, you MUST use your 'save_file' tool to save your complete findings to that output_filename.",
        "Limit yourself to 3 web searches at a time",
        "Respond to the Orchestrator with a summary of your findings AND a confirmation that you have saved them to the specified file (e.g., 'Research complete. Findings saved to `search_results_X.md`.'). If no filename was given, just return your findings.",
    ],
    markdown=True,
    stream_intermediate_steps=True
)