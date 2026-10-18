from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from pgvector.django import CosineDistance
import pypdf

from .serializers import StudyPlanRequestSerializer
from .services import EmbeddingService, GroqService
from .models import StudyPlan, StudyKnowledge

class StudyPlanGenerateView(APIView):
    # Ensure only authenticated users can access this endpoint
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Validate the request data
        serializer = StudyPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        subjects = validated_data['subjects']
        topics = validated_data['topics']

        # 1. Formulate search query using student's input subjects & topics
        query_text = f"Subjects: {', '.join(subjects)}. Topics: {', '.join(topics)}."

        # 2. Generate embedding for query text using local sentence transformer
        try:
            query_vector = EmbeddingService.generate_embedding(query_text)
        except Exception as e:
            return Response(
                {"error": f"Failed to generate text embeddings: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. Retrieve top 4 matching study knowledge chunks from PostgreSQL + pgvector
        try:
            # Annotation with CosineDistance: smaller distance means higher similarity
            retrieved_chunks = StudyKnowledge.objects.annotate(
                distance=CosineDistance('embedding', query_vector)
            ).order_by('distance')[:4]
            # Convert to list to force query evaluation and catch database errors here
            retrieved_chunks_list = list(retrieved_chunks)
        except Exception as e:
            return Response(
                {"error": f"PostgreSQL pgvector search failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. Generate plan using Groq SDK
        try:
            generated_plan = GroqService.generate_plan(validated_data, retrieved_chunks_list)
        except Exception as e:
            return Response(
                {"error": f"Unable to generate the study plan. Please check your Groq API key: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # 5. Save the generated plan to the database
        try:
            study_plan_obj = StudyPlan.objects.create(
                user=request.user,
                input_data=serializer.data,
                generated_plan=generated_plan
            )
            created_at = study_plan_obj.created_at
        except Exception:
            created_at = None

        return Response({
            "generated_plan": generated_plan,
            "created_at": created_at
        }, status=status.HTTP_200_OK)


class StudyKnowledgeUploadView(APIView):
    # Ensure only authenticated users can upload documents
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('file')
        subject = request.data.get('subject', 'Uploaded Document').strip()

        if not file_obj:
            return Response({"error": "No file was uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        # Allow common text-based file extensions and PDF
        filename_lower = file_obj.name.lower()
        if not filename_lower.endswith(('.txt', '.md', '.csv', '.json', '.pdf')):
            return Response({"error": "Only text-based files (.txt, .md, .csv, .json) or PDF (.pdf) files are supported."}, status=status.HTTP_400_BAD_REQUEST)

        content_text = ""
        try:
            if filename_lower.endswith('.pdf'):
                # Extract text page by page using pypdf
                reader = pypdf.PdfReader(file_obj)
                pages_text = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text.strip())
                content_text = "\n\n".join(pages_text)
            else:
                # Read text content and decode as utf-8
                content_bytes = file_obj.read()
                content_text = content_bytes.decode('utf-8')
        except Exception as e:
            return Response({"error": f"Failed to parse document content: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Split content into paragraphs/sections
        paragraphs = [p.strip() for p in content_text.split('\n\n') if p.strip()]
        if len(paragraphs) <= 1:
            paragraphs = [p.strip() for p in content_text.split('\n') if p.strip()]

        # Combine short paragraphs into cohesive RAG chunks (approx 100-800 characters)
        chunks = []
        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) < 800:
                current_chunk += "\n" + p if current_chunk else p
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = p
        if current_chunk:
            chunks.append(current_chunk)

        if not chunks:
            return Response({"error": "The uploaded file is empty."}, status=status.HTTP_400_BAD_REQUEST)

        saved_count = 0
        try:
            for i, chunk in enumerate(chunks):
                # Generate local vector embedding
                embedding = EmbeddingService.generate_embedding(chunk)
                # Save chunk to Database
                StudyKnowledge.objects.create(
                    title=f"{file_obj.name} (Part {i+1})",
                    subject=subject,
                    content=chunk,
                    embedding=embedding
                )
                saved_count += 1
        except Exception as e:
            return Response(
                {"error": f"Failed to generate embeddings: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "message": f"Successfully processed and indexed {saved_count} text chunks from '{file_obj.name}'.",
            "chunks_count": saved_count
        }, status=status.HTTP_201_CREATED)

