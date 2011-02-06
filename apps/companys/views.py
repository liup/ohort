from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _

from django.conf import settings

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from companys.models import Company 
from companys.forms import CompanyForm, CompanyUpdateForm

from emailconfirmation.models import EmailAddress, EmailConfirmation
import re

TOPIC_COUNT_SQL = """
SELECT COUNT(*)
FROM forums_forum
WHERE
    forums_forum.object_id = companys_company.id AND
    forums_forum.content_type_id = %s
"""
MEMBER_COUNT_SQL = """
SELECT COUNT(*)
FROM companys_company_members
WHERE companys_company_members.company_id = companys_company.id
"""

@login_required
def create(request, form_class=CompanyForm, template_name="companys/create.html"):
    if not request.user.is_staff:
        return render_to_response("companys/your_companys.html", {
            "companys": Company.objects.filter(members=request.user).order_by("name"),
        }, context_instance=RequestContext(request))

    company_form = form_class(request.POST or None)
    
    if company_form.is_valid():
        company = company_form.save(commit=False)
        company.creator = request.user
        company.save()
        company.members.add(request.user)
        company.save()
        if notification:
            # @@@ might be worth having a shortcut for sending to all users
            notification.send(User.objects.all(), "companys_new_company",
                {"company": company}, queue=True)
        return HttpResponseRedirect(company.get_absolute_url())
    
    return render_to_response(template_name, {
        "company_form": company_form,
    }, context_instance=RequestContext(request))


def companys(request, template_name="companys/companys.html"):
    
    companys = Company.objects.all()
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        companys = (companys.filter(name__icontains=search_terms) |
            companys.filter(description__icontains=search_terms))
    
    content_type = ContentType.objects.get_for_model(Company)
    
    companys = companys.extra(select=SortedDict([
        ('member_count', MEMBER_COUNT_SQL),
        ('topic_count', TOPIC_COUNT_SQL),
    ]), select_params=(content_type.id,))
    
    return render_to_response(template_name, {
        'companys': companys,
        'search_terms': search_terms,
    }, context_instance=RequestContext(request))


def delete(request, group_slug=None, redirect_url=None):
    company = get_object_or_404(Company, slug=group_slug)
    if not redirect_url:
        redirect_url = reverse('company_list')
    
    # @@@ eventually, we'll remove restriction that company.creator can't leave company but we'll still require company.members.all().count() == 1
    if (request.user.is_authenticated() and request.method == "POST" and
            request.user == company.creator and company.members.all().count() == 1):
        company.delete()
        request.user.message_set.create(message=_("Company %(company_name)s deleted.") % {"company_name": company.name})
        # no notification required as the deleter must be the only member
    
    return HttpResponseRedirect(redirect_url)


@login_required
def your_companys(request, template_name="companys/your_companys.html"):
    return render_to_response(template_name, {
        "companys": Company.objects.filter(members=request.user).order_by("name"),
    }, context_instance=RequestContext(request))
	
	
def company_members(request, group_slug=None, template_name="companys/company_members.html"):
	company = get_object_or_404(Company, slug=group_slug)
	return render_to_response(template_name, {
		"company": company,
    }, context_instance=RequestContext(request))


@login_required
def company(request, group_slug=None, form_class=CompanyUpdateForm,
        template_name="companys/company.html"):
    company = get_object_or_404(Company, slug=group_slug)
    
    company_form = form_class(request.POST or None, instance=company)
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        is_member = company.user_is_member(request.user)
    
    action = request.POST.get('action')
    if action == 'update' and company_form.is_valid():
        company = company_form.save()
    elif action == 'join':
        if not is_member:
            # verify company email 
            emails = EmailAddress.objects.filter(user__exact=request.user)
            is_employee = False
            pattern = '@' + company.domain
            for email in emails:
                if email.verified:
                    if re.search(pattern, email.email):
                        is_employee = True
            if not is_employee:
                request.user.message_set.create(
                    message=_("Please verify your company email first %(company_name)s") % {"company_name": company.name})
                return HttpResponseRedirect("/account/email")
            else:
                company.members.add(request.user)
                request.user.message_set.create(
                    message=_("You have joined the company %(company_name)s") % {"company_name": company.name})
                is_member = True
                if notification:
                    notification.send([company.creator], "companys_created_new_member", {"user": request.user, "company": company})
                    notification.send(company.members.all(), "companys_new_member", {"user": request.user, "company": company})
        else:
            request.user.message_set.create(
                message=_("You have already joined company %(company_name)s") % {"company_name": company.name})
    elif action == 'leave':
        company.members.remove(request.user)
        request.user.message_set.create(message="You have left the company %(company_name)s" % {"company_name": company.name})
        is_member = False
        if notification:
            pass # @@@ no notification on departure yet
    
    # join the company for user automatically if s/he already verified her/his company email
    if not is_member:
        # verify company email 
        emails = EmailAddress.objects.filter(user__exact=request.user)
        is_employee = False
        pattern = '@' + company.domain
        for email in emails:
            if email.verified:
                if re.search(pattern, email.email):
                    is_employee = True
        if is_employee:
            company.members.add(request.user)
            is_member = True

    return render_to_response(template_name, {
        "company_form": company_form,
        "company": company,
        "group": company, # @@@ this should be the only context var for the company
        "is_member": is_member,
    }, context_instance=RequestContext(request))
