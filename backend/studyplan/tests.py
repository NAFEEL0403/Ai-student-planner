from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from studyplan.models import StudyKnowledge, StudyPlan

class StudyPlanTests(APITestCase):
    def setUp(self):
        self.generate_url = reverse('studyplan_generate')
        self.user = User.objects.create_user(
            username='student@example.com',
            email='student@example.com',
            password='password123',
            first_name='Alice'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create some knowledge blocks with dummy 384-dimension embeddings
        dummy_embedding = [0.0] * 384
        self.knowledge1 = StudyKnowledge.objects.create(
            title='Test Title 1',
            subject='DBMS',
            content='This is some database knowledge content.',
            embedding=dummy_embedding
        )
        self.knowledge2 = StudyKnowledge.objects.create(
            title='Test Title 2',
            subject='Python',
            content='This is some Python knowledge content.',
            embedding=dummy_embedding
        )

        self.payload = {
            'name': 'Alice',
            'subjects': ['DBMS', 'Python'],
            'topics': ['SQL Joins', 'OOP Concepts'],
            'exam_date': '2026-09-30',
            'daily_hours': 4,
            'knowledge_level': 'Beginner',
            'preferred_session': 'Morning',
            'duration_days': 7
        }

    @patch('studyplan.services.EmbeddingService.generate_embedding')
    @patch('studyplan.services.GroqService.generate_plan')
    def test_generate_study_plan_success(self, mock_generate_plan, mock_generate_embedding):
        # Mock embeddings to return a dummy vector of 384 dimensions
        mock_generate_embedding.return_value = [0.1] * 384
        # Mock groq generator response
        mock_generate_plan.return_value = "## Day 1\n- Study SQL Joins\n## Day 2\n- Study OOP Concepts"

        response = self.client.post(self.generate_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('generated_plan', response.data)
        self.assertEqual(response.data['generated_plan'], "## Day 1\n- Study SQL Joins\n## Day 2\n- Study OOP Concepts")
        
        # Verify it was saved to db
        self.assertTrue(StudyPlan.objects.filter(user=self.user).exists())
        plan = StudyPlan.objects.get(user=self.user)
        self.assertEqual(plan.generated_plan, "## Day 1\n- Study SQL Joins\n## Day 2\n- Study OOP Concepts")
        self.assertEqual(plan.input_data['name'], 'Alice')

    def test_generate_study_plan_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.generate_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_study_plan_invalid_payload(self):
        bad_payload = self.payload.copy()
        bad_payload['daily_hours'] = 25  # Max is 24
        response = self.client.post(self.generate_url, bad_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('daily_hours', response.data)

    @patch('studyplan.services.EmbeddingService.generate_embedding')
    def test_upload_document_success(self, mock_generate_embedding):
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_generate_embedding.return_value = [0.2] * 384
        
        p1 = b"A" * 850
        p2 = b"B" * 850
        file_content = p1 + b"\n\n" + p2
        uploaded_file = SimpleUploadedFile("syllabus.txt", file_content, content_type="text/plain")
        
        upload_url = reverse('studyplan_upload')
        response = self.client.post(upload_url, {'file': uploaded_file, 'subject': 'DBMS'}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['chunks_count'], 2)
        
        # Verify chunks created in DB
        self.assertTrue(StudyKnowledge.objects.filter(subject='DBMS', title__contains='syllabus.txt').exists())
        self.assertEqual(StudyKnowledge.objects.filter(subject='DBMS').count(), 3) # 2 uploaded + 1 setup

    def test_upload_document_unauthenticated(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_authenticate(user=None)
        
        uploaded_file = SimpleUploadedFile("syllabus.txt", b"Content", content_type="text/plain")
        upload_url = reverse('studyplan_upload')
        response = self.client.post(upload_url, {'file': uploaded_file, 'subject': 'DBMS'}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_document_invalid_extension(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        uploaded_file = SimpleUploadedFile("syllabus.exe", b"Content", content_type="application/octet-stream")
        upload_url = reverse('studyplan_upload')
        response = self.client.post(upload_url, {'file': uploaded_file, 'subject': 'DBMS'}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('studyplan.views.pypdf.PdfReader')
    @patch('studyplan.services.EmbeddingService.generate_embedding')
    def test_upload_pdf_success(self, mock_generate_embedding, mock_pdf_reader):
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_generate_embedding.return_value = [0.2] * 384
        
        # Mock the PdfReader and its page elements
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 850
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page, mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        uploaded_file = SimpleUploadedFile("syllabus.pdf", b"Dummy PDF bytes", content_type="application/pdf")
        upload_url = reverse('studyplan_upload')
        response = self.client.post(upload_url, {'file': uploaded_file, 'subject': 'DSA'}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['chunks_count'], 2)
        
        # Verify it saved chunks
        self.assertTrue(StudyKnowledge.objects.filter(subject='DSA', title__contains='syllabus.pdf').exists())



