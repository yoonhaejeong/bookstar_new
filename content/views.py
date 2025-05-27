from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Feed, Like, Bookmark  # 또는 Post, Content 등 실제 모델명
from user.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

class Main(APIView):
    def get(self, request):
        email = request.session.get('email')
        feed_list = Feed.objects.all().order_by('-id')
        user = User.objects.filter(email=email).first() if email else None

        #추천 사용자
        #recommended_users=[]
        #if user:
        #    recommended_users=User.objects.exclude(id=user.id)[:5]

        for feed in feed_list:
            if email:
                is_marked = Bookmark.objects.filter(feed_id=feed.id, email=email, is_marked=True).exists()
                feed.is_marked = is_marked
            else:
                feed.is_marked = False

        return render(request, 'bookstar/main.html', {
            'feed_list': feed_list,
            #'recommended_users': recommended_users,
            #'user': user,
        })

class ToggleLike(APIView):
    def post(self, request):
        feed_id = request.data.get('feed_id')
        favorite_text = request.data.get('favorite_text')
        email = request.session.get('email')

        if not (feed_id and email):
            return Response({'error': 'Invalid data'}, status=400)

        is_like = (favorite_text == 'favorite_border')

        like = Like.objects.filter(feed_id=feed_id, email=email).first()

        if like:
            like.is_like = is_like
            like.save()
        else:
            Like.objects.create(feed_id=feed_id, is_like=is_like, email=email)

        # 좋아요 수 갱신
        like_count = Like.objects.filter(feed_id=feed_id, is_like=True).count()
        Feed.objects.filter(id=feed_id).update(like_count=like_count)

        return Response({'like_count': like_count}, status=200)

class ToggleBookmark(APIView):
    def post(self, request):
        feed_id = request.data.get('feed_id')
        email = request.session.get('email')

        if not (feed_id and email):
            return Response({'error': 'Invalid data'}, status=400)

        # 북마크가 이미 존재하는지 확인
        bookmark = Bookmark.objects.filter(feed_id=feed_id, email=email).first()

        if bookmark:
            # is_marked 값을 반대로 토글
            bookmark.is_marked = not bookmark.is_marked
            bookmark.save()
        else:
            # 없으면 새로 생성 (북마크 ON 상태로)
            Bookmark.objects.create(feed_id=feed_id, email=email, is_marked=True)

        return Response({'message': 'Bookmark toggled successfully'}, status=200)


