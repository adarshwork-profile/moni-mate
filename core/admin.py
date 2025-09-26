from django.contrib import admin, messages
from .models import UserProfile
from django.core.mail import send_mail
from django.conf import settings

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved', 'notify_email')
    list_filter = ('is_approved',)
    actions = ['approve_users','reject_users']

    def approve_users(self, request, queryset):
        for profile in queryset:
            profile.is_approved = True
            profile.user.is_active = True
            profile.user.save()
            profile.save()
            send_mail(
                'Account Approved - Moni-Mate',
                'Dear User,\nYour account has been approved. You can now log in.',
                settings.DEFAULT_FROM_EMAIL,
                [profile.notify_email]
            )
        self.message_user(request, "Selected users have been approved.", messages.SUCCESS)
    approve_users.short_description = "Approve selected users."

    def reject_users(self, request, queryset):
        for profile in queryset:
            send_mail(
                'Account Rejected - Moni-Mate',
                'Your account has been rejected. Please contact support for more information.',
                settings.DEFAULT_FROM_EMAIL,
                [profile.notify_email]
            )
            user = profile.user
            user.delete() # delete the created profiles.
        self.message_user(request, "Selected users have been rejected and deleted.", messages.SUCCESS)

    reject_users.short_description = "Reject selected users."
