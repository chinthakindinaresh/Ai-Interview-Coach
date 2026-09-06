import os
import re
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)

st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🤖"
)

st.title("🤖 AI Interview Coach")
st.write("Practice a complete interview with AI.")

# -----------------------------
# Session State
# -----------------------------

if "started" not in st.session_state:
    st.session_state.started = False

if "question_number" not in st.session_state:
    st.session_state.question_number = 0

if "question" not in st.session_state:
    st.session_state.question = ""

if "evaluated" not in st.session_state:
    st.session_state.evaluated = False

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "scores" not in st.session_state:
    st.session_state.scores = []


# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.header("Interview Settings")

role = st.sidebar.selectbox(
    "Select Job Role",
    [
        "Python Developer",
        "Java Developer",
        "Data Analyst",
        "Frontend Developer",
        "Full Stack Developer"
    ]
)

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"]
)

total_questions = st.sidebar.selectbox(
    "Number of Questions",
    [5, 10, 15],
    index=1
)


# -----------------------------
# Generate Question Function
# -----------------------------

def generate_question():

    prompt = f"""
    Act as a professional technical interviewer.

    Job Role: {role}
    Difficulty: {difficulty}

    This is interview question number {st.session_state.question_number}
    out of {total_questions}.

    Generate ONE technical interview question.

    Requirements:
    - Do not give the answer.
    - Do not repeat common previous questions.
    - Keep the question relevant to the job role.
    - Ask only the question.
    """

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return response.output_text


# -----------------------------
# Start Interview
# -----------------------------

if not st.session_state.started:

    st.info(
        f"Your interview will contain {total_questions} questions."
    )

    if st.button("🚀 Start Interview"):

        with st.spinner("Generating first question..."):

            st.session_state.started = True
            st.session_state.question_number = 1
            st.session_state.scores = []
            st.session_state.evaluated = False

            st.session_state.question = generate_question()

        st.rerun()


# -----------------------------
# Interview
# -----------------------------

if st.session_state.started:

    # Progress
    st.progress(
        st.session_state.question_number / total_questions
    )

    st.write(
        f"### Question {st.session_state.question_number} "
        f"of {total_questions}"
    )

    st.subheader("📝 Interview Question")

    st.write(st.session_state.question)

    # Answer
    answer = st.text_area(
        "Your Answer",
        height=180,
        key=f"answer_{st.session_state.question_number}",
        disabled=st.session_state.evaluated
    )

    # -------------------------
    # Evaluate Answer
    # -------------------------

    if not st.session_state.evaluated:

        if st.button("📊 Evaluate My Answer"):

            if not answer.strip():

                st.warning("Please enter your answer.")

            else:

                with st.spinner("AI is evaluating your answer..."):

                    prompt = f"""
                    You are an expert technical interviewer.

                    Job Role:
                    {role}

                    Difficulty:
                    {difficulty}

                    Question:
                    {st.session_state.question}

                    Candidate Answer:
                    {answer}

                    Evaluate the candidate answer.

                    Start your response exactly like this:

                    SCORE: X/10

                    Then provide:

                    1. What was correct
                    2. What was missing
                    3. How to improve
                    4. Better sample answer
                    """

                    response = client.interactions.create(
                        model="gemini-3.6-flash",
                        input=prompt
                    )

                    feedback = response.output_text

                    st.session_state.feedback = feedback

                    # Extract score
                    match = re.search(
                        r"SCORE:\s*(\d+)\s*/\s*10",
                        feedback,
                        re.IGNORECASE
                    )

                    if match:

                        score = int(match.group(1))

                    else:

                        score = 0

                    st.session_state.scores.append(score)

                    st.session_state.evaluated = True

                st.rerun()


    # -------------------------
    # Show Feedback
    # -------------------------

    if st.session_state.evaluated:

        st.subheader("📊 AI Feedback")

        st.write(st.session_state.feedback)

        current_question = st.session_state.question_number

        # ---------------------
        # Next Question
        # ---------------------

        if current_question < total_questions:

            if st.button("➡️ Next Question"):

                with st.spinner("Generating next question..."):

                    st.session_state.question_number += 1

                    st.session_state.question = generate_question()

                    st.session_state.evaluated = False

                    st.session_state.feedback = ""

                st.rerun()

        else:

            # -----------------
            # Final Result
            # -----------------

            st.success("🎉 Interview Completed!")

            total_score = sum(st.session_state.scores)

            max_score = total_questions * 10

            percentage = (total_score / max_score) * 100

            st.subheader("🏆 Final Result")

            st.metric(
                "Total Score",
                f"{total_score}/{max_score}"
            )

            st.metric(
                "Percentage",
                f"{percentage:.1f}%"
            )

            if percentage >= 80:

                st.success(
                    "🔥 Excellent! You are interview ready."
                )

            elif percentage >= 60:

                st.info(
                    "👍 Good performance. Keep practicing."
                )

            else:

                st.warning(
                    "📚 Keep practicing your technical concepts."
                )

            st.subheader("📈 Question-wise Scores")

            for i, score in enumerate(
                st.session_state.scores,
                start=1
            ):

                st.write(
                    f"Question {i}: **{score}/10**"
                )

            # Restart
            if st.button("🔄 Start New Interview"):

                st.session_state.started = False
                st.session_state.question_number = 0
                st.session_state.question = ""
                st.session_state.evaluated = False
                st.session_state.feedback = ""
                st.session_state.scores = []

                st.rerun()