import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import EmailMessage
from .models import MailLog
from .models import OrgBookmark
from .models import SearchBookmark
from .models import User
from allauth.account.models import EmailAddress
from allauth.account.models import EmailConfirmation

admin.site.unregister(User)
admin.site.unregister(EmailAddress)
admin.site.unregister(EmailConfirmation)


class UserVerifiedFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Verified'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'verified'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            (True, 'Yes'),
            (False, 'No'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'True':
            return queryset.filter(emailaddress__verified=True)
        elif self.value() == 'False':
            return queryset.filter(emailaddress__verified=False)


@admin.register(SearchBookmark)
class SearchBookmarkAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('name', 'user', 'created_at', 'approved')
    list_filter = ('approved', 'created_at')
    readonly_fields = ('dashboard_link',)

    def dashboard_link(self, obj):
        return format_html(
            '<a href="{}">view in site</a>', obj.dashboard_url())


@admin.register(OrgBookmark)
class OrgBookmarkAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('name', 'user', 'created_at', 'approved')
    list_filter = ('approved', 'created_at')
    readonly_fields = ('dashboard_link',)

    def dashboard_link(self, obj):
        return format_html(
            '<a href="{}">view in site</a>', obj.dashboard_url())


class EmailMessageInline(admin.TabularInline):
    model = EmailMessage


@admin.register(User)
class UserWithProfile(UserAdmin):
    list_display = (UserAdmin.list_display[0], ) + (
        'is_staff', 'emails_received', 'emails_opened', 'emails_clicked',
        'orgbookmarks', 'searchbookmarks'
    )
    list_filter = (UserVerifiedFilter, )
    inlines = [
        EmailMessageInline,
    ]

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        return qs.annotate(
            searchbookmark_count=Count('searchbookmark', distinct=True),
            orgbookmark_count=Count('orgbookmark', distinct=True))

    def orgbookmarks(self, obj):
        return obj.orgbookmark_set.count()
    orgbookmarks.short_description = 'Orgs bookmarked'
    orgbookmarks.admin_order_field = 'orgbookmark_count'

    def searchbookmarks(self, obj):
        return obj.searchbookmark_set.count()
    searchbookmarks.short_description = 'Searches bookmarked'
    searchbookmarks.admin_order_field = 'searchbookmark_count'

    def emails_received(self, obj):
        return obj.profile.emails_received
    emails_received.short_description = 'Emails received'
    emails_received.admin_order_field = 'profile__emails_received'

    def emails_opened(self, obj):
        return obj.profile.emails_opened
    emails_opened.short_description = 'Emails opened'
    emails_opened.admin_order_field = 'profile__emails_opened'

    def emails_clicked(self, obj):
        return obj.profile.emails_clicked
    emails_clicked.short_description = 'Links clicked'
    emails_clicked.admin_order_field = 'profile__emails_clicked'


class MailLogInline(admin.TabularInline):
    model = MailLog
    fields = readonly_fields = (
        'timestamp', 'event_type', 'message_id', 'recipient', 'tags',
        'reject_reason', 'metadata_prettyprinted')

    def metadata_prettyprinted(self, obj):
        return mark_safe("<pre>%s</pre>" % json.dumps(obj.metadata, indent=2))

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('to', 'subject', 'tags', 'created_at', 'send_count')
    list_filter = (
        'tags', 'subject')
    readonly_fields = fields = (
        'message_id', 'to', 'subject', 'tags', 'created_at', 'send_count',
        'user', 'message_html',)
    inlines = [
        MailLogInline
    ]
    date_hierarchy = 'created_at'

    def message_html(self, obj):
        if obj.message.alternatives:
            return mark_safe(obj.message.alternatives[0][0])
        else:
            return mark_safe(obj.message.body)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MailLog)
class MailLogAdmin(admin.ModelAdmin):
    date_hierarchy = 'timestamp'
    list_display = (
        'timestamp', 'event_type', 'message_id', 'recipient', 'tags')
    list_filter = (
        'event_type', 'recipient', 'tags')
    readonly_fields = fields = (
        'timestamp', 'event_type', 'message_id', 'recipient', 'tags',
        'reject_reason', 'metadata_prettyprinted')

    def metadata_prettyprinted(self, obj):
        return mark_safe("<pre>%s</pre>" % json.dumps(obj.metadata, indent=2))

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
