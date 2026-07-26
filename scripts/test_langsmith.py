import os
from dotenv import load_dotenv

def main():
    load_dotenv()

    print("=== LANGSMITH CONNECTION TEST ===")
    print(f"LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
    print(f"LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")
    print(f"LANGCHAIN_ENDPOINT: {os.environ.get('LANGCHAIN_ENDPOINT')}")
    
    api_key = os.environ.get('LANGCHAIN_API_KEY')
    if api_key:
        # Strip quotes if the user accidentally added them literally in the .env file
        api_key = api_key.strip('"').strip("'")
        os.environ['LANGCHAIN_API_KEY'] = api_key
        print(f"LANGCHAIN_API_KEY: {api_key[:15]}... (Length: {len(api_key)})")
    else:
        print("LANGCHAIN_API_KEY: Not found!")

    from langchain_google_genai import ChatGoogleGenerativeAI
    from app.core.config import settings

    print("\nInitializing ChatGoogleGenerativeAI...")
    try:
        chat = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0
        )
        print("Sending request to Gemini (tracing to LangSmith)...")
        res = chat.invoke("Hello LangSmith! Just reply with 'Ready' for tracing confirmation.")
        print(f"Gemini Response: {res.content}")
        print("\nSUCCESS! Tracing completed. Please check your LangSmith dashboard under project 'babycare-ai'.")
    except Exception as e:
        print(f"\nERROR: Failed to run test query. Details: {e}")

if __name__ == "__main__":
    main()
