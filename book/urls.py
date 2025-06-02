from django.urls import path
from .views import Book, RecommendBooks, search_book_single  # ✅ 추가

urlpatterns = [
    path('', Book.as_view(), name='book_page'),
    path('recommend/', RecommendBooks.as_view(), name='recommend_books'),
    path('search/naver_xml/', search_book_single, name='search_book_single'),  # ✅ 추가
]