import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        self._initialize_llm()
    
    def _initialize_llm(self):
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.gemini_api_key,
                temperature=0,
                convert_system_message_to_human=True
            )
            logger.info("Gemini LLM initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini LLM: {e}")
            raise
    
    def generate_response(self, query, context_docs):
        try:
            if not context_docs:
                return {
                    "text": "I couldn't find any relevant information in your documents to answer this question.",
                    "sources": []
                }
            
            # Create context from retrieved documents
            context = "\n\n---\n\n".join([doc["content"] for doc in context_docs])
            
            # Create source references
            sources = []
            for doc in context_docs:
                meta = doc["metadata"]
                sources.append({
                    "fileId": meta.get("file_id", ""),
                    "title": meta.get("filename", "Unknown Document"),
                    "page": meta.get("page")
                })
            
            # Create prompt with context and the query, the context consists of the documents retrieved from the vector store, the query is the question asked by the user
            system_prompt = """You are an AI assistant that answers questions based on provided documents.
            Use ONLY the information in the context provided to answer the question.
            If the context doesn't contain the information needed, say you don't know or cannot find it in the documents.
            Provide a clear, concise answer that directly addresses the question.
            Do not make up information or draw from knowledge outside the provided context."""
            
            user_prompt = f"""Context:
            {context}
            
            Question: {query}
            
            Please provide an answer based only on the context above."""
            
            # In langchain we can provide separate messages for the system and user prompts
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Generate response using the LLM using the invoke method of the ChatGoogleGenerativeAI library
            response = self.llm.invoke(messages)
            
            return {
                "text": response.content,
                "sources": sources
            }
        
        except Exception as e:
            logger.error(f"Error generating response from Gemini LLM: {e}")
            return {
                "text": "Sorry, I encountered an error while processing your question.",
                "sources": []
            }