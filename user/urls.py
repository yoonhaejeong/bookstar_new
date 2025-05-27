from django.urls import path
from .views import Login, Join, Logout, profile_view, UpdateProfileImage

urlpatterns = [
    path('login/', Login.as_view(), name='login'),
    path('join/', Join.as_view(), name='join'),
    path('logout/', Logout.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('update-profile-image/', UpdateProfileImage.as_view(), name='update-profile'),
]