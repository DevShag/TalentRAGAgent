import os
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from state import HiringState
from rag_engine import grade_resume_against_jd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
#from email_utils import send_email


load_dotenv()

class TestQuestions(BaseModel):
    questions: list[str] = Field(description='List of exaclty 5 technical and skill-based questions.')

    # ===============================
    # NODE FUNCTIONS
    # ==============================

    #def evaluate_resume_rag(state: HiringState) -> 