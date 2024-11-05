from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import os

class ActionRoute(BaseModel):
    """Define the action to be taken based on the user query."""
    action: Literal["search_jobs", "analyze_job", "freelancing_tips", "other"] = Field(
        ...,
        description="Determine which action to take based on the user question"
    )

env_file = find_dotenv()
load_dotenv(env_file)
gpt_key = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=gpt_key)
structured_llm = llm.with_structured_output(ActionRoute)

system = """You are a smart assistant specifically designed to help freelance programmers. Based on the user query, determine the correct action:
- If the user is looking to find jobs on freelance platforms, route to 'search_jobs'.
- If the user is asking for an analysis of specific job characteristics, route to 'analyze_job'.
- If the user is seeking general tips about the digital freelancing world, route to 'freelancing_tips'.
- For anything else, route to 'other'.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{input}"),
    ]
)

router = prompt | structured_llm

def get_router_decision(user_query: str) -> str:
    """Function to determine the action based on the user query."""
    result = router.invoke(input=user_query)
    return result.action
