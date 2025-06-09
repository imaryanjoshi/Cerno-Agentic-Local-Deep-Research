

from agno.agent import Agent
from agno.tools.spider import SpiderTools
from api.config import default_llm, generic_file_tools  
import os


if not os.getenv("SPIDER_API_KEY"):
    print("Warning: SPIDER_API_KEY environment variable not set. SpiderTools may fail.")

web_scraping_agent = Agent(
    name="WebScrapingAgent",
    role="An agent specialized in scraping web content from specific URLs using SpiderTools. I can save the scraped content to a file if instructed.",
    model=default_llm,
    tools=[
        SpiderTools(max_results=5),
        generic_file_tools  
    ],
    instructions=[
        "You receive a request to scrape content from one or more specific URLs.",
        "Use the 'scrape' function from SpiderTools, providing the URL.",
        "The tool will return the extracted content, usually in markdown or clean HTML format.",
        "If the request includes a target FILENAME, use your 'save_file' tool to save the scraped content to that file.Do not put your internal dialogue or reasoning in the saved file.",
        "Respond with a summary or excerpt of the content AND confirm the file save (e.g., 'Scraping complete. Content saved to `scraped_page.md`.').",
        "If no filename is provided, just return the scraped content.",
        "If scraping fails (e.g., invalid URL, access error), clearly report the issue in your response.",
        "Optionally, if a search query is given instead of a URL, use the 'search' function to find a relevant page, then scrape it. Use only UTF-8 characters",
    ],
    markdown=True,
)
