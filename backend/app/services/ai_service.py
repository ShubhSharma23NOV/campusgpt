"""
CampusGPT – RAG AI Service
Handles: PDF ingestion, vector storage, semantic search, and Gemini-powered responses.
"""

import os
import re
import time
import logging
from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are CampusGPT, an AI assistant for college students. 
You answer questions ONLY based on the official college policy documents provided as context.

CRITICAL RULES:
1. Only answer from the provided context documents
2. If the answer is NOT in the context, respond EXACTLY: "This information is not available in the uploaded policy documents."
3. Always cite the source document name when answering
4. Be concise, clear, and student-friendly
5. Support Hindi, Hinglish, and English - respond in the same language as the question
6. Do NOT make up, infer, or hallucinate information

Context from policy documents:
{context}

Remember: If unsure or not found in documents, say the exact fallback phrase."""

STUDENT_CONTEXT_PROMPT = """You are CampusGPT, a personalized AI assistant for a college student.
You have access to:
1. The student's personal academic data (attendance, fees, hostel, scholarships, fines)
2. Official college policy documents

Student Data:
{student_data}

Policy Context:
{context}

RULES:
1. Combine student data + policy documents to give personalized answers
2. Be accurate with numbers (fees, percentages, dates)
3. Give actionable advice when possible
4. If data is unavailable, clearly state that
5. Respond in the same language as the question (Hindi/Hinglish/English)
6. Never guess or hallucinate"""


class RAGService:
    """Handles document ingestion and retrieval for the campus policy chatbot."""

    def __init__(self):
        self._chroma_client = None
        self._collection = None
        self._embeddings = None
        self._llm = None
        self._initialized = False

    def _get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=settings.GEMINI_API_KEY,
            )
        return self._embeddings

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1,
                max_output_tokens=2048,
            )
        return self._llm

    def _get_chroma_collection(self):
        if self._collection is None:
            client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_PATH,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    # ─────────────────────────────────────────────
    # Document Ingestion
    # ─────────────────────────────────────────────

    async def ingest_pdf(self, file_path: str, policy_id: int, title: str, category: str) -> dict:
        """Parse a PDF, chunk it, embed, and store in ChromaDB."""
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=150,
                separators=["\n\n", "\n", ".", "!", "?", " "],
            )
            chunks = splitter.split_documents(pages)

            if not chunks:
                return {"success": False, "error": "No text extracted from PDF"}

            collection = self._get_chroma_collection()
            embeddings_model = self._get_embeddings()

            texts = [c.page_content for c in chunks]
            metadatas = [
                {
                    "policy_id": str(policy_id),
                    "title": title,
                    "category": category,
                    "page": str(c.metadata.get("page", 0)),
                    "source": os.path.basename(file_path),
                }
                for c in chunks
            ]
            ids = [f"policy_{policy_id}_chunk_{i}" for i in range(len(chunks))]

            # Remove existing chunks for this policy (re-upload)
            try:
                existing = collection.get(where={"policy_id": str(policy_id)})
                if existing["ids"]:
                    collection.delete(ids=existing["ids"])
            except Exception:
                pass

            # Batch embed and store
            embeddings = embeddings_model.embed_documents(texts)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            logger.info(f"Ingested {len(chunks)} chunks for policy '{title}'")
            return {"success": True, "chunks": len(chunks), "policy_id": policy_id}

        except Exception as e:
            logger.error(f"PDF ingestion error: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────
    # Semantic Search
    # ─────────────────────────────────────────────

    def _search_docs(self, query: str, n_results: int = 5, category_filter: Optional[str] = None) -> list[dict]:
        """Perform semantic search in ChromaDB."""
        collection = self._get_chroma_collection()
        embeddings_model = self._get_embeddings()

        query_embedding = embeddings_model.embed_query(query)

        where = None
        if category_filter:
            where = {"category": category_filter}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
            where=where,
        )

        docs = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                docs.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity": 1 - dist,  # cosine distance → similarity
                })

        # Filter low-relevance results
        return [d for d in docs if d["similarity"] > 0.3]

    # ─────────────────────────────────────────────
    # Chat – Policy-only mode
    # ─────────────────────────────────────────────

    async def chat_policy(self, question: str, session_history: list[dict] = None) -> dict:
        """Answer questions using only policy documents (RAG)."""
        start_time = time.time()

        try:
            docs = self._search_docs(question, n_results=5)

            if not docs:
                return {
                    "answer": "This information is not available in the uploaded policy documents.",
                    "sources": [],
                    "was_answered": False,
                    "response_time": time.time() - start_time,
                }

            # Build context string
            context = "\n\n---\n\n".join([
                f"[Source: {d['metadata'].get('title', 'Policy Document')} | Page {d['metadata'].get('page', '?')}]\n{d['content']}"
                for d in docs
            ])

            # Build sources list (deduplicated)
            seen = set()
            sources = []
            for d in docs:
                key = d["metadata"].get("title", "")
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "title": d["metadata"].get("title", "Policy Document"),
                        "category": d["metadata"].get("category", "general"),
                        "page": d["metadata"].get("page", "?"),
                        "source_file": d["metadata"].get("source", ""),
                    })

            llm = self._get_llm()

            # Include chat history for context
            history_text = ""
            if session_history:
                last_3 = session_history[-6:]  # last 3 exchanges
                history_text = "\nPrevious conversation:\n" + "\n".join(
                    [f"{m['role'].upper()}: {m['content']}" for m in last_3]
                )

            prompt_text = f"""{SYSTEM_PROMPT}
{history_text}

Student Question: {question}

Provide a clear, accurate answer based only on the policy documents above."""

            response = await llm.ainvoke(prompt_text.replace("{context}", context))
            answer = response.content if hasattr(response, "content") else str(response)

            return {
                "answer": answer,
                "sources": sources,
                "was_answered": True,
                "response_time": time.time() - start_time,
            }

        except Exception as e:
            logger.error(f"Policy chat error: {e}")
            return {
                "answer": "I encountered an error processing your question. Please try again.",
                "sources": [],
                "was_answered": False,
                "response_time": time.time() - start_time,
                "error": str(e),
            }

    # ─────────────────────────────────────────────
    # Chat – Personalized Student mode
    # ─────────────────────────────────────────────

    async def chat_personalized(
        self,
        question: str,
        student_data: dict,
        session_history: list[dict] = None,
    ) -> dict:
        """Answer using student's personal data + policy documents."""
        start_time = time.time()

        try:
            # Get relevant policy docs
            docs = self._search_docs(question, n_results=4)
            context = "\n\n---\n\n".join([d["content"] for d in docs]) if docs else "No relevant policy found."

            # Format student data as readable text
            student_summary = self._format_student_data(student_data)

            # Build sources
            seen = set()
            sources = []
            for d in docs:
                key = d["metadata"].get("title", "")
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "title": d["metadata"].get("title", "Policy Document"),
                        "category": d["metadata"].get("category", "general"),
                    })

            llm = self._get_llm()

            history_text = ""
            if session_history:
                last_4 = session_history[-8:]
                history_text = "\nConversation history:\n" + "\n".join(
                    [f"{m['role'].upper()}: {m['content']}" for m in last_4]
                )

            prompt_text = STUDENT_CONTEXT_PROMPT.replace("{student_data}", student_summary)
            prompt_text = prompt_text.replace("{context}", context)
            prompt_text += f"\n{history_text}\n\nStudent Question: {question}\n\nAnswer:"

            response = await llm.ainvoke(prompt_text)
            answer = response.content if hasattr(response, "content") else str(response)

            return {
                "answer": answer,
                "sources": sources,
                "was_answered": True,
                "response_time": time.time() - start_time,
            }

        except Exception as e:
            logger.error(f"Personalized chat error: {e}")
            return {
                "answer": "I encountered an error. Please try again.",
                "sources": [],
                "was_answered": False,
                "response_time": time.time() - start_time,
            }

    def _format_student_data(self, data: dict) -> str:
        """Convert student data dict to readable text for AI context."""
        lines = []
        if "student" in data:
            s = data["student"]
            lines.append(f"Student: {s.get('name')} | ID: {s.get('student_id')} | {s.get('course')} Sem {s.get('semester')}")

        if "attendance" in data:
            lines.append("\nATTENDANCE:")
            for sub in data["attendance"]:
                pct = sub.get("percentage", 0)
                lines.append(f"  - {sub.get('subject_name')}: {sub.get('attended')}/{sub.get('total')} = {pct:.1f}%")

        if "fees" in data:
            lines.append("\nFEES:")
            for fee in data["fees"]:
                lines.append(f"  - {fee.get('fee_type').title()}: Paid ₹{fee.get('paid_amount')} / Total ₹{fee.get('total_amount')} | Due: {fee.get('due_date')} | Status: {fee.get('status')}")

        if "hostel" in data:
            h = data["hostel"]
            if h:
                lines.append(f"\nHOSTEL: {h.get('hostel_name')} Room {h.get('room_number')} | Remaining Fee: ₹{h.get('remaining_fee')} | Next Due: {h.get('next_due_date')}")

        if "scholarships" in data:
            lines.append("\nSCHOLARSHIPS:")
            for sch in data["scholarships"]:
                lines.append(f"  - {sch.get('name')}: Status: {sch.get('status')}")

        if "fines" in data:
            unpaid = [f for f in data["fines"] if f.get("status") != "paid"]
            if unpaid:
                lines.append("\nPENDING FINES:")
                for fine in unpaid:
                    lines.append(f"  - {fine.get('reason')}: ₹{fine.get('remaining_amount')} | Due: {fine.get('due_date')}")

        return "\n".join(lines)

    # ─────────────────────────────────────────────
    # Document Summarization
    # ─────────────────────────────────────────────

    async def summarize_policy(self, policy_id: int, title: str) -> str:
        """Generate a summary of a policy document."""
        try:
            collection = self._get_chroma_collection()
            results = collection.get(
                where={"policy_id": str(policy_id)},
                include=["documents"],
            )

            if not results["documents"]:
                return "Document content not found."

            # Take first ~3000 chars for summary
            text = " ".join(results["documents"])[:3000]
            llm = self._get_llm()

            prompt = f"""Summarize the following college policy document in 3-5 clear bullet points.
Be concise and focus on key rules, requirements, and important dates.

Document: {title}
Content: {text}

Summary:"""

            response = await llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Unable to generate summary."

    # ─────────────────────────────────────────────
    # Attendance AI Suggestion
    # ─────────────────────────────────────────────

    async def get_attendance_advice(self, attendance_data: list[dict]) -> str:
        """Generate personalized attendance advice."""
        try:
            llm = self._get_llm()

            subjects_text = "\n".join([
                f"- {s['subject_name']}: {s['attended']}/{s['total']} = {s['percentage']:.1f}%"
                for s in attendance_data
            ])

            prompt = f"""As a student advisor, analyze this attendance data and give short, actionable advice:

{subjects_text}

Minimum required attendance: 75%

Provide:
1. Overall status (good/warning/critical)
2. Which subjects need immediate attention
3. How many classes needed to reach 75% for each at-risk subject
4. Motivational message

Keep it concise (under 100 words). Be friendly and direct."""

            response = await llm.ainvoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Attendance advice error: {e}")
            return "Unable to generate attendance advice."


# Singleton instance
rag_service = RAGService()
