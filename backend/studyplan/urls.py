from django.urls import path
from .views import StudyPlanGenerateView, StudyKnowledgeUploadView

urlpatterns = [
    path('generate/', StudyPlanGenerateView.as_view(), name='studyplan_generate'),
    path('upload/', StudyKnowledgeUploadView.as_view(), name='studyplan_upload'),
]
