import os
from django.conf import settings
from sentence_transformers import SentenceTransformer
from groq import Groq

class EmbeddingService:
    _model = None

    @classmethod
    def get_model(cls):
        """
        Lazy load the SentenceTransformer model to prevent loading it
        unnecessarily during startup or django migrations/management runs.
        """
        if cls._model is None:
            # We use all-MiniLM-L6-v2 which yields a 384-dimension vector
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> list:
        """
        Generates a 384-dimensional vector embedding for the input text.
        """
        model = cls.get_model()
        embedding = model.encode(text)
        return embedding.tolist()


class GroqService:
    @classmethod
    def generate_plan(cls, student_data: dict, context_chunks) -> str:
        """
        Combines retrieved RAG context and student preferences to prompt
        Groq API for generating a personalized day-by-day study plan.
        """
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "gsk_your_actual_key_here":
            raise ValueError("A valid GROQ_API_KEY must be provided in the backend .env file.")

        # Initialize the official Groq client
        client = Groq(api_key=settings.GROQ_API_KEY)

        # Format the retrieved RAG context
        formatted_context = ""
        for i, chunk in enumerate(context_chunks):
            formatted_context += f"\n--- Topic Info {i+1}: {chunk.subject} ({chunk.title}) ---\n{chunk.content}\n"

        # Format user subjects and topics
        subjects_str = ", ".join(student_data.get("subjects", []))
        topics_str = ", ".join(student_data.get("topics", []))

        # Build prompt
        user_prompt = f"""
You are a student study planning assistant.

Create a realistic study plan based on the student's information.

Student Name: {student_data.get('name', 'Student')}
Subjects: {subjects_str}
Topics: {topics_str}
Available hours per day: {student_data.get('daily_hours')} hours
Knowledge level: {student_data.get('knowledge_level')}
Exam date: {student_data.get('exam_date')}
Study duration: {student_data.get('duration_days')} days
Preferred study session: {student_data.get('preferred_session')}

Relevant study knowledge (RAG context):
{formatted_context}

Create a practical day-by-day study plan for the given {student_data.get('duration_days')} days.

For each day include:
- Day index (e.g. Day 1, Day 2)
- Focus Topic name
- Study duration (split between new concepts and revision, matching daily hours)
- Bulleted list of what to learn
- Specific practice or revision tasks

Constraints:
- Use the available daily study time ({student_data.get('daily_hours')} hours) realistically.
- Do not overload the student.
- Format the output clearly in markdown.
"""

        # Call Groq API using llama-3.3-70b-versatile
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional student study planning assistant. You create clean, structured day-by-day study schedules in markdown format."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )

        return response.choices[0].message.content
