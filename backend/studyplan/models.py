from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField

class StudyKnowledge(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100)
    content = models.TextField()
    # all-MiniLM-L6-v2 produces 384 dimensions
    embedding = VectorField(dimensions=384)

    def __str__(self):
        return f"{self.subject} - {self.title}"


class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    input_data = models.JSONField()
    generated_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Plan for {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"
