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
from email_utils import send_email


load_dotenv()

class TestQuestions(BaseModel):
    questions: list[str] = Field(description='List of exaclty 5 technical and skill-based questions.')

    # ===============================
    # NODE FUNCTIONS
    # ==============================

def evaluate_resume_rag(state: HiringState) -> Dict[str, Any]
    """Node 1: Evaluates the resume against JD using RAG engine."""
    resume_text = state.get('resume_text', "")
    job_description = state.get('job_description', "")

    if not resume_text or not job_description:
        return {'status': 'rejected ', "rag_evaluation_resaon": "Missing inputs."}
    
    evaluation = grade_resume_against_jd(job_description, resume_text)

    threshold = 70.0
    status = 'shortlisted' if evaluation.score >= threshold else 'rejected'

    return{
        'rag_evaluation_score': evaluation.score,
        'rag_evaluation_reason': evaluation.reason,
        'status': status,
        'human_approval_status': 'pending' if status == 'shortlisted' else 'rejected'
    }


def human_approval_shortlist(state: HiringState) -> Dict[str, Any]:
    """Node 2: Human-in-the-loop checkpoint for shortlist."""
    status = state.get("human_approval_status", 'pending')
    if status == 'approved':
        return {'status': 'online_test_scheduled'}
    return {'status':'rejected'}



def schedule_online_test(state: HiringState) -> Dict[str, Any]:
    """Node 3: Dynamically generates 5 online test questions based on resume & JD."""
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)
    parser = PydanticOutputParser(pydantic_object=TestQuestions)

    messages = [
        SystemMessage(content="You are an expert technical interviewer designing a custom online assessment test."),
        HumanMessage(content=(
            f"Based on this candidate's Resume: {state.get('resume_text', '')}\n\n"
            f"And this Job Description: {state.get('job_description', '')}\n\n"
            f"Here is an evaluation of the resume against the JD, highlighting key matches and missing requirements:\n"
            f"{state.get('rag_evaluation_reason', '')}\n\n"
            f"Generate exactly 5 questions that test the specific technical skills required for this role."
            f"Please focus specifically on assessing any missing requirements or weaker areas identified in the evaluation.\n"
            f"Format your response exactly like this:\n"
            f"{parser.get_format_instructions()}"

        ))
    ]

    try:
        response = llm.invoke(messages)
        test_questions = parser.invoke(response).questions
    except Exception as e:
        print(f"Error generating questions: {e}")
        # fallback
        test_questions = [
            "Explain your most complex project.",
            "How do you handle system failures?",
            "Write a brief pseudo-code for a task queue.",
            "Describe your experience with databases.",
            "How do you ensure code quality?"
        ]

        link = f"https://mock-assessment.com/test/{state.get('candidate_name', 'candidate').replace(' ', '').lower()}"

        # New: Send email for online test schedule
        candidate_email = state.get('candidate_email')
        if candidate_email:
            email_body = f"Hello {state.get('candidate_name', 'Candidate')},\n\n"
            email_body += f"Congratulations! Your resume has been shortlisted for the role.\n"
            email_body += "Please complete the following custom technical assessment at your earliest convenience:\n\n"
            email_body += f"Link: {link}\n\n"
            email_body += "Best of luck!\nAI Recruitment Team"

            send_email(candidate_email, "Action Required: Your Online Technical Assessment", email_body)

        return {
            'status': 'awaiting_test_completion',
            'online_test_link': link,
            'generated_questions': test_questions,
            'candidate_test_answers': [],
            'human_approval_status' : 'pending'
        }
    

def await_online_test_completion(state: HiringState) -> Dict[str, Any]:
    a=10

def conduct_ai_screening(state: HiringState) -> Dict[str, Any]:
    b=10


def human_approval_technical(state: HiringState) -> Dict[str, Any]:
    c=10

def rollout_offer(state: HiringState) -> Dict[str, Any]:
    d=10

# =======================
# EDGES (ROUTING LOGIC)
# ========================

def route_after_rag(state: HiringState) -> Literal['human_approval_shortlist', 'END']:
    e=10

def route_after_shortlist_approval(state: HiringState) -> Literal['schedule_online_test', 'END']:
    a=10


def route_after_screening_test(state: HiringState) -> Li['await_online_test_completion']:
    a=10





# ================================
# GRAPH COMPILATION
# ================================

def build_graph():
    builder = StateGraph(HiringState)

    builder.add_node('evaluate_resume_rag', evaluate_resume_rag)
    builder.add_node('human_approval_shortlist', human_approval_shortlist)
    builder.add_node('schedule_online_test', schedule_online_test)
    builder.add_node('await_online_test_completion', await_online_test_completion)
    builder.add_node('conduct_ai_screening', conduct_ai_screening)
    builder.add_node('human_approval_technical', human_approval_technical)
    builder.add_node('rollout_offer', rollout_offer)

    # EDGES
    builder.add_edge(START, 'evaluate_resume_rag')
    builder.add_conditional_edges(
        'evaluate_resume_rag',
         rou
    )






