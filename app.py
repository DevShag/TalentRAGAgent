import streamlit as st
import os
import uuid
import re
from dotenv import load_dotenv

from src.rag_engine import extract_text
from src.graph import app_graph
from langgraph.graph import START

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
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
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
            for event in app_graph.stream(initial_state, config):
                pass
            st.rerun()
    
    # Refresh current_state
    current_state = app_graph.get_state(config)
    
    
    if current_state and current_state.values:
        state_vals = current_state.values
        st.write('## Current Status: ', state_vals.get('status',"").upper())

        if state_vals.get('rag_evaluation_score', 0) > 0:
            st.info(f"**RAG Score:** {state_vals.get('rag_evaluation_score')}/100")
            st.write(f"**Evaluation Reason:** {state_vals.get('rag_evaluation_reason')}")

        next_node = current_state.next

        if "human_approval_shortlist" in next_node:
            st.warning("Human Approval Required: Candidate shortlisted by the RAG pipeline.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve Resume & Generate Custome Test"):
                    with st.spinner("Generating Agentic Custom Assessment based on Resume & JD..."):
                        app_graph.update_state(config, {"human_approval_status": "approved"})
                        for event in app_graph.stream(None, config):
                            pass
                    st.rerun()

            with col2:
                if st.button("Reject Candidate"):
                    app_graph.update_state(config, {'human_approval_status': 'rejected'})
                    for event in app_graph.stream(None, config):
                        pass
                    st.rerun()


        elif 'await_online_test_completion' in next_node:
            st.success('Custom Online Test has been successfully generated and scheduled!')
            st.code(state_vals.get('online_test_link', ""))
            if st.button("Reject, Candidate No-Show"):
                app_graph.update_state(config, {'human_approval_status': 'rejected'})
                for event in app_graph.stream(None, config):
                    pass
                st.rerun()


        elif "human_approval_technical" in next_node:
            st.success("Candidate completed Custom Online Test.")
            st.write("**AI Test Evaluation & Screening Feedback:**")
            st.info(state_vals.get("screening_feedback", "No feedback available"))
            st.warning("⚠️ Human Approval Required: Approve offering the candidate?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Finalize & Rollout Offer"):
                    app_graph.update_state(config, {"human_approval_status": "approved"})
                    for event in app_graph.stream(None, config):
                        pass
                    st.rerun()
            with col2:
                if st.button("❌ Reject Candidate"):
                    app_graph.update_state(config, {"human_approval_status": "rejected"})
                    for event in app_graph.stream(None, config):
                        pass
                    st.rerun()
                    
        elif state_vals.get("status") == "offer_generated":
            st.success("🎉 Candidate has been offered!")
            st.write("**Offer Letter Preview:**")
            st.text_area("Offer Letter", state_vals.get("technical_feedback"), height=300)
        elif state_vals.get("status") == "rejected":
            st.error("Candidate was rejected.")

with tab_candidate:
    st.header("Candidate Assessment Portal")
    if current_state and current_state.values:
        state_vals = current_state.values
        next_node = current_state.next
        
        if "await_online_test_completion" in next_node:
            st.info(f"Welcome to your custom skill evaluation assessment, **{state_vals.get('candidate_name', 'Candidate')}**!")
            st.write("---")
            
            questions = state_vals.get("generated_questions", [])
            answers_dict = {}
            
            # Use a form to group all submissions nicely
            with st.form("candidate_test_form"):
                st.subheader("Technical Questions")
                for i, q in enumerate(questions):
                    answers_dict[i] = st.text_area(f"Q{i+1}: {q}", height=150, key=f"q_{i}")
                
                submitted = st.form_submit_button("Submit Final Assessment")
                if submitted:
                    all_answered = all(len(ans.strip()) > 5 for ans in answers_dict.values())
                    if not all_answered:
                         st.error("Please provide an answer for every question.")
                    else:
                         answers_list = [answers_dict[i] for i in range(len(questions))]
                         app_graph.update_state(config, {
                             "human_approval_status": "approved",
                             "candidate_test_answers": answers_list
                         })
                         # Trigger graph progression
                         with st.spinner("Submitting test exactly to the AI evaluator..."):
                             for event in app_graph.stream(None, config):
                                 pass
                         st.success("Assessment submitted successfully! You may close this window. Switch to HR tab to see results.")
                         st.rerun()
                         
        elif state_vals.get("status") in ["screening_scheduled", "technical_scheduled", "offer_generated"]:
             st.success("Your assessment has been submitted and is under review by the AI. Thank you!")
        else:
            st.write("There are no active assessments scheduled for your profile.")
    else:
        st.write("Please start an evaluation on the Dashboard first.")





 