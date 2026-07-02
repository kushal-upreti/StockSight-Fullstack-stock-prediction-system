
from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    LogoutView, 
    UserProfileView,
    ProfilePictureUploadView,
    ForgotPasswordView,
    ResetPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/picture/', ProfilePictureUploadView.as_view(), name='profile-picture'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
