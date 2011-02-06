from django.conf.urls.defaults import *

from companys.models import Company

from groups.bridge import ContentBridge


bridge = ContentBridge(Company, 'companys')

urlpatterns = patterns('companys.views',
    url(r'^$', 'companys', name="company_list"),
    url(r'^create/$', 'create', name="company_create"),
    url(r'^your_companys/$', 'your_companys', name="your_companys"),
    
    # company-specific
    url(r'^company/(?P<group_slug>[-\w]+)/$', 'company', name="company_detail"),
    url(r'^company/(?P<group_slug>[-\w]+)/delete/$', 'delete', name="company_delete"),
	url(r'^company/(?P<group_slug>[-\w]+)/members/$', 'company_members', name="company_members"),
)

urlpatterns += bridge.include_urls('forums.urls', r'^company/(?P<group_slug>[-\w]+)/forums/')
#urlpatterns += bridge.include_urls('wiki.urls', r'^company/(?P<group_slug>[-\w]+)/wiki/')
urlpatterns += bridge.include_urls('pinax.apps.photos.urls', r'^company/(?P<group_slug>[-\w]+)/photos/')
