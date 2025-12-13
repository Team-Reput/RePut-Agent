import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_chroma import Chroma

DATA_DIR = "data/static_docs"
CHROMA_PATH = "chroma_db"

def load_env():
    env_path = Path(".") / ".env"
    if env_path.exists():
        load_dotenv(env_path)

def load_documents():
    docs = []
    if not os.path.exists(DATA_DIR):
        print(f"Data directory {DATA_DIR} does not exist.")
        return []
        
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith(".pdf"):
            path = os.path.join(DATA_DIR, fname)
            loader = PyPDFLoader(path)
            file_docs = loader.load()
            for d in file_docs:
                d.metadata["source_file"] = fname
            docs.extend(file_docs)
    return docs

def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
    )
    return splitter.split_documents(docs)

def build_and_save_index(chunks):
    # Clear out the database first to avoid duplicates
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # 1) Get embeddings model
    embeddings_model = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )
    
    print(f"Creating ChromaDB index with {len(chunks)} chunks...")
    
    # 2) Create ChromaDB from documents
    Chroma.from_documents(
        chunks, 
        embeddings_model, 
        persist_directory=CHROMA_PATH
    )

    print(f" ChromaDB index built and saved to {CHROMA_PATH}")

if __name__ == "__main__":
    load_env()
    docs = load_documents()
    print(f"Loaded {len(docs)} raw pages")
    if docs:
        chunks = split_documents(docs)
        print(f"Split into {len(chunks)} chunks")
        build_and_save_index(chunks)
    else:
        print("No documents found to ingest.")
