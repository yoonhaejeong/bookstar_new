"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from config.views import feed_search
from .views import Main, UploadFeed
from content.views import ToggleLike, ToggleBookmark
from user.views import ToggleFollow
from content import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('',Main.as_view(),name='main'),
    path('content/upload',UploadFeed.as_view()),
    path('user/',include('user.urls')),
    path('book/',include('book.urls')),
    path('admin/', admin.site.urls),
    path('search/', feed_search, name='feed_search'),
    path('api/toggle-like/', ToggleLike.as_view(), name='toggle_like'),
    path('api/toggle-bookmark/', ToggleBookmark.as_view(), name='toggle_bookmark'),
    path('content/bookmark', ToggleBookmark.as_view(), name='toggle_bookmark'),
    path('api/toggle-follow/', ToggleFollow.as_view(), name='toggle-follow'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)