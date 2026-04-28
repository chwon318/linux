import calendar
from datetime import date

from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import DiaryConversationForm, UserMessageForm
from .models import ConversationMessage, DiaryConversation
from .services import DEFAULT_DIARY_TITLE, generate_diary, generate_follow_up


def add_month(year, month, offset):
    month_index = year * 12 + (month - 1) + offset
    return month_index // 12, month_index % 12 + 1


def dashboard(request):
    conversations = DiaryConversation.objects.annotate(message_count=Count("messages"))
    writing_diaries = conversations.filter(final_diary="")
    finished_diaries = conversations.exclude(final_diary="")
    recent_conversations = conversations.order_by("-updated_at", "-id")[:12]
    writing_items = writing_diaries.order_by("-updated_at", "-id")
    finished_items = finished_diaries.order_by("-updated_at", "-id")
    recent_diaries = finished_diaries.order_by("-updated_at", "-id")[:5]
    today = timezone.localdate()
    selected_status = request.GET.get("status", "")
    if selected_status == "writing":
        selected_status_label = "작성중인 일기"
        selected_status_items = writing_diaries
    elif selected_status == "finished":
        selected_status_label = "작성된 일기"
        selected_status_items = finished_diaries
    else:
        selected_status = ""
        selected_status_label = ""
        selected_status_items = []
    selected_date = None
    selected_date_param = request.GET.get("date", "")
    if selected_date_param:
        try:
            selected_date = date.fromisoformat(selected_date_param)
        except ValueError:
            selected_date = None

    calendar_year = selected_date.year if selected_date else today.year
    calendar_month = selected_date.month if selected_date else today.month
    if not selected_date:
        try:
            requested_year = int(request.GET.get("year", calendar_year))
            requested_month = int(request.GET.get("month", calendar_month))
            if 1 <= requested_month <= 12:
                calendar_year = requested_year
                calendar_month = requested_month
        except ValueError:
            pass

    prev_year, prev_month = add_month(calendar_year, calendar_month, -1)
    next_year, next_month = add_month(calendar_year, calendar_month, 1)
    written_dates = (
        finished_diaries
        .filter(diary_date__year=calendar_year, diary_date__month=calendar_month)
        .values("diary_date")
        .annotate(count=Count("id", distinct=True))
    )
    diary_counts = {item["diary_date"].day: item["count"] for item in written_dates}
    calendar_weeks = []
    sunday_start_calendar = calendar.Calendar(firstweekday=6)
    for week in sunday_start_calendar.monthdayscalendar(calendar_year, calendar_month):
        calendar_weeks.append(
            [
                {
                    "day": day,
                    "count": diary_counts.get(day, 0),
                    "has_diary": day in diary_counts,
                    "is_today": day == today.day and calendar_year == today.year and calendar_month == today.month,
                    "is_selected": bool(selected_date and day == selected_date.day and calendar_year == selected_date.year and calendar_month == selected_date.month),
                    "date_param": f"{calendar_year}-{calendar_month:02d}-{day:02d}" if day else "",
                }
                for day in week
            ]
        )
    selected_diaries = finished_diaries.filter(diary_date=selected_date) if selected_date else []
    context = {
        "conversations": recent_conversations,
        "recent_diaries": recent_diaries,
        "writing_items": writing_items,
        "finished_items": finished_items,
        "writing_count": writing_diaries.count(),
        "finished_count": finished_diaries.count(),
        "selected_status": selected_status,
        "selected_status_label": selected_status_label,
        "selected_status_items": selected_status_items,
        "calendar_month_label": f"{calendar_year}년 {calendar_month}월",
        "calendar_prev_url": f"?year={prev_year}&month={prev_month:02d}",
        "calendar_next_url": f"?year={next_year}&month={next_month:02d}",
        "calendar_today_url": f"?year={today.year}&month={today.month:02d}",
        "calendar_written_days": sum(diary_counts.values()),
        "calendar_weeks": calendar_weeks,
        "selected_date": selected_date,
        "selected_diaries": selected_diaries,
    }
    return render(request, "dearday/dashboard.html", context)


def conversation_new(request):
    if request.method == "POST":
        form = DiaryConversationForm(request.POST)
        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.title = f"{conversation.diary_date:%Y-%m-%d} {DEFAULT_DIARY_TITLE}"
            conversation.save()
            ConversationMessage.objects.create(
                conversation=conversation,
                role="assistant",
                content=(
                    "오늘 하루를 같이 천천히 정리해보자. "
                    "가장 먼저 떠오르는 장면이나 사건부터 편하게 말해줄래?"
                ),
            )
            messages.success(request, "새 하루 대화를 시작했습니다.")
            return redirect("conversation_detail", pk=conversation.pk)
    else:
        initial = {}
        date_param = request.GET.get("date", "")
        if date_param:
            try:
                initial["diary_date"] = date.fromisoformat(date_param)
            except ValueError:
                pass
        form = DiaryConversationForm(initial=initial)
    return render(request, "dearday/conversation_form.html", {"form": form})


def conversation_detail(request, pk):
    conversation = get_object_or_404(DiaryConversation, pk=pk)
    form = UserMessageForm()
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "send":
            form = UserMessageForm(request.POST)
            if form.is_valid():
                user_message = form.save(commit=False)
                user_message.conversation = conversation
                user_message.role = "user"
                user_message.save()
                ai_reply = generate_follow_up(conversation)
                assistant_message = ConversationMessage.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=ai_reply,
                )
                if is_ajax:
                    return JsonResponse(
                        {
                            "ok": True,
                            "user": {
                                "role": user_message.role,
                                "content": user_message.content,
                            },
                            "assistant": {
                                "role": assistant_message.role,
                                "content": assistant_message.content,
                            },
                        }
                    )
                messages.success(request, "오늘 하루가 다음 질문을 준비했습니다.")
                return redirect("conversation_detail", pk=conversation.pk)
            if is_ajax:
                return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        elif action == "generate":
            generated_title, generated_diary = generate_diary(conversation)
            conversation.title = generated_title
            conversation.final_diary = generated_diary
            conversation.save(update_fields=["title", "final_diary", "updated_at"])
            if is_ajax:
                return JsonResponse(
                    {
                        "ok": True,
                        "title": conversation.title,
                        "final_diary": conversation.final_diary,
                    }
                )
            messages.success(request, "대화를 바탕으로 일기를 작성했습니다.")
            return redirect("conversation_detail", pk=conversation.pk)
        elif action == "update_diary":
            edited_diary = request.POST.get("final_diary", "").strip()
            edited_date_value = request.POST.get("diary_date", "").strip()
            if not edited_diary:
                if is_ajax:
                    return JsonResponse(
                        {"ok": False, "error": "일기 내용을 입력해주세요."},
                        status=400,
                    )
                messages.error(request, "일기 내용을 입력해주세요.")
                return redirect("conversation_detail", pk=conversation.pk)
            try:
                edited_date = date.fromisoformat(edited_date_value)
            except ValueError:
                if is_ajax:
                    return JsonResponse(
                        {"ok": False, "error": "날짜를 올바르게 입력해주세요."},
                        status=400,
                    )
                messages.error(request, "날짜를 올바르게 입력해주세요.")
                return redirect("conversation_detail", pk=conversation.pk)
            conversation.diary_date = edited_date
            conversation.final_diary = edited_diary
            conversation.save(update_fields=["diary_date", "final_diary", "updated_at"])
            if is_ajax:
                return JsonResponse(
                    {
                        "ok": True,
                        "diary_date": conversation.diary_date.isoformat(),
                        "final_diary": conversation.final_diary,
                    }
                )
            messages.success(request, "일기를 수정했습니다.")
            return redirect("conversation_detail", pk=conversation.pk)

    return render(
        request,
        "dearday/conversation_detail.html",
        {
            "conversation": conversation,
            "chat_messages": conversation.messages.all(),
            "form": form,
        },
    )


def conversation_delete(request, pk):
    conversation = get_object_or_404(DiaryConversation, pk=pk)
    if request.method == "POST":
        response_data = {
            "ok": True,
            "id": conversation.pk,
            "title": conversation.title,
            "is_finished": conversation.is_finished,
            "diary_date": conversation.diary_date.isoformat(),
        }
        conversation.delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(response_data)
        messages.success(request, "하루 대화를 삭제했습니다.")
        return redirect("dashboard")
    return redirect("dashboard")
