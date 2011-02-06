from django.conf.urls.defaults import *
from django.conf import settings

try:
    FORUMS_URL_RE = settings.FORUMS_URL_RE
except AttributeError:
    FORUMS_URL_RE = r'\w+'

try:
    TOPICS_URL_RE = settings.TOPICS_URL_RE
except AttributeError:
    TOPICS_URL_RE = r'\w+'

urlpatterns = patterns('',
    url(r'^$', 'forums.views.forums', name="forum_list"),
    url(r'^(?P<forum_id>\d+)/edit/$', 'forums.views.forum', kwargs={"edit": True}, name="forum_edit"),
    url(r'^(?P<forum_id>\d+)/delete/$', 'forums.views.forum_delete', name="forum_delete"),
    url(r'^(?P<forum_id>\d+)/$', 'forums.views.forum', name="forum_detail"),

    url(r'^topics/$', 'forums.views.topics', name="topic_list"),
    url(r'^topics/(?P<topic_id>\d+)/edit/$', 'forums.views.topic', kwargs={"edit": True}, name="topic_edit"),
    url(r'^topics/(?P<topic_id>\d+)/delete/$', 'forums.views.topic_delete', name="topic_delete"),
    url(r'^topics/(?P<topic_id>\d+)/$', 'forums.views.topic', name="topic_detail"),

    url(r'observe/(?P<forum_id>'+ FORUMS_URL_RE +r')/$', 'forums.views.observe_forum',
        name='forums_observe'),

    url(r'observe/(?P<forum_id>'+ FORUMS_URL_RE +r')/stop/$', 'forums.views.stop_observing_forum',
        name='forums_stop_observing'),

    url(r'^(?P<forum_id>\d+)/$', 'forums.views.forum', name="forums_forum"),

    url(r'topics/observe/(?P<topic_id>'+ FORUMS_URL_RE +r')/$', 'forums.views.observe_topic',
        name='topics_observe'),

    url(r'topics/observe/(?P<topic_id>'+ FORUMS_URL_RE +r')/stop/$', 'forums.views.stop_observing_topic',
        name='topics_stop_observing'),

    url(r'^topics/(?P<topic_id>\d+)/$', 'forums.views.topic', name="forums_topic"),
)

