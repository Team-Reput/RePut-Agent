import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_chroma import Chroma

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHROMA_PATH = "chroma_db"

# Global variables for singleton pattern
_vector_db = None
_llm = None

def load_env():
    env_path = Path(".") / ".env"
    if env_path.exists():
        load_dotenv(env_path)

def get_vector_db():
    """
    Returns a singleton instance of the Chroma vector database.
    """
    global _vector_db
    if _vector_db is None:
        logger.info("Initializing ChromaDB client...")
        load_env()
        embeddings_model = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=os.getenv("AWS_DEFAULT_REGION")
        )
        if not os.path.exists(CHROMA_PATH):
             logger.warning(f"ChromaDB path '{CHROMA_PATH}' does not exist. Please run ingestion.")
             # We can still return the object, but it might be empty.
        
        _vector_db = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings_model
        )
    return _vector_db

def get_llm():
    """
    Returns a singleton instance of the LLM.
    """
    global _llm
    if _llm is None:
        logger.info("Initializing AWS Bedrock Claude LLM...")
        load_env()
        _llm = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            model_kwargs={"temperature": 0.2}
        )
    return _llm

def build_prompt(question, context_text, history=[]):
    history_text = ""
    if history:
        history_text = "Recent conversation history:\n"
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Jeremy"
            history_text += f"{role}: {msg['content']}\n"
        history_text += "\n"
    system_prompt = """
You are Jeremy, the official AI assistant of RePut, a green-tech sustainability and ESG company.
Your goals:
- Answer ONLY using the information in the provided context.
- If the question is unrelated to RePut or ESG (e.g., general knowledge), politely explain that your expertise is limited to RePut's sustainability and ESG services. Then, immediately offer to help with RePut-related topics like supply chain traceability, ESG data, or climate impact.
- Do NOT mention "documents", "context", or "provided information" in your refusal.
- Keep responses clear, friendly, and concise.
- Emphasise RePut's strengths in ESG data, traceability, circularity, climate impact, and transparency.
"""
    user_prompt = f"""
{history_text}
User question: {question}
Relevant company context:
{context_text}
Answer as Jeremy, referring to "we" as RePut when appropriate.
INSTRUCTIONS FOR CONTACT FORM:
1. If the user asks a general question about services/products:
   - Answer the question helpfuly.
   - You MAY ask "Would you like to connect with our team to explore this further?" at the end.
   - Do NOT show the contact form yet.
2. If the user explicitly asks to "contact support", "talk to sales", "get a demo", or "connect":
   - Output the special token |||SHOW_CONTACT_FORM||| at the end of your response.
3. If the user says "Yes", "Sure", or agrees to your previous offer to connect (check the history):
   - Output the special token |||SHOW_CONTACT_FORM||| at the end of your response.
"""
    return system_prompt, user_prompt

def answer_question(question: str, history: list = [], top_k: int = 5):
    try:
        # 1) Get DB and LLM (Singletons)
        db = get_vector_db()
        llm = get_llm()

        # 2) Retrieve documents
        logger.info(f"Searching for: {question}")
        results = db.similarity_search_with_score(question, k=top_k)
        
        # results is a list of (Document, score) tuples. 
        # Note: Chroma scores are distance (lower is better), but LangChain might normalize depending on version.
        # Usually for cosine distance, lower is better. 
        
        top_docs = [doc for doc, score in results]
        
        # 3) Build context text
        context_text = ""
        for i, d in enumerate(top_docs, 1):
            context_text += (
                f"\n[Source {i} - {d.metadata.get('source_file', 'unknown')}]\n"
                f"{d.page_content}\n"
            )

        # 4) Call Gemini chat model
        system_prompt, user_prompt = build_prompt(question, context_text, history)
        
        # Append instruction for suggested questions
        user_prompt += "\n\nIMPORTANT: After your answer, please provide 3 short, relevant follow-up questions that the user might ask next based on the context. Format them as a JSON list at the very end of your response, strictly following this format:\n|||SUGGESTIONS||| [\"Question 1?\", \"Question 2?\", \"Question 3?\"]"

        response = llm.invoke(
            [
                ("system", system_prompt),
                ("user", user_prompt),
            ]
        )
        
        content = response.content
        suggested_questions = []
        if "|||SUGGESTIONS|||" in content:
            parts = content.split("|||SUGGESTIONS|||")
            answer_text = parts[0].strip()
            try:
                import json
                json_str = parts[1].strip()
                # clean up any markdown code blocks if present
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                suggested_questions = json.loads(json_str.strip())
            except Exception as e:
                logger.error(f"Error parsing suggestions: {e}")
                # Fallback if parsing fails
                suggested_questions = []
        else:
            answer_text = content

        return {
            "answer": answer_text,
            "sources": [
                {
                    "source": d.metadata.get("source_file", "unknown"),
                    "snippet": d.page_content[:300],
                }
                for d in top_docs
            ],
            "suggested_questions": suggested_questions
        }

    except Exception as e:
        logger.error(f"Error in answer_question: {e}", exc_info=True)
        if "429" in str(e) or "ResourceExhausted" in str(e):
             return {
                "answer": "I'm currently experiencing high traffic and my brain is a bit overloaded (API Quota Exceeded). Please try again in a minute.",
                "sources": [],
                "suggested_questions": []
            }
        raise e

if __name__ == "__main__":
    q = "What does RePut do and how do we help with sustainability?"
    result = answer_question(q)
    print("\n Answer:\n", result["answer"])
    print("\n Suggested Questions:\n", result.get("suggested_questions"))
    print("\n Sources:")
    for s in result["sources"]:
        print("-", s["source"])



