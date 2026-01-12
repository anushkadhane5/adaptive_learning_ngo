import streamlit as st
from openai import OpenAI

def ask_ai(question: str) -> str:
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}],
            max_tokens=50
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI ERROR → {type(e).__name__}: {e}"
