from django.contrib import admin

from .models import ConversationMessage, DiaryConversation


class ConversationMessageInline(admin.TabularInline):
    model = ConversationMessage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(DiaryConversation)
class DiaryConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "diary_date", "mood", "is_finished", "updated_at")
    list_filter = ("diary_date",)
    search_fields = ("title", "mood", "final_diary")
    inlines = [ConversationMessageInline]


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content",)
