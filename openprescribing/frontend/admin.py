from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import OrgBookmark
from .models import SearchBookmark
from .models import User

admin.site.unregister(User)


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


@admin.register(User)
class UserWithProfile(UserAdmin):
    list_display = (UserAdmin.list_display[0], ) + (
        'is_staff', 'emails_received', 'emails_opened', 'emails_clicked')

    def emails_received(self, obj):
        return obj.profile.emails_received
    emails_received.short_description = 'Emails received'
    emails_received.admin_order_field = 'profile__emails_received'

    def emails_opened(self, obj):
        return obj.profile.emails_opened
    emails_opened.short_description = 'Emails opened'
    emails_opened.admin_order_field = 'profile__emails_received'

    def emails_clicked(self, obj):
        return obj.profile.emails_clicked
    emails_clicked.short_description = 'Links clicked'
    emails_clicked.admin_order_field = 'profile__emails_clicked'
