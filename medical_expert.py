"""
Medical Case Trainer - CME Application for Physicians

This Streamlit application provides an interactive learning experience for physicians
to work through a cardiac case and earn CME credits. The application uses the Agno
framework for intelligent interaction and case progression with persistent storage
and an enhanced continuous chat feature.
"""

import streamlit as st
import json
import uuid
from datetime import datetime

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage

api_key = st.secrets["API_KEY"]

# Constants
APP_TITLE = "Medical Case Trainer for CME"

# Setup page config
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the fixed sequence of case stages
CASE_SEQUENCE = ["initial", "treatment", "catheterization", "post_intervention"]

# Sample cardiac case data
CARDIAC_CASE = {
    "title": "58-year-old with Acute Chest Pain",
    "specialty": "Cardiology",
    "difficulty": "Moderate",
    "content": """
# Case: 58-year-old with Acute Chest Pain

## Initial Presentation
A 58-year-old male presents to the emergency department with sudden onset severe chest pain that began 2 hours ago while mowing his lawn. The pain is described as crushing, radiating to the left arm and jaw, and is rated 8/10 in severity. The patient reports shortness of breath and diaphoresis. He has a history of hypertension, hyperlipidemia, and type 2 diabetes. Current medications include lisinopril, atorvastatin, and metformin. He smokes one pack of cigarettes daily for the past 30 years.

Initial vital signs:
- BP: 165/95 mmHg
- HR: 96 bpm
- RR: 22/min
- Temp: 98.6°F (37°C)
- SpO2: 94% on room air

## Lab Results
### Complete Blood Count
- WBC: 9.8 x 10^9/L (normal: 4.5-11.0)
- Hgb: 14.2 g/dL (normal: 13.5-17.5)
- Hct: 42% (normal: 41-53%)
- Platelets: 245 x 10^9/L (normal: 150-450)

### Comprehensive Metabolic Panel
- Na: 138 mEq/L (normal: 135-145)
- K: 4.2 mEq/L (normal: 3.5-5.0)
- Cl: 101 mEq/L (normal: 98-107)
- CO2: 24 mEq/L (normal: 22-30)
- BUN: 18 mg/dL (normal: 7-20)
- Cr: 1.1 mg/dL (normal: 0.6-1.2)
- Glucose: 168 mg/dL (normal: 70-99)

### Cardiac Enzymes
- Troponin I: 0.32 ng/mL (normal: <0.04)
- CK-MB: 8.5 ng/mL (normal: <5.0)

### Lipid Panel
- Total Cholesterol: 235 mg/dL (normal: <200)
- LDL: 155 mg/dL (normal: <100)
- HDL: 38 mg/dL (normal: >40)
- Triglycerides: 210 mg/dL (normal: <150)

## Diagnostic Imaging
### EKG Findings
12-lead EKG shows 2 mm ST-segment elevation in leads II, III, and aVF with reciprocal ST depression in leads I and aVL.

### Optimal Management Path
Initial treatment should include aspirin 325 mg, sublingual nitroglycerin, and morphine for pain. This should be followed by immediate cardiac catheterization which will reveal a 95% occlusion of the right coronary artery. Percutaneous coronary intervention (PCI) with drug-eluting stent placement is the optimal treatment. Post-intervention therapy should include dual antiplatelet therapy, high-intensity statin, beta-blocker, and ACE inhibitor.

### Learning Points
1. Classic presentation of acute STEMI includes crushing chest pain radiating to the arm and jaw, associated with shortness of breath and diaphoresis.
2. Inferior wall MIs typically present with ST elevation in leads II, III, and aVF.
3. Primary PCI is the preferred reperfusion strategy for STEMI when available in a timely manner.
4. Optimal medical therapy post-MI includes dual antiplatelet therapy, statins, beta-blockers, and ACE inhibitors.
5. Risk factor modification, including smoking cessation, is crucial for secondary prevention.

### Correct Path Indicators
- Initial workup: Complete Blood Count, Metabolic Panel, and EKG
- Initial treatment: Administer aspirin and nitroglycerin
- Definitive treatment: Perform immediate cardiac catheterization
- Intervention: Percutaneous Coronary Intervention (PCI) with stent
- Secondary prevention: Comprehensive post-MI care (DAPT, statin, beta-blocker, ACE inhibitor)
"""
}

# User identification - in a real app, this would come from authentication
if "user_id" not in st.session_state:
    # Generate a unique user ID for this session
    st.session_state.user_id = str(uuid.uuid4())

# Application states
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "case_history" not in st.session_state:
    st.session_state.case_history = []
if "user_decisions" not in st.session_state:
    st.session_state.user_decisions = []
if "case_completed" not in st.session_state:
    st.session_state.case_completed = False
if "case_started" not in st.session_state:
    st.session_state.case_started = False
if "agent" not in st.session_state:
    st.session_state.agent = None
if "cme_earned" not in st.session_state:
    st.session_state.cme_earned = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_processing" not in st.session_state:
    st.session_state.chat_processing = False


class MedicalCaseAgent:
    """Handles the agent interactions for medical case training."""
    
    @staticmethod
    def initialize_agent(user_id, case_id="case-001"):
        """Initialize the Agno agent with persistent storage."""
        agent = Agent(
            model=OpenAIChat(id="gpt-4o",api_key="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"),
            # Store agent sessions in a database
            storage=SqliteAgentStorage(
                table_name="medical_trainer_sessions", 
                db_file="data/medical_trainer.db"
            ),
            # Use a session ID that combines user and case
            session_id=f"user_{user_id}_case_{case_id}",
            # Include chat history in context
            add_history_to_messages=True,
            description="""
            You are an expert medical educator specializing in case-based learning for physicians.
            Your role is to guide medical professionals through realistic patient cases,
            presenting clinical information in stages and evaluating their decision-making.
            """,
            instructions=[
                "Present medical case information in a clear, professional manner",
                "Provide realistic lab values and clinical findings at each step",
                "Track the user's decisions throughout the case progression",
                "Evaluate final outcomes based on the clinical decisions made",
                "Provide educational feedback that references medical literature",
                "Remember that there is often one optimal path, but alternative approaches may still be acceptable",
                "When answering questions about the case, remember where the user is in the case progression",
                "Do not reveal future steps or diagnoses when answering questions"
            ],
            markdown=True,
        )
        return agent
    
    @staticmethod
    def start_case(agent):
        """Start a new medical case by retrieving the initial presentation."""
        # Get the case content
        case_content = CARDIAC_CASE["content"]
        
        prompt = f"""
        You'll be facilitating a medical case for a physician learner.
        
        Here is the full case information for your reference (the learner won't see all of this yet):
        
        {case_content}
        
        Present only the initial clinical presentation with:
        1. Brief patient demographics
        2. Chief complaint
        3. Key history elements
        4. Initial vital signs
        
        Do not reveal the diagnosis or full case details yet. Wait for the user to request labs or choose an initial intervention.
        """
        
        response = agent.run(prompt)
        return response.content
    
    @staticmethod
    def get_case_options(step_index):
        """Return predefined options for each step in the sequence."""
        options = [
            # Step 0 - Initial workup (initial)
            [
                "Complete Blood Count, Metabolic Panel, and EKG", 
                "Cardiac enzymes and 12-lead EKG", 
                "Chest X-ray and cardiac monitoring",
                "CT angiogram with contrast"
            ],
            
            # Step 1 - Initial treatment (treatment)
            [
                "Administer aspirin and nitroglycerin", 
                "Perform immediate cardiac catheterization", 
                "Start thrombolytic therapy",
                "Begin full-dose anticoagulation with heparin"
            ],
            
            # Step 2 - Catheterization intervention (catheterization)
            [
                "Percutaneous Coronary Intervention (PCI) with stent", 
                "Medical management with anticoagulation", 
                "Coronary artery bypass grafting (CABG)",
                "Balloon angioplasty without stent placement"
            ],
            
            # Step 3 - Post-intervention management (post_intervention)
            [
                "Initiate dual antiplatelet therapy, high-intensity statin, beta-blocker, and ACE inhibitor",
                "Administer aspirin only and continue previous medications",
                "Start therapeutic anticoagulation with low molecular weight heparin for 3 months",
                "Arrange outpatient cardiac rehabilitation without medication changes"
            ]
        ]
        
        # Return appropriate options based on the step
        if step_index < len(options):
            return options[step_index]
        else:
            return ["Option 1", "Option 2", "Option 3", "Option 4"]  # Default fallback
    
    @staticmethod
    def progress_case(agent, action, step_index):
        """Progress the case based on the user's selected action."""
        # Get the case content
        case_content = CARDIAC_CASE["content"]
        
        # Build the conversation history
        history = "\n\n".join(st.session_state.case_history)
        decisions = "\n".join([f"Step {i+1}: {decision}" for i, decision in enumerate(st.session_state.user_decisions)])
        
        # Get the current stage based on the step index
        if step_index < len(CASE_SEQUENCE):
            current_stage = CASE_SEQUENCE[step_index]
        else:
            current_stage = "post_intervention"  # Default to post-intervention for any extra steps
        
        # Determine if this action is a correct one
        action_lower = action.lower()
        case_near_complete = False
        
        # Fixed sequence of prompts based on step index, not dependent on content analysis
        if step_index == 0:  # Initial labs/workup
            prompt = f"""
            Case reference (not to be fully revealed to the learner yet):
            {case_content}
            
            Conversation history:
            {history}
            
            The physician has requested: "{action}"
            
            Provide appropriate initial lab results, imaging findings, or other requested clinical data.
            Be sure to include EKG findings that show ST elevation and elevated troponin.
            Then present the patient's CURRENT STATUS and ask what initial intervention they would like to pursue.
            
            DO NOT PROVIDE ANY OPTIONS yourself as these will be pre-defined in the interface.
            """
        elif step_index == 1:  # Initial treatment
            prompt = f"""
            Case reference:
            {case_content}
            
            Conversation history:
            {history}
            
            Physician decisions so far:
            {decisions}
            
            The physician has chosen: "{action}"
            
            Advance the case by:
            1. Describing the patient's response to initial treatment
            2. Explaining that the cardiologist recommends immediate cardiac catheterization
            3. Describe the findings from the coronary angiography showing 95% occlusion of the right coronary artery
            4. Ask what intervention they would recommend for this catheterization finding
            
            DO NOT PROVIDE ANY OPTIONS yourself as these will be pre-defined in the interface.
            """
        elif step_index == 2:  # Catheterization intervention
            prompt = f"""
            Case reference:
            {case_content}
            
            Conversation history:
            {history}
            
            Physician decisions so far:
            {decisions}
            
            The physician has chosen: "{action}"
            
            Advance the case by:
            1. Describing that the PCI with stent placement procedure was successful
            2. Detailing the immediate post-procedure results and patient status
            3. Explaining that the patient is now stable post-PCI
            4. Ask what post-intervention management plan they would like to implement
            
            DO NOT PROVIDE ANY OPTIONS yourself as these will be pre-defined in the interface.
            """
        elif step_index == 3:  # Post-intervention management
            # Check if this is the correct comprehensive post-MI care
            if (
                ("dual antiplatelet" in action_lower or "dapt" in action_lower) and
                ("statin" in action_lower) and
                (("beta" in action_lower and "blocker" in action_lower) or "ace" in action_lower)
            ):
                case_near_complete = True
                prompt = f"""
                Case reference:
                {case_content}
                
                Conversation history:
                {history}
                
                Physician decisions so far:
                {decisions}
                
                The physician has chosen: "{action}"
                
                This is the correct comprehensive post-MI approach and completes the case management.
                
                Provide:
                1. A detailed description of the positive outcome for the patient
                2. A comprehensive explanation of why this was the optimal approach
                3. An educational summary of the key learning points from this case
                4. Evidence-based rationale with 2-3 specific literature references
                5. Explicitly congratulate the physician on completing the case successfully
                6. State that they have earned CME credit for this case completion
                
                Make your response comprehensive and educational, suitable for medical CME credit.
                """
            else:
                prompt = f"""
                Case reference:
                {case_content}
                
                Conversation history:
                {history}
                
                Physician decisions so far:
                {decisions}
                
                The physician has chosen: "{action}"
                
                The patient has already had a successful PCI with stent placement.
                
                Explain what is missing or suboptimal about their post-PCI care selection.
                
                Clearly explain that guidelines recommend comprehensive secondary prevention with DAPT, 
                statin, beta-blocker, and ACE inhibitor therapy post-MI.
                Ask what post-intervention management they would like to choose instead.
                
                DO NOT PROVIDE ANY OPTIONS yourself as these will be pre-defined in the interface.
                """
        else:  # Any extra steps
            prompt = f"""
            Case reference:
            {case_content}
            
            Conversation history:
            {history}
            
            Physician decisions so far:
            {decisions}
            
            The physician has chosen: "{action}"
            
            Provide feedback on this decision and ask if they would like to make any additional changes
            to their management plan.
            
            DO NOT PROVIDE ANY OPTIONS yourself as these will be pre-defined in the interface.
            """
        
        response = agent.run(prompt)
        
        # Mark case as completed if this was the final successful step
        if case_near_complete:
            st.session_state.case_completed = True
            st.session_state.cme_earned = True
        
        return response.content
    
    @staticmethod
    def ask_question(agent, question, step_index):
        """Allows the user to ask questions about the case with appropriate context."""
        # Get the case content for context
        case_content = CARDIAC_CASE["content"]
        
        # Build the conversation history
        history = "\n\n".join(st.session_state.case_history)
        decisions = "\n".join([f"Step {i+1}: {decision}" for i, decision in enumerate(st.session_state.user_decisions)])
        
        # Get the current stage of the case
        if step_index < len(CASE_SEQUENCE):
            current_stage = CASE_SEQUENCE[step_index]
        else:
            # If we're beyond the defined stages, we're in the post-case review
            current_stage = "case_review"
        
        # Create a prompt that maintains awareness of the current stage
        prompt = f"""
        The physician has a question about the current case:
        
        "{question}"
        
        Case reference (for your understanding only):
        {case_content}
        
        Current case progression:
        - Step index: {step_index}
        - Current stage: {current_stage} 
        - Case history: {history}
        - Decisions made: {decisions}
        - Case completed: {"Yes" if st.session_state.case_completed else "No"}
        
        Please answer their question knowledgeably while considering:
        1. Where they currently are in the case (step {step_index}, {current_stage} stage)
        2. What they already know based on the case history
        3. What would be appropriate educational content without revealing future diagnostics or treatments
        
        If they ask about what to do next, guide them to use the decision interface instead of directly telling them.
        If they ask about content that hasn't been revealed yet, explain that it would be premature to discuss that
        at the current stage of the case.
        
        If the case is completed, you can provide more comprehensive information as they have already
        finished the case scenario.
        
        Respond as an experienced medical educator providing guidance during a case-based learning session.
        """
        
        response = agent.run(prompt)
        return response.content


def process_chat_input():
    """Process the chat input when Enter is pressed."""
    user_question = st.session_state.chat_input
    if user_question and not st.session_state.chat_processing:
        # Set processing flag to prevent multiple submissions
        st.session_state.chat_processing = True
        
        # Get response
        response = MedicalCaseAgent.ask_question(
            st.session_state.agent,
            user_question,
            st.session_state.current_step
        )
        
        # Add to chat history
        st.session_state.chat_history.append({"question": user_question, "answer": response})
        
        # Clear the input
        st.session_state.chat_input = ""
        
        # Reset processing flag
        st.session_state.chat_processing = False
        
        # Rerun to update the interface
        st.rerun()


def render_chat_interface():
    """Render the chat interface."""
    # Create a visually distinct chat container
    chat_container = st.container(border=True)
    
    with chat_container:
        st.markdown("### 💬 Ask the Medical Educator")
        st.markdown("*Ask any questions about the case, medical concepts, or guidelines*")
        
        # Add previous chat history
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history:
                with st.container(border=True):
                    st.markdown(f"**Question:** {chat['question']}")
                    st.markdown(f"**Answer:** {chat['answer']}")
        
        # Add chat input with Enter key support
        st.text_input(
            "Your question:",
            key="chat_input",
            on_change=process_chat_input,
            placeholder="Type your question here and press Enter"
        )


def render_case_selection():
    """Render the case selection screen."""
    st.title("📋 Medical Case Trainer")
    
    # Initialize agent if not already done
    if not st.session_state.agent:
        st.session_state.agent = MedicalCaseAgent.initialize_agent(
            user_id=st.session_state.user_id
        )
    
    # Display CME credits earned
    if st.session_state.cme_earned:
        st.sidebar.header("Your CME Credits")
        st.sidebar.success(f"✅ {CARDIAC_CASE['title']} - 1.0 CME Credit")
    
    # Display case card
    st.subheader("Available Case")
    
    # Create card-like container
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {'✅ ' if st.session_state.cme_earned else ''}{CARDIAC_CASE['title']}")
            st.markdown(f"**Specialty:** {CARDIAC_CASE['specialty']}")
            st.markdown(f"**Difficulty:** {CARDIAC_CASE['difficulty']}")
            st.markdown("This case presents a patient with acute chest pain and guides you through diagnostic "
                        "workup, intervention decisions, and management of a potential cardiac emergency.")
            
            if st.session_state.cme_earned:
                st.success("CME Credit Earned")
        
        with col2:
            # Center the button
            st.write("")
            st.write("")
            if st.button("Start Case", use_container_width=True):
                # Start the case
                initial_presentation = MedicalCaseAgent.start_case(
                    st.session_state.agent
                )
                
                # Set session state
                st.session_state.case_started = True
                st.session_state.current_step = 0
                st.session_state.case_history = [initial_presentation]
                st.session_state.user_decisions = []
                st.session_state.case_completed = False
                st.session_state.chat_history = []
                
                # Rerun to show case interface
                st.rerun()
    
    # Show CME information
    st.markdown("---")
    st.markdown("### About CME Credit")
    st.markdown("""
    This interactive case-based learning module offers CME credit upon successful completion.
    
    **Learning Objectives:**
    1. Recognize the clinical presentation of an acute myocardial infarction
    2. Understand the appropriate diagnostic workup for chest pain
    3. Identify the best treatment approach for STEMI
    4. Apply evidence-based guidelines for post-MI care
    
    Complete the case by making appropriate clinical decisions to earn your CME credit.
    """)


def render_case_interface():
    """Render the interactive case interface."""
    
    # Display the case header
    st.title("🏥 Medical Case Training")
    
    # Check if case is completed
    if st.session_state.case_completed:
        # Display congratulations banner
        st.success("## 🎉 Congratulations! Case Completed Successfully")
        
        # Display the certificate section
        st.markdown("""
        ### CME Certificate
        
        **This certifies that you have successfully completed:**
        """)
        
        st.info(f"#### {CARDIAC_CASE['title']}")
        
        st.markdown("""
        **Credits Earned:** 1.0 AMA PRA Category 1 Credit™
        
        This activity has been planned and implemented in accordance with the accreditation 
        requirements and policies of the Accreditation Council for Continuing Medical Education (ACCME).
        """)
        
        # Display the case evaluation
        st.markdown("## Case Summary and Evaluation")
        st.markdown(st.session_state.case_history[-1])
        
        # Display chat interface for final questions
        st.markdown("---")
        render_chat_interface()
        
        # Option to return to case selection
        st.button("Return to Home", type="primary", on_click=lambda: setattr(st.session_state, 'case_started', False))
        
        return
    
    # Progress tracker for ongoing case
    steps_in_case = 4  # Cardiac case has 4 key decision points
    progress_value = min(1.0, (st.session_state.current_step + 1) / steps_in_case)
    st.progress(progress_value)
    
    # Display current case information
    st.markdown(st.session_state.case_history[-1])
    
    # Add the chat interface for asking questions
    st.markdown("---")
    render_chat_interface()
    
    # Create a separation between case info/chat and decision section
    st.markdown("---")
    
    # Get the appropriate stage based on step index, following a fixed sequence
    current_step = st.session_state.current_step
    
    # Get options based on the current step index
    options = MedicalCaseAgent.get_case_options(current_step)
    
    # Action input based on current step
    step_headers = [
        "Initial Diagnostic Workup", 
        "Initial Treatment Decision", 
        "Catheterization Intervention",
        "Post-Intervention Management"
    ]
    
    current_header = "Decision Point"
    if current_step < len(step_headers):
        current_header = step_headers[current_step]
    
    st.markdown(f"### {current_header}")
    
    # Display options without hints or explanations
    selected_option = st.radio("Select your approach:", options, index=None)
    action = selected_option if selected_option else "No selection"
    
    # Action buttons
    submit_button = st.button("Submit Decision", type="primary", disabled=(not selected_option))
    if submit_button:
        # Record the decision
        st.session_state.user_decisions.append(action)
        
        # Progress the case
        next_info = MedicalCaseAgent.progress_case(
            st.session_state.agent,
            action,
            st.session_state.current_step
        )
        
        # Update session state
        st.session_state.case_history.append(next_info)
        st.session_state.current_step += 1
        
        # Rerun to update the interface
        st.rerun()
    
    # Show case history in the sidebar
    with st.sidebar:
        st.header("Case Progress")
        st.subheader("Decision History")
        
        for i, decision in enumerate(st.session_state.user_decisions):
            st.markdown(f"**Step {i+1}:** {decision}")
        
        # Show current stage information
        if current_step < len(CASE_SEQUENCE):
            current_stage = CASE_SEQUENCE[current_step]
            st.info(f"Current Stage: {current_stage.capitalize()}")
        
        # Option to restart case
        if st.button("Restart Case"):
            # Reset session state but keep the same case
            initial_presentation = MedicalCaseAgent.start_case(
                st.session_state.agent
            )
            
            st.session_state.current_step = 0
            st.session_state.case_history = [initial_presentation]
            st.session_state.user_decisions = []
            st.session_state.case_completed = False
            st.session_state.chat_history = []
            
            st.rerun()
        
        # Option to exit case
        if st.button("Exit Case"):
            st.session_state.case_started = False
            st.rerun()


def main():
    """Main application entry point."""
    st.sidebar.title("🏥 Medical Case Trainer")
    st.sidebar.markdown("Interactive CME for Physicians")
    
    # Display the appropriate interface based on application state
    if not st.session_state.case_started:
        render_case_selection()
    else:
        render_case_interface()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Medical Case Trainer")
    st.sidebar.markdown("Powered by Agno Framework")


if __name__ == "__main__":
    main()
