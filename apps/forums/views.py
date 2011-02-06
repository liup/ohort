import os
import pprint

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import (Http404, HttpResponseRedirect,
                         HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden)
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import select_template
from django.utils.translation import ugettext_lazy as _ # @@@ really should be ugettext

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

try:
    from notification import models as notification
except ImportError:
    notification = None

from threadedcomments.models import ThreadedComment

from forums.forms import ForumForm
from forums.models import Forum
from forums.forms import ForumTopicForm
from forums.forms import TopicForm
from forums.models import Topic

ALL_TOPICS = Topic.non_removed_objects.all()
ALL_FORUMS = Forum.non_removed_objects.all()

def get_ct(obj):
    """ Return the ContentType of the object's model.
    """
    return ContentType.objects.get(app_label=obj._meta.app_label,
                                   model=obj._meta.module_name)

def has_read_perm(user, group, is_member, is_private):
    """ Return True if the user has permission to *read*
    Articles, False otherwise.
    """
    if (group is None) or (is_member is None) or is_member(user, group):
        return True
    if (is_private is not None) and is_private(group):
        return False
    return True

def has_write_perm(user, group, is_member):
    """ Return True if the user have permission to edit Articles,
    False otherwise.
    """
    if (group is None) or (is_member is None) or is_member(user, group):
        return True
    return False

def get_url(urlname, group=None, args=None, kw=None, bridge=None):
    if group is None:
        # @@@ due to group support passing args isn't really needed
        return reverse(urlname, args=args, kwargs=kw)
    else:
        return bridge.reverse(urlname, group, kwargs=kw)
        

def forums(request, group_slug=None, form_class=ForumForm, template_name="forums/forums.html", bridge=None):

    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if group:
            is_member = group.user_is_member(request.user)
        else:
            is_member = True
    
    if group:
        group_base = bridge.group_base_template()
    else:
        group_base = None
    
    if request.method == "POST":
        if request.user.is_authenticated():
            if is_member:
                forum_form = form_class(request.POST)
                if forum_form.is_valid():
                    forum = forum_form.save(commit=False)
                    if group:
                        group.associate(forum, commit=False)
                    forum.creator = request.user
                    forum.save()
                    request.user.message_set.create(message=_("You have started the group %(forum_title)s") % {"forum_title": forum.title})
                    forum_form = form_class() # @@@ is this the right way to reset it?
            else:
                request.user.message_set.create(message=_("You are not a member and so cannot start a new forum"))
                forum_form = form_class()
        else:
            return HttpResponseForbidden()
    else:
        forum_form = form_class()
    
    if group:
        forums = group.content_objects(Forum)
        search_terms = request.GET.get('search', '')
        if search_terms:
            forums = (forums.filter(title__icontains=search_terms) |
                forums.filter(body__icontains=search_terms))
    else:
        forums = Forum.objects.filter(object_id=None)
    
    return render_to_response(template_name, {
        "group": group,
        "forum_form": forum_form,
        "is_member": is_member,
        "forums": forums,
        "group_base": group_base,
    }, context_instance=RequestContext(request))


def forum(request, forum_id, group_slug=None, edit=False, template_name="forums/forum.html", bridge=None, form_class=ForumTopicForm, new_topic=False):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if group:
            is_member = group.user_is_member(request.user)
        else:
            is_member = True
    
    if group:
        forums = group.content_objects(Forum)
        topics = group.content_objects(Topic).filter(forum=forum_id)
        search_terms = request.GET.get('search', '')
        if search_terms:
            topics = (topics.filter(title__icontains=search_terms) |
                topics.filter(body__icontains=search_terms))
    else:
        forums = Forum.objects.filter(object_id=None)
        topics = Topic.objects.filter(object_id=None)
    
    forum = get_object_or_404(forums, id=forum_id)
    
    if notification is not None:
        is_observing = notification.is_observing(forum, request.user)
    else:
        is_observing = False
    
    if (request.method == "POST" and edit == True and (request.user == forum.creator or request.user == forum.group.creator)):
        forum.body = request.POST["body"]
        forum.save()
        return HttpResponseRedirect(forum.get_absolute_url(group))
    elif request.method == "POST":
        if request.user.is_authenticated():
            if is_member:
                topic_form = form_class(request.POST)
                if topic_form.is_valid():
                    topic = topic_form.save(commit=False)
                    if group:
                        group.associate(topic, commit=False)
                    topic.creator = request.user
                    topic.forum_id = forum_id
                    topic.save()
                    request.user.message_set.create(message=_("You have started the topic %(topic_title)s") % {"topic_title": topic.title})
                    topic_form = form_class() # @@@ is this the right way to reset it?
                    if notification:
                        # send notification to company member who are watching the forum
                        members = forum.group.members.all()
                        watching_users = []
                        for u in members:
                            if notification.is_observing(forum, u):
                                watching_users.append(u)
                        notification.send(watching_users, "forums_observed_forum_changed", {"user": request.user, "company": forum.group})
            else:
                request.user.message_set.create(message=_("You are not a member and so cannot start a new topic"))
                topic_form = form_class()
        else:
            return HttpResponseForbidden()
    else:
        topic_form = form_class()
    
    if group:
        group_base = bridge.group_base_template()
    else:
        group_base = None
    
    return render_to_response(template_name, {
        "is_member": is_member,
        "forum": forum,
        "topics": topics,
        "topic_form": topic_form,
        "edit": edit,
        "group": group,
        "group_base": group_base,
        "is_observing": is_observing,
        "can_observe": True
    }, context_instance=RequestContext(request))


def forum_delete(request, forum_id, group_slug=None, bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        forums = group.content_objects(Forum)
    else:
        forums = Forum.objects.filter(object_id=None)
    
    forum = get_object_or_404(forums, id=forum_id)
    
    if (request.method == "POST" and (request.user == forum.creator or request.user == forum.group.creator)):
        ThreadedComment.objects.all_for_object(forum).delete()
        forum.delete()
    
    return HttpResponseRedirect(request.POST["next"])


@login_required
def observe_forum(request, forum_id,
                    group_slug=None, bridge=None,
                    forum_qs=ALL_FORUMS,
                    template_name='recentchanges.html',
                    template_dir='forums',
                    extra_context=None,
                    is_member=None,
                    is_private=None,
                    *args, **kw):
    if request.method == 'POST':
        forum_args = {'id': forum_id}
        group = None
        if group_slug is not None:
            try:
                group = bridge.get_group(group_slug)
            except ObjectDoesNotExist:
                raise Http404
            forum_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
            allow_read = has_read_perm(request.user, group, is_member,
                                       is_private)
        else:
            group = None
            allow_read = True

        if not allow_read:
            return HttpResponseForbidden()

        forum = get_object_or_404(forum_qs, **forum_args)

        notification.observe(forum, request.user,
                             'forums_observed_forum_changed')
        
        url = get_url('forums_forum', group, kw={
            'forum_id': forum.id,
        }, bridge=bridge)
        
        return redirect_to(request, url)

    return HttpResponseNotAllowed(['POST'])


@login_required
def stop_observing_forum(request, forum_id,
                           group_slug=None, bridge=None,
                           forum_qs=ALL_FORUMS,
                           template_name='recentchanges.html',
                           template_dir='forums',
                           extra_context=None,
                           is_member=None,
                           is_private=None,
                           *args, **kw):
    if request.method == 'POST':
        forum_args = {'id': forum_id}
        group = None
        if group_slug is not None:
            try:
                group = bridge.get_group(group_slug)
            except ObjectDoesNotExist:
                raise Http404
            forum_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
            allow_read = has_read_perm(request.user, group, is_member,
                                       is_private)
        else:
            group = None
            allow_read = True
            forum_args.update({'object_id': None})

        if not allow_read:
            return HttpResponseForbidden()

        forum = get_object_or_404(forum_qs, **forum_args)

        notification.stop_observing(forum, request.user)
        
        url = get_url('forums_forum', group, kw={
            'forum_id': forum.id,
        }, bridge=bridge)
        
        return redirect_to(request, url)
    return HttpResponseNotAllowed(['POST'])




def topics(request, group_slug=None, form_class=TopicForm, template_name="forums/topics.html", bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        if group:
            is_member = group.user_is_member(request.user)
        else:
            is_member = True
    
    if group:
        group_base = bridge.group_base_template()
    else:
        group_base = None
    
    if request.method == "POST":
        if request.user.is_authenticated():
            if is_member:
                topic_form = form_class(request.POST)
                if topic_form.is_valid():
                    topic = topic_form.save(commit=False)
                    if group:
                        group.associate(topic, commit=False)
                    topic.creator = request.user
                    topic.save()
                    request.user.message_set.create(message=_("You have started the topic %(topic_title)s") % {"topic_title": topic.title})
                    topic_form = form_class() # @@@ is this the right way to reset it?
            else:
                request.user.message_set.create(message=_("You are not a member and so cannot start a new topic"))
                topic_form = form_class()
        else:
            return HttpResponseForbidden()
    else:
        topic_form = form_class()
    
    if group:
        topics = group.content_objects(Topic)
    else:
        topics = Topic.objects.filter(object_id=None)
    
    return render_to_response(template_name, {
        "group": group,
        "topic_form": topic_form,
        "is_member": is_member,
        "topics": topics,
        "group_base": group_base,
    }, context_instance=RequestContext(request))


def topic(request, topic_id, group_slug=None, edit=False, template_name="forums/topic.html", bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        topics = group.content_objects(Topic)
    else:
        topics = Topic.objects.filter(object_id=None)
    
    topic = get_object_or_404(topics, id=topic_id)
    if notification is not None:
        is_observing = notification.is_observing(topic, request.user)
    else:
        is_observing = False
    
    if (request.method == "POST" and edit == True and (request.user == topic.creator or request.user == topic.group.creator)):
        topic.body = request.POST["body"]
        topic.save()
        return HttpResponseRedirect(topic.get_absolute_url(group))
    
    if group:
        group_base = bridge.group_base_template()
    else:
        group_base = None
    
    if notification:
        # send notification to company member who are watching the topic
        members = topic.group.members.all()
        watching_users = []
        for u in members:
            if notification.is_observing(topic, u):
                watching_users.append(u)
        notification.send(watching_users, "forums_observed_topic_changed", {"user": request.user, "company": topic.group})
    return render_to_response(template_name, {
        "topic": topic,
        "edit": edit,
        "group": group,
        "group_base": group_base,
        "is_observing": is_observing,
        "can_observe": True
    }, context_instance=RequestContext(request))


def topic_delete(request, topic_id, group_slug=None, bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        topics = group.content_objects(Topic)
    else:
        topics = Topic.objects.filter(object_id=None)
    
    topic = get_object_or_404(topics, id=topic_id)
    
    if (request.method == "POST" and (request.user == topic.creator or request.user == topic.group.creator)):
        ThreadedComment.objects.all_for_object(topic).delete()
        topic.delete()
    
    return HttpResponseRedirect(request.POST["next"])


@login_required
def observe_topic(request, topic_id,
                    group_slug=None, bridge=None,
                    topic_qs=ALL_TOPICS,
                    template_name='recentchanges.html',
                    template_dir='forums',
                    extra_context=None,
                    is_member=None,
                    is_private=None,
                    *args, **kw):
    if request.method == 'POST':
        topic_args = {'id': topic_id}
        group = None
        if group_slug is not None:
            try:
                group = bridge.get_group(group_slug)
            except ObjectDoesNotExist:
                raise Http404
            topic_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
            allow_read = has_read_perm(request.user, group, is_member,
                                       is_private)
        else:
            group = None
            allow_read = True

        if not allow_read:
            return HttpResponseForbidden()

        topic = get_object_or_404(topic_qs, **topic_args)

        notification.observe(topic, request.user,
                             'forums_observed_topic_changed')
        
        url = get_url('forums_topic', group, kw={
            'topic_id': topic.id,
        }, bridge=bridge)
        
        return redirect_to(request, url)

    return HttpResponseNotAllowed(['POST'])


@login_required
def stop_observing_topic(request, topic_id,
                           group_slug=None, bridge=None,
                           topic_qs=ALL_TOPICS,
                           template_name='recentchanges.html',
                           template_dir='forums',
                           extra_context=None,
                           is_member=None,
                           is_private=None,
                           *args, **kw):
    if request.method == 'POST':
        topic_args = {'id': topic_id}
        group = None
        if group_slug is not None:
            try:
                group = bridge.get_group(group_slug)
            except ObjectDoesNotExist:
                raise Http404
            topic_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
            allow_read = has_read_perm(request.user, group, is_member,
                                       is_private)
        else:
            group = None
            allow_read = True
            topic_args.update({'object_id': None})

        if not allow_read:
            return HttpResponseForbidden()

        topic = get_object_or_404(topic_qs, **topic_args)

        notification.stop_observing(topic, request.user)
        
        url = get_url('forums_topic', group, kw={
            'topic_id': topic.id,
        }, bridge=bridge)
        
        return redirect_to(request, url)
    return HttpResponseNotAllowed(['POST'])


