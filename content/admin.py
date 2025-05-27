from django.contrib import admin
from .models import Feed

class FeedAdmin(admin.ModelAdmin):
    search_fields = ['content']

admin.site.register(Feed,FeedAdmin)
