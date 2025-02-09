import dotenv
from langchain_openai import OpenAIEmbeddings

dotenv.load_dotenv()

text_embedding_3_small = OpenAIEmbeddings(model="text-embedding-3-small")
text_embedding_3_large = OpenAIEmbeddings(model="text-embedding-3-large")
