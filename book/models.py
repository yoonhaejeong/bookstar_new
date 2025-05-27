from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255 ,blank=True)
    publish_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    rating = models.FloatField(default=0)
    review_count = models.IntegerField(default=0)
    genre = models.CharField(max_length=100, blank=True)
    link = models.TextField(blank=True)

    def __str__(self):
        return self.title
