from django import template
from companys.forms import CompanyForm

register = template.Library()


@register.inclusion_tag("companys/company_item.html", takes_context=True)
def show_company(context, company):
	request = context['request']
	if not request.user.is_authenticated():
		is_member = False
	else:
		is_member = company.user_is_member(request.user)
	return {'company': company, 'is_member': is_member, 'request': request}

# @@@ should move these next two as they aren't particularly company-specific

@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if 'search' in getvars:
        del getvars['search']
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path


@register.simple_tag
def persist_getvars(request):
    getvars = request.GET.copy()
    if len(getvars.keys()) > 0:
        return "?%s" % getvars.urlencode()
    return ''
