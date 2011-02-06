from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models

from groups.base import Group

class Company(Group):
    
    members = models.ManyToManyField(User, related_name='companys', verbose_name=_('members'))
    domain = models.CharField(_('Domain'), max_length=20, blank=False)
    location = models.CharField(_('Location'), max_length=100, blank=True)
    zipcode = models.CharField(_('ZipCode'), max_length=5, blank=True)
    website = models.URLField(_('Website'), blank=True)
    logo = models.URLField(_('Logo'), blank=True)
    
    def get_absolute_url(self):
        return reverse('company_detail', kwargs={'group_slug': self.slug})
    
    def get_url_kwargs(self):
        return {'group_slug': self.slug}
