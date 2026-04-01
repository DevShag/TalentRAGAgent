import os
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from src.state import HiringState
from src.rag_engine import grade_resume_against_jd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from src.email_utils import send_email

import streamlit as st

load_dotenv()

class TestQuestions(BaseModel):
    questions: list[str] = Field(description='List of exaclty 5 technical and skill-based questions.')

    # ===============================
    # NODE FUNCTIONS
    # ==============================

def evaluate_resume_rag(state: HiringState) -> Dict[str, Any]:
    """Node 1: Evaluates the resume against JD using RAG engine."""
    st.write("cv evaluation started")
    resume_text = state.get('resume_text', "")
    job_description = state.get('job_description', "")

    st.write(f"jd: {job_description} ")
    if not resume_text or not job_description:
        return {'status': 'rejected ', "rag_evaluation_resaon": "Missing inputs."}
    
    evaluation = grade_resume_against_jd(job_description, resume_text)

    st.write(f"rag score: {evaluation.score}")

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
    """Node 4: Human-in-the-llop checkpoint waiting for candidate to finish test."""
    status = state.get("human_approval_status", 'pending')
    if status == 'approved':
        return {"status": "screening_scheduled"}
    return{'status': 'rejected'}


def conduct_ai_screening(state: HiringState) -> Dict[str, Any]:
    """Node 5: Conduct AI Screening based on candidate's 5 custom test responses."""
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)

    questions = state.get('generated_questions', [])
    answers = state.get('candidate_test_answers', [])

    qa_pairs = "\n\n".join([f"Q{i+1}: {q}\nA: {a}" for i, (q, a) in enumerate(zip(questions, answers))])

    messages = [
        SystemMessage(content="You are an AI technical recuruiter grading a candidate's custom responses to an online assessment test."),
        HumanMessage(content=f"Resume: {state['resume_text']}\n\nJob Desc: {state['job_description']}\n\nCandidate's Test Submissions:\n{qa_pairs}\n\nEvaluate the candidate's answers based on correctness and depth. Provide a short summary of their performance, critique their answers, and clearly state 'pass' or 'fail' at the end.")
    ]

    response = llm.invoke(messages)
    feedback = response.content

    cleared = 'pass' in feedback.lower() and 'fail' not in feedback.lower()

    # Ensuring testing passes if they score well overall but prompt is tricky
    if state.get('rag_evaluation_score', 0) >= 80 and len(answers) >= 1:
        cleared = True

    next_status = "technical_scheduled" if cleared else "rejected"

    return{
        "screening_feedback": feedback,
        "status" : next_status,
        "human_approval_status": "pending" if cleared else 'rejected'
    }


def human_approval_technical(state: HiringState) -> Dict[str, Any]:
    """Node 6: Human-in-the-loop checkpoint for technical round."""
    status = state.get("human_approval_status", "pending")
    if status == "approved":
        return {'status': 'offer_generated'}
    return {'status': 'rejected'}

def rollout_offer(state: HiringState) -> Dict[str, Any]:
    """Node 7: Generates an Offer Letter."""
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    messages = [
        SystemMessage(content='You are an HR Executive drafting an offer letter.'),
        HumanMessage(content=f"Draft a 3-paragraph professional offer letter for {state['candidate_name']} for {state['job_description'][:300]}.")
    ]
    response = llm.invoke(messages)

    # NEW: Send email for offer letter
    candidate_email = state.get('candidate_email')
    if candidate_email:
        send_email(candidate_email, "Congratulations! Your Job Offer is Enclosed", response.content)

    return{
        'status': 'offer_generated',
        'technical_feedback': response.content
    }

# =======================
# EDGES (ROUTING LOGIC)
# ========================

def route_after_rag(state: HiringState) -> Literal['human_approval_shortlist', 'END']:
    if state.get('status') =='shortlisted':
        return 'human_approval_shortlist'
    return 'END'

def route_after_shortlist_approval(state: HiringState) -> Literal['schedule_online_test', 'END']:
    if state.get('status') =='online_test_scheduled':
        return 'schedule_online_test'
    return 'END'

def route_after_scheduling_test(state: HiringState) -> Literal['await_online_test_completion']:
    return 'await_online_test_completion'


def route_after_test_completion(state: HiringState) -> Literal['conduct_ai_screening', 'END']:
    if state.get('status') =='screening_scheduled':
        return 'conduct_ai_screening'
    return 'END'



def route_after_screening(state: HiringState) -> Literal['human_approval_technical', 'END']:
    if state.get('status') =='technical_scheduled':
        return 'human_approval_technical'
    return 'END'


def route_after_technical_approval(state: HiringState) -> Literal['rollout_offer', 'END']:
    if state.get('status') =='offer_generated':
        return 'rollout_offer'
    return 'END'




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
         route_after_rag,
         {'human_approval_shortlist': 'human_approval_shortlist',
          'END': END
          }
    )

    
    builder.add_conditional_edges(
        'human_approval_shortlist',
        route_after_shortlist_approval,
        {
            'schedule_online_test': 'schedule_online_test',
            'END': END
        }
    )


    builder.add_conditional_edges(
        'schedule_online_test',
        route_after_scheduling_test,
        {
            'await_online_test_completion': 'await_online_test_completion'
        }
    )


    builder.add_conditional_edges(
        'await_online_test_completion',
        route_after_scheduling_test,
        {
            'conduct_ai_screening': 'conduct_ai_screening',
            'END': END
        }
    )


    builder.add_conditional_edges(
        'conduct_ai_screening',
        route_after_test_completion,
        {
            'human_approval_technical': 'human_approval_technical',
            'END' : END
        }
    )


    builder.add_conditional_edges(
        'human_approval_technical',
        route_after_technical_approval,
        {
            'rollout_offer': 'rollout_offer',
            'END': END
        }
    )


    builder.add_edge('rollout_offer', END)


    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before = ['human_approval_shortlist','await_online_test_completion', 'human_approval_technical']

    )



    return graph

app_graph = build_graph()






