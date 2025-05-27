from django.shortcuts import render
from rest_framework.views import APIView
from content.models import Feed, Bookmark, Like
from user.models import Follow
from rest_framework.response import Response
import os
from .settings import MEDIA_ROOT
from uuid import uuid4
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from user.models import User

class Main(APIView):
    def get(self,request):
        feed_list=Feed.objects.all().order_by('-id')
        email = request.session.get('email')
        user=User.objects.filter(email=email).first() if email else None

        for feed in feed_list:
            if email:
                feed.is_marked = Bookmark.objects.filter(feed_id=feed.id, email=email, is_marked=True).exists()
                feed.is_liked = Like.objects.filter(feed_id=feed.id, email=email, is_like=True).exists()
            else:
                feed.is_marked = False
                feed.is_liked = False

        raw_users=[]
        following_ids=[]
        if user:
            raw_users = User.objects.exclude(id=user.id)[:5]
            following_ids = Follow.objects.filter(from_user=user).values_list('to_user_id', flat=True)

        mike = raw_users[0] if len(raw_users) > 0 else None
        sulley = raw_users[1] if len(raw_users) > 1 else None
        rose = raw_users[2] if len(raw_users) > 2 else None
        monsterinc = raw_users[3] if len(raw_users) > 3 else None
        monsteruni = raw_users[4] if len(raw_users) > 4 else None

        # 팔로우 여부 추가
        for u in [mike, sulley, rose, monsterinc, monsteruni]:
            if u:  # None 방지
                u.is_following = u.id in following_ids
        recommended_users = [mike, sulley, rose, monsterinc, monsteruni]

        bookmarked_feeds=[]
        if email:
            bookmark_feed_ids = Bookmark.objects.filter(email=email, is_marked=True).values_list('feed_id', flat=True)
            bookmarked_feeds = Feed.objects.filter(id__in=bookmark_feed_ids).order_by('-id')
        return render(request,'bookstar/main.html',
            context={
                'feed_list':feed_list,
                'bookmarked_feeds':bookmarked_feeds,
                'recommend_users':recommended_users,
                'mike':mike,
                'sulley':sulley,
                'rose':rose,
                'monsterinc':monsterinc,
                'monsteruni':monsteruni,
                'user':user,
            })

@method_decorator(csrf_exempt, name='dispatch')
class UploadFeed(APIView):
    def post(self, request):
        file = request.FILES['file']
        uuid_name = uuid4().hex
        save_path = os.path.join(MEDIA_ROOT, uuid_name)

        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        content = request.data.get('content')
        image = uuid_name

        email = request.session.get('email')
        if not email:
            return Response(status=400, data={'message': '로그인이 필요합니다.'})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(status=400, data={'message': '존재하지 않는 사용자입니다.'})

        Feed.objects.create(
            content=content,
            image=image,
            user=user,
            like_count=0
        )
        return Response(status=200)

def feed_search(request):
    query = request.GET.get('q', '')
    feeds = Feed.objects.filter(
        Q(content__icontains=query) | Q(user_id__icontains=query)
    ) if query else []

    return render(request, 'bookstar/search_result.html', {
        'query': query,
        'feeds': feeds
    })
