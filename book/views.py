# book/views.py
from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from .recommender import get_recommendations

import requests
from bs4 import BeautifulSoup
from html import unescape
import re

# 기존: 추천 도서 페이지 렌더링
class Book(APIView):
    def get(self, request):
        return render(request, 'book/recommend_book.html')

# 기존: 사용자 ID 기반 도서 추천
class RecommendBooks(APIView):
    def get(self, request):
        user_id = request.GET.get('user_id', '흙속에저바람속에')
        try:
            recommendations = get_recommendations(user_id=user_id, top_k=5)
            return JsonResponse({'results': recommendations})
        except Exception as e:
            import traceback
            print("[추천 오류]", traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

# ✅ 추가: 네이버 책 검색 API
def clean_text(text):
    text = re.sub('<.*?>', '', text)
    return unescape(text)

def search_book_single(request):
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({'items': []})

    headers = {
        "X-Naver-Client-Id": "VyGxEbFfN_rYgqrtWTby",
        "X-Naver-Client-Secret": "nDnh4BmwQk"
    }

    url = "https://openapi.naver.com/v1/search/book.xml"
    params = {
        "query": query,
        "display": 3
    }

    res = requests.get(url, headers=headers, params=params)
    items = []

    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'xml')
        for item in soup.find_all("item"):
            items.append({
                'title': clean_text(item.title.get_text()),
                'author': clean_text(item.author.get_text()),
                'description': clean_text(item.description.get_text()),
                'link': item.link.get_text()
            })

    return JsonResponse({'items': items}, json_dumps_params={'ensure_ascii': False})
