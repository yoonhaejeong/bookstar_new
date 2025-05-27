from django.db import models
from user.models import User
from content.models import Feed  # Post가 content.Feed면 맞게 수정

class Notification(models.Model):
    NOTI_TYPE_CHOICES = [
        ('LIKE', 'Like'),
        ('FOLLOW', 'Follow'),
        ('COMMENT', 'Comment'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # 알림 받는 사람
    type = models.CharField(max_length=10, choices=NOTI_TYPE_CHOICES)
    ref_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='triggered_notifications')  # 알림 유발자
    post = models.ForeignKey(Feed, null=True, blank=True, on_delete=models.SET_NULL)  # 관련 게시물
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification to {self.user.email} of type {self.type}"
