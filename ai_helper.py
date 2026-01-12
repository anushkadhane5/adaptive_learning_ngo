import streamlit as st
from openai import OpenAI

# Explicitly load key from Streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_ai(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI tutor who explains concepts simply to students."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0.4,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()
