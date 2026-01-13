# ai_helper.py
from openai import OpenAI
import streamlit as st

# Initialize the client with your API Key
# It's best to store this in st.secrets or an environment variable
client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")

def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling AI: {e}"

def generate_quiz_from_chat(messages):
    """
    Formats the chat history and asks AI to generate 3 questions.
    """
    # Filter only the text from the message tuples
    chat_context = "\n".join([f"{m[0]}: {m[1]}" for m in messages])
    
    quiz_prompt = f"""
    You are an educational assistant. Review this tutoring session transcript:
    ---
    {chat_context}
    ---
    Based ONLY on the topics discussed above, generate 3 Multiple Choice Questions.
    Format the output clearly:
    Q1: [Question]
    A) [Option] B) [Option] C) [Option] D) [Option]
    Correct Answer: [Letter]
    """
    return ask_ai(quiz_prompt)
