from datetime import datetime

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User

from tagging.fields import TagField

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from threadedcomments.models import ThreadedComment
from django.db.models.query import QuerySet


# Avoid boilerplate defining our own querysets
class QuerySetManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)

class NonRemovedTopicManager(QuerySetManager):
    def get_query_set(self):
        q = super(NonRemovedTopicManager, self).get_query_set()
        return q.filter(removed=False)

class NonRemovedForumManager(QuerySetManager):
    def get_query_set(self):
        q = super(NonRemovedForumManager, self).get_query_set()
        return q.filter(removed=False)


class Forum(models.Model):
    """
    a forum for the tribe.
    """
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey("content_type", "object_id")
    
    title = models.CharField(_('title'), max_length=50)
    creator = models.ForeignKey(User, related_name="created_forums", verbose_name=_('creator'))
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now) # forum modified when commented on
    body = models.TextField(_('body'), blank=True)
    
    tags = TagField()
    
    removed = models.BooleanField(_("Is removed?"), default=False)
    objects = QuerySetManager()
    non_removed_objects = NonRemovedForumManager()
    class QuerySet(QuerySet):

        def get_by(self, title, group=None):
            if group is None:
                return self.get(object_id=None, title=title)
            return group.content_objects(self.filter(title=title)).get()
            
    def remove(self):
        """ Mark the Article as 'removed'. If the article is
        already removed, delete it.
        Returns True if the article was deleted, False when just marked
        as removed.
        """
        if self.removed:
            self.delete()
            return True
        else:
            self.removed = True
            self.save()
            return False

    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self, group=None):
        kwargs = {"forum_id": self.pk}
        if group:
            return group.content_bridge.reverse("forum_detail", group, kwargs=kwargs)
        else:
            return reverse("forum_detail", kwargs=kwargs)
    
    class Meta:
        ordering = ('-modified', )


class Topic(models.Model):
    """
    a discussion topic for the tribe.
    """
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey("content_type", "object_id")
    
    forum = models.ForeignKey(Forum)
    title = models.CharField(_('title'), max_length=50)
    creator = models.ForeignKey(User, related_name="created_topics", verbose_name=_('creator'))
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now) # topic modified when commented on
    body = models.TextField(_('body'), blank=True)
    
    tags = TagField()
    
    removed = models.BooleanField(_("Is removed?"), default=False)
    objects = QuerySetManager()
    non_removed_objects = NonRemovedTopicManager()
    class QuerySet(QuerySet):

        def get_by(self, title, group=None):
            if group is None:
                return self.get(object_id=None, title=title)
            return group.content_objects(self.filter(title=title)).get()
            
    def remove(self):
        """ Mark the Article as 'removed'. If the article is
        already removed, delete it.
        Returns True if the article was deleted, False when just marked
        as removed.
        """
        if self.removed:
            self.delete()
            return True
        else:
            self.removed = True
            self.save()
            return False


    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self, group=None):
        kwargs = {"topic_id": self.pk}
        if group:
            return group.content_bridge.reverse("topic_detail", group, kwargs=kwargs)
        else:
            return reverse("topic_detail", kwargs=kwargs)
    
    class Meta:
        ordering = ('-modified', )


def new_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Topic):
        topic = instance.content_object
        topic.modified = datetime.now()
        topic.save()
        if notification:
            # @@@ how do I know which notification type to send?
            # @@@ notification.send([topic.creator], "tribes_topic_response", {"user": instance.user, "topic": topic})
            pass
models.signals.post_save.connect(new_comment, sender=ThreadedComment)
