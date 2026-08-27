"""
Admin configuration for Dance Style.
"""
from django.contrib import admin
from .models import DanceStyle


@admin.register(DanceStyle)
class DanceStyleAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_tag', 'is_active', 'package_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    ordering = ['name']
    
    def package_count(self, obj):
        return obj.get_package_count()
    package_count.short_description = 'Active Packages'