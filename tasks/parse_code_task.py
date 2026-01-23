from textwrap import dedent
from crewai import Task, Agent
from tools import DiffParser, TreeSitterParser, DiffParsingTool
from data.models import ReviewInput

class ParseCodeTask:
    def __init__(self):
        self.diff_parser = DiffParser()
        self.tree_parser = TreeSitterParser()

    def create(self, agent: Agent, diff_content: str, pr_details: dict) -> Task:
        return Task(
            description=dedent(f"""\
                Analyze the provided PR diff content and extract metadata.
                
                PR Details:
                Repo: {pr_details.get('repo_name')}
                PR #{pr_details.get('pr_number')}
                
                Your job is to:
                1. Parse the diff content to identify changed files.
                2. Validate that valid Python code blocks can be extracted.
                3. Prepare the input for the next steps.
                
                DIFF CONTENT:
                {diff_content[:2000]}... (truncated if too long)
            """),
            expected_output="A structured summary of files changed and their validity for review.",
            agent=agent,
            tools=[
                DiffParsingTool()
            ],
            context=[] # No previous context
        )
