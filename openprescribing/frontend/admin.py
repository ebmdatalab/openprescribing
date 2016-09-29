from django.contrib import admin
from .models import SearchBookmark, OrgBookmark


@admin.register(SearchBookmark)
class SearchBookmarkAdmin(admin.ModelAdmin):
    pass

@admin.register(OrgBookmark)
class OrgBookmarkAdmin(admin.ModelAdmin):
    pass
