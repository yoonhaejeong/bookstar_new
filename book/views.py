# book/views.py
from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from .recommender import get_recommendations

class Book(APIView):
    def get(self, request):
        return render(request, 'book/recommend_book.html')

class RecommendBooks(APIView):
    def get(self, request):
        user_id = request.GET.get('user_id', '흙속에저바람속에')
        try:
            recommendations = get_recommendations(user_id=user_id, top_k=5)
            return JsonResponse({'results': recommendations})
        except Exception as e:
            import traceback
            print("[추천 오류]",traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)