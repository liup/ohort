from django.conf.urls.defaults import *

from notification.views import settings, notices, mark_all_seen, feed_for_user, single

urlpatterns = patterns('',
    url(r'^$', notices, name="notification_notices"),
    url(r'^settings$', settings, name="notification_settings"),
    url(r'^(\d+)/$', single, name="notification_notice"),
    url(r'^feed/$', feed_for_user, name="notification_feed_for_user"),
    url(r'^mark_all_seen/$', mark_all_seen, name="notification_mark_all_seen"),
)
