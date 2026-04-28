from django.core.management.base import BaseCommand
from django.utils import timezone

from dearday.models import ConversationMessage, DiaryConversation
from dearday.services import fallback_diary


class Command(BaseCommand):
    help = "Create demo AI diary conversations when the database is empty."

    def handle(self, *args, **options):
        if DiaryConversation.objects.exists() or ConversationMessage.objects.exists():
            self.stdout.write("demo data already exists")
            return

        conversation = DiaryConversation.objects.create(
            title="조금 복잡했지만 끝은 괜찮았던 하루",
            diary_date=timezone.localdate(),
            mood="피곤하지만 뿌듯함",
        )
        messages = [
            ("assistant", "오늘 하루를 같이 천천히 정리해보자. 가장 먼저 떠오르는 장면이나 사건부터 편하게 말해줄래?"),
            ("user", "아침에는 좀 정신이 없었고, 오후에는 과제 때문에 계속 Docker Compose를 만졌다."),
            ("assistant", "과제 때문에 하루의 에너지를 꽤 많이 쓴 것 같아. 그 과정에서 제일 막혔던 순간은 언제였어?"),
            ("user", "Nginx랑 Django 정적 파일 연결이 헷갈렸다. 그래도 로그를 보면서 원인을 찾으니까 조금 뿌듯했다."),
            ("assistant", "막혔던 부분을 직접 추적해서 해결한 게 오늘의 중요한 장면처럼 들려. 그때 마음이 어떻게 바뀌었어?"),
            ("user", "처음엔 답답했는데, 해결하고 나서는 내가 구조를 조금 이해한 것 같아서 안심됐다."),
        ]
        ConversationMessage.objects.bulk_create(
            [ConversationMessage(conversation=conversation, role=role, content=content) for role, content in messages]
        )
        conversation.final_diary = fallback_diary(conversation)
        conversation.save(update_fields=["final_diary", "updated_at"])
        self.stdout.write(self.style.SUCCESS("demo diary conversation created"))
