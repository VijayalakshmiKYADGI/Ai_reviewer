from langchain_google_genai import ChatGoogleGenerativeAI
import os


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1
)
response = llm.invoke("Say hello in one sentence.")
print(response)