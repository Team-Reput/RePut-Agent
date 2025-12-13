Jeremy – RePut ESG & Supply-Chain Assistant

A lightweight local RAG-based chatbot for RePut using Gemini + Gradio

Jeremy is an AI chatbot that answers questions about RePut, sustainability, traceability, circularity, and ESG data by reading real RePut PDF documents.
It uses a custom-built Retrieval-Augmented Generation (RAG) backend with Gemini embeddings and a Gradio chat UI.

⭐ Features

 Ingests and processes RePut PDFs
 
Performs semantic search using Gemini embeddings

Answers questions using Gemini chat models

Custom RAG pipeline using cosine similarity

 Clean chat UI with examples and suggestions

Runs entirely on your laptop (no cloud required except Gemini API key)

 How to Run Jeremy Locally

These instructions work for Windows, macOS, and Linux.

1️⃣ Prerequisites

Python 3.10 or 3.11

A Gemini API key
(Create one at https://aistudio.google.com
 or ask your teammate for a key)


2️⃣Set Up Environment

3. Open Terminal / CMD inside the project folder:

cd RAGchatbot_reput

4. python -m venv .venv
.venv\Scripts\activate

5. pip install -r requirements.txt

6. GOOGLE_API_KEY=your_gemini_api_key_here

7. Place RePut PDFs

8. Add the required PDFs inside:
data/static_docs/

9. Build the RAG Index
(This processes the PDFs and creates embeddings.)

python -m rag.ingest

Loaded X raw pages
Split into Y chunks
Computing embeddings...
✅ Custom index built and saved to index/

10. Launch Jeremy ---
python app.py

you'll see : Running on local URL:  http://127.0.0.1:7860






