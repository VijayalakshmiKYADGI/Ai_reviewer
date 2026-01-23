from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv()

print(os.getenv("GEMINI_API_KEY"))
print(os.getenv("GEMINI_MODEL"))

llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL"),  # Changed to a compatible model
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.1
)
response = llm.invoke("Say hello in one sentence.")
print(response)