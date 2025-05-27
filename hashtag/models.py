from django.db import models
from content.models import Feed  # Post가 content.Feed면 맞게 수정

class Hashtag(models.Model):
    tag_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"#{self.tag_name}"

class PostHashtag(models.Model):
    post = models.ForeignKey(Feed, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'hashtag')

    def __str__(self):
        return f"{self.post.id} tagged with #{self.hashtag.tag_name}"
