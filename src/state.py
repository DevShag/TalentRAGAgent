from typing import TypedDict, Optional, List

class HiringState(TypedDict):
    # Core Information
    candidate_name: str
    candidate_email: str
    job_description: str
    resume_text: str

    # RAG Evalauation
    rag_evaluation_score: float
    rag_evaluation_reason: str

    # State tracking
    status: str # e.g., 'pending_evaluation', 'shortlisted', 'rejected', 'screening_scheduled', 'technical_scheduled', 'offer_generated'

    # Human-In-The-Loop Approvals
    human_approval_status: str # 'pending', 'approved', 'rejected'

    # Online Test details
    online_test_link: str
    generated_questions: List[str]
    candidate_test_answers: List[str]
    candidate_test_answer: str

    
    # Interview Feedback
    screening_feedback: str
    technical_feedback: str