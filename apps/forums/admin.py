from django.contrib import admin
from forums.models import Forum
from forums.models import Topic

class ForumAdmin(admin.ModelAdmin):
    list_display = ('title', )

admin.site.register(Forum, ForumAdmin)


class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', )

admin.site.register(Topic, TopicAdmin)
