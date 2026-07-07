import chromadb
from openai import OpenAI
from PyPDF2 import PdfReader
from langchain.tools import tool

from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
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