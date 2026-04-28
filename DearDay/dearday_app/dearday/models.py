import re

from django.db import models
from django.utils import timezone


class DiaryConversation(models.Model):
    title = models.CharField(max_length=80)
    diary_date = models.DateField(default=timezone.localdate)
    mood = models.CharField(max_length=30, blank=True)
    final_diary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-diary_date", "-updated_at"]

    def __str__(self):
        return self.title

    @property
    def is_finished(self):
        return bool(self.final_diary.strip())

    def split_embedded_title(self):
        text = self.final_diary.strip()
        match = re.match(r"^\s*제목\s*[:：]\s*(.+?)\s*(?:\r?\n|$)", text)
        if not match:
            return "", text
        title = match.group(1).strip()
        body = text[match.end():].strip()
        body = re.sub(r"^\s*(?:본문|일기 본문)\s*[:：]\s*", "", body).strip()
        return title, body

    @property
    def display_title(self):
        embedded_title, _ = self.split_embedded_title()
        return embedded_title or self.title

    @property
    def display_diary(self):
        embedded_title, body = self.split_embedded_title()
        if embedded_title and body:
            return body
        return self.final_diary


class ConversationMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "사용자"),
        ("assistant", "AI"),
    ]

    conversation = models.ForeignKey(
        DiaryConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_role_display()} - {self.content[:30]}"
