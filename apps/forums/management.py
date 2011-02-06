from django.db.models import signals

from django.utils.translation import ugettext_noop as _

try:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("forums_forum_edited",
                                        _("Forum Edited"),
                                        _("your forum has been edited"))
        notification.create_notice_type("forums_revision_reverted",
                                        _("Forum Revision Reverted"),
                                        _("your revision has been reverted"))
        notification.create_notice_type("forums_observed_forum_changed",
                                        _("Observed Forum Changed"),
                                        _("an forum you observe has changed"))

        notification.create_notice_type("forums_topic_edited",
                                        _("Topic Edited"),
                                        _("your topic has been edited"))
        notification.create_notice_type("forums_revision_reverted",
                                        _("Topic Revision Reverted"),
                                        _("your revision has been reverted"))
        notification.create_notice_type("forums_observed_topic_changed",
                                        _("Observed Topic Changed"),
                                        _("an topic you observe has changed"))


    signals.post_syncdb.connect(create_notice_types,
                                sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
