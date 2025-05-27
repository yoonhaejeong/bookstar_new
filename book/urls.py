# book/urls.py
from django.urls import path
from .views import Book,RecommendBooks

urlpatterns = [
    path('', Book.as_view(), name='book_page'),
    path('recommend/', RecommendBooks.as_view(), name='recommend_books'),
]