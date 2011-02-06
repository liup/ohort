from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
    
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("companys_new_member", _("New Company Member"), _("a company you are a member of has a new member"), default=1)
        notification.create_notice_type("companys_created_new_member", _("New Member Of Company You Created"), _("a company you created has a new member"), default=2)
        notification.create_notice_type("companys_new_company", _("New Company Created"), _("a new company has been created"), default=1)
        
    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
