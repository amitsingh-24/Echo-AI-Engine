import os
import json
import re
import logging
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_groq import ChatGroq

tlogging = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def get_llm():
    return ChatGroq(model= "gemma2-9b-it", temperature = 0.5)

def generate_tutoring_response(subject, level, question, learning_style, background, language):
    llm = get_llm()
    prompt = _create_tutoring_prompt(subject, level, question, learning_style, background, language)
    logging.info(f"Generating tutoring response: {subject} | {level} | {learning_style}")
    response = llm([HumanMessage(content=prompt)])
    return _format_tutoring_response(response.content, learning_style)

def generate_quiz(subject, level, num_questions=5):
    llm = get_llm()
    prompt = _create_quiz_prompt(subject, level, num_questions)
    logging.info(f"Generating quiz: {subject} | {level} | {num_questions} questions")
    response = llm([HumanMessage(content=prompt)])
    return _parse_quiz_response(response.content, subject, num_questions)

def _create_tutoring_prompt(subject, level, question, learning_style, background, language):
    return f"""
You are an expert tutor in {subject} at the {level} level.

STUDENT PROFILE:
- Background knowledge: {background}
- Learning style preference: {learning_style}
- Language preference: {language}

QUESTION:
{question}

INSTRUCTIONS:
1. Provide a clear, educational explanation that directly addresses the question
2. Tailor your explanation to a {background} student at {level} level
3. Use {language} as the primary language
4. Format your response with appropriate markdown for readability

LEARNING STYLE ADAPTATIONS:
- For Visual learners: Include descriptions of visual concepts or mental models
- For Text-based learners: Provide clear, structured explanations
- For Hands-on learners: Include practical examples or exercises
"""

def _format_tutoring_response(content, learning_style):
    if learning_style == "Visual":
        return content + "\n\n*Note: Visualize these concepts as you read.*"
    elif learning_style == "Hands-on":
        return content + "\n\n*Tip: Try the examples yourself to reinforce learning.*"
    return content


def _create_quiz_prompt(subject, level, num_questions):
    return f"""
Create a {level}-level quiz on {subject} with exactly {num_questions} multiple-choice questions.

INSTRUCTIONS:
1. Each question appropriate for {level} students
2. Exactly 4 options (A, B, C, D)
3. Clearly mark the correct answer
4. Return valid JSON ONLY:
```json
[
  {{"question":"...","options":["...","...","...","..."],"correct_answer":"..."}},
  ...
]
```"""

def _parse_quiz_response(text, subject, num_questions):
    # Extract JSON block
    match = re.search(r'```json\s*(\[.*?\])\s*```', text, re.DOTALL)
    payload = match.group(1) if match else text
    try:
        data = json.loads(payload)
        if len(data) > num_questions:
            data = data[:num_questions]
        return data
    except json.JSONDecodeError:
        logging.warning("Failed to parse quiz, using fallback quiz.")
        return _create_fallback_quiz(subject, num_questions)

def _create_fallback_quiz(subject, num_questions):
    return [
        {"question": f"Sample {subject} Question #{i+1}",
         "options": ["A","B","C","D"],
         "correct_answer": "A"}
        for i in range(num_questions)
    ]