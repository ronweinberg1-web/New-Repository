import chromadb
from openai import OpenAI
from PyPDF2 import PdfReader
from langchain.tools import tool

from dotenv import load_dotenv
import os
from pathlib import Path

# 1. Locate this specific file (emb.py)
current_file_path = Path(__file__).resolve()

# 2. Travel up the directory tree to your project root
# current_file_path                      -> .../app/modules/embedding/emb.py
# current_file_path.parent               -> .../app/modules/embedding
# current_file_path.parents[0]           -> .../app/modules/embedding
# current_file_path.parents[1]           -> .../app/modules
# current_file_path.parents[2]           -> .../app/          
# current_file_path.parents[3]           -> .../New-Repository/ <- (If .env is here)

# Let's target 3 levels up (New-Repository root). Adjust the number if your structure differs.
project_root = current_file_path.parents[3] 
env_path = project_root / '.env'

load_dotenv(dotenv_path=env_path)  # Load variables from .env file
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="my_collection_openai")


def build_index():
    
    import os

    BASE_DIR = os.path.dirname(__file__)
    pdf_path = os.path.join(BASE_DIR, "Python Developer Job Description.pdf")

    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )

    embedding = response.data[0].embedding

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=["id1"]
    )


@tool
def get_job_info(user_input):
    """get details on the job description."""

    query_embedding = client.embeddings.create(
        input=[user_input],
        model="text-embedding-3-small"
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1
    )

    context = "\n".join(results["documents"][0])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Context details:\n{context}"},
            {"role": "user", "content": user_input}
        ]
    )

    return response.choices[0].message.content