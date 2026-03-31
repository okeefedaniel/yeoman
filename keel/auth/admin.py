from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Role, RoleAssignment, User


class RoleAssignmentInline(admin.TabularInline):
    model = RoleAssignment
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'org', 'is_staff')
    list_filter = BaseUserAdmin.list_filter + ('org',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Organization', {'fields': ('org',)}),
    )
    inlines = [RoleAssignmentInline]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'org')
    list_filter = ('role', 'org')
