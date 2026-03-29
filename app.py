import streamlit as st
import os
import uuid
import re
from dotenv import load_dotenv

from rag_engine import extract_text

load_dotenv()


st.set_page_config(page_title="AI Recruitment Automation", layout="wide")
st.title("AI-Powered Recruitment Automation")
st.markdown("Automating resume screening & dynamic interview scheduling with Langgraph")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY is not set in the environment variable")
    st.stop()


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


config = {"configurable": {"thread_id": st.session_state.thread_id}}
#current_state = app_graph.get_state(config)


# ================================
# TAB SETUP
# ================================
tab_hr, tab_candidate = st.tabs(["HR Dashboard", "Candidate Portal"])


with tab_hr:
    st.sidebar.header("1. Setup")
    job_desc = st.sidebar.text_area("Job Description", height=200, placeholder="Enter the job description...")
    pdf_file = st.sidebar.file_uploader("Upload Resume", type=['pdf', 'docx'])

    
    if st.sidebar.button("Start Evaluation"):
        if job_desc and pdf_file:
            resume_text = extract_text(pdf_file)


            # Autonomously extract email directly from the CV text using regex pattern
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-ZA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
            extracted_email = email_match.group(0) if email_match else "candidate@example.com"

            st.session_state.thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": st.session_state.thread_id}}

            initial_state = {
                "candidate_name": pdf_file.name.replace(".pdf", ""),
                "candidate_email": extracted_email,
                "job_description": job_desc,
                "resume_text": resume_text,
                "rag_evaluation_score": 0.0,
                "rag_evaluation_reason": "",
                "status": "pending_evaluation",
                "online_test_link": "",
                "generated_questions": [],
                "candidate_test_answers": [],
                "candidate_test_answer": "",
                "human_approval_status": "pending",
                "screening_feedback": "",
                "technical_feedback": ""

            }
            
            st.write('### Running Graph...')
           # fro event
    
