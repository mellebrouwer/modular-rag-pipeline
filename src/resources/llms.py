import dotenv
from langchain_openai import ChatOpenAI

dotenv.load_dotenv()

chat_gpt_4o = ChatOpenAI(model="gpt-4o", temperature=0)
