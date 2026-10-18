from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserSignupView, CustomTokenObtainPairView

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='auth_signup'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),
]
