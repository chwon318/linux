from django import forms

from .models import ConversationMessage, DiaryConversation


class DiaryConversationForm(forms.ModelForm):
    mood = forms.CharField(
        label="오늘의 기분",
        max_length=30,
        required=True,
        error_messages={"required": "오늘의 기분을 입력해주세요."},
        widget=forms.TextInput(
            attrs={
                "placeholder": "예: 뿌듯함, 피곤함, 복잡함",
                "required": "required",
            }
        ),
    )

    class Meta:
        model = DiaryConversation
        fields = ["diary_date", "mood"]
        labels = {
            "diary_date": "기록할 날짜",
        }
        widgets = {
            "diary_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class UserMessageForm(forms.ModelForm):
    class Meta:
        model = ConversationMessage
        fields = ["content"]
        labels = {"content": "오늘 하루에게 들려줄 이야기"}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "친구에게 말하듯 편하게 적어주세요. 짧아도 괜찮습니다.",
                }
            )
        }
