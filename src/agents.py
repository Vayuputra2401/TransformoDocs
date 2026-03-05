import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

class AgenticWorkflow:
    def __init__(self, rag_engine):
        """Initializes agents. Takes a configured RAGPipeline instance so agents can query the document."""
        self.llm = ChatOpenAI(temperature=0.1, model="gpt-4-turbo-preview")
        self.rag_engine = rag_engine

    def execute_analytical_query(self, user_query):
        """Runs the multi-agent system to answer a complex query using MCP servers/tools pattern."""

        # Define Agents
        researcher_agent = Agent(
            role='Senior Document Analyst',
            goal='Extract exact facts from the document context',
            backstory='An expert analyst who uses vector search databases to retrieve precise information and structure it meticulously.',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        synthesizer_agent = Agent(
            role='Data Reporting Specialist',
            goal='Synthesize raw facts into beautifully formatted, Chain-of-Thought answers.',
            backstory='A specialist in taking complex extracted facts and turning them into easy-to-understand summaries.',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # Since tools require a bit more setup in CrewAI to natively call our RAG instance,
        # we will extract top facts ourselves using the RAG and provide it as context to the Crew.
        # This simulates the tool-calling pattern while keeping complexity low for the prototype.
        context_data = self.rag_engine.query_document(user_query)

        # Define Tasks
        extraction_task = Task(
            description=f'Based on this extracted context: "{context_data}", identify all facts relevant to answering: "{user_query}"',
            agent=researcher_agent,
            expected_output='A bulleted list of raw facts extracted from the context.'
        )

        synthesis_task = Task(
            description=f'Take the facts identified by the analyst and formulate a comprehensive, polite response to the user query: "{user_query}"',
            agent=synthesizer_agent,
            expected_output='A highly readable, formatted final response string answering the user query.'
        )

        # Create Crew
        crew = Crew(
            agents=[researcher_agent, synthesizer_agent],
            tasks=[extraction_task, synthesis_task],
            process=Process.sequential,
            verbose=2
        )

        # Execute
        result = crew.kickoff()
        return result
