import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
# from google.ai.generativelanguage_v1 import Tool

class Chatbot:
    def __init__(self):
        dotenv.load_dotenv()
        if "GOOGLE_API_KEY" not in os.environ:
            assert os.path.exists(".env"), "Please create a .env file with your Google API key"
            
        self.chatbot = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=512,
            timeout=512,
        )

        self.prompt = ChatPromptTemplate(
            [
                ("system", "You are a helpful assistant that answer users' questions in a chatroom."),
                ("human", "{input}")
            ]
        )

        self.chain = self.prompt | self.chatbot

    def get_response(self, prompt, chat_log):
        prompt = "Previous chat log:\n" + chat_log + "\n\nAnswer the question:\n" + prompt
        response = self.chain.invoke(prompt)
        return response