from django import template
from django.contrib.contenttypes.models import ContentType

from forums.models import Forum

register = template.Library()

def show_forum(context, forum):
    return {
        "forum": forum,
        "group": context.get("group"),
    }
register.inclusion_tag("forums/forum_item.html", takes_context=True)(show_forum)

def forum_link(forum):
  return forum.get_absolute_url(forum.group)
register.simple_tag(forum_link)

class ForumsForGroupNode(template.Node):
    def __init__(self, group_name, context_name):
        self.group = template.Variable(group_name)
        self.context_name = context_name
    
    def render(self, context):
        try:
            group = self.group.resolve(context)
        except template.VariableDoesNotExist:
            return u''
        content_type = ContentType.objects.get_for_model(group)
        context[self.context_name] = Forum.objects.filter(
            content_type=content_type, object_id=group.id)
        return u''

def do_get_forums_for_group(parser, token):
    """
    Provides the template tag {% get_forums_for_group GROUP as VARIABLE %}
    """
    try:
        _tagname, group_name, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u'%(tagname)r tag syntax is as follows: '
            '{%% %(tagname)r GROUP as VARIABLE %%}' % {'tagname': tagname})
    return ForumsForGroupNode(group_name, context_name)

register.tag('get_forums_for_group', do_get_forums_for_group)


@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if 'search' in getvars:
        del getvars['search']
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path

