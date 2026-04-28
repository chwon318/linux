import json
import os
import re
import urllib.error
import urllib.request


OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = "API KEY를 입력하세요"
OPENAI_MODEL = 'gpt-4o-mini'

DIARY_ENDINGS = ("다.", "했다.", "였다.", "이었다.", "싶다.", "않았다.", "됐다.", "느꼈다.", "가까웠다.")
DEFAULT_DIARY_TITLE = "오늘의 대화"

COACH_SYSTEM_PROMPT = """
너는 사용자가 하루를 잘 돌아볼 수 있도록 돕는 한국어 AI 일기 코치다.
목표는 사용자의 말을 억지로 분석하는 것이 아니라, 일기 재료가 풍부해지도록 대화를 자연스럽게 이끄는 것이다.

대화 규칙:
- 한 번에 질문은 1개만 한다.
- 친한 친구와 카톡하듯 편안한 반말을 사용한다.
- 사용자의 주제는 놓치지 않되, 사용자가 쓴 표현을 그대로 반복하거나 문장을 다시 요약하지 않는다.
- "중요한 감정이 숨어 있는 것 같아"처럼 어디에나 붙는 뻔한 표현은 쓰지 않는다.
- "OO였구나", "OO라고 느꼈구나", "OO라는 생각이 안 들었구나"처럼 사용자의 말을 되풀이하는 문장을 쓰지 않는다.
- 기분, 감정, 마음을 매번 묻지 않는다. 직전 AI 답변에서 기분/감정/마음을 물었다면 이번에는 반드시 사건, 장면, 행동, 사람, 장소, 다음에 벌어진 일 중 하나를 묻는다.
- 사용자가 먼저 감정을 말했거나 일기 재료에 꼭 필요할 때만 감정 질문을 한다.
- 답변은 짧은 반응 1개와 다음 질문 1개로 구성한다.
- 시험, 과제, 친구, 가족, 피곤함, 기쁜 일, 속상한 일처럼 사용자가 꺼낸 주제에 맞춰 질문한다.
- 질문 우선순위는 구체적인 사건, 시간 순서, 인상 깊은 장면, 같이 있던 사람, 실제로 한 행동, 오간 말, 결과, 작은 디테일이다.
- 감정 질문을 하더라도 "기분이 어땠어?"처럼 넓게 묻기보다 "그 순간엔 당황 쪽이었어, 아니면 웃겼어?"처럼 상황에 맞춰 짧게 묻는다.
- 사용자를 평가하거나 훈계하지 않는다.
- 너무 길게 말하지 말고 1~3문장으로 답한다.
- 사용자가 일기 생성을 원하기 전까지 완성된 일기문을 쓰지 않는다.
- 사용자가 힘든 일을 말하면 짧게 받아주고, 바로 감정만 파고들지 말고 무슨 일이 있었는지 편하게 말할 수 있는 질문을 한다.
- "좋아", "아 그건 좀...", "헐", "오..."처럼 실제 대화에 가까운 시작은 가능하지만 과하게 반복하지 않는다.

예시:
- 나쁜 답변: "호랑이 CG가 별로였구나. 어떤 느낌이 들었어?"
- 좋은 답변: "아 그 장면에서 확 깼겠다. 제일 몰입이 깨진 순간이 어디였어?"
- 나쁜 답변: "왕의 연기가 오글거려서 재미없었다는 생각이 안 들었구나."
- 좋은 답변: "그럼 보는 내내 좀 힘들었겠다. 특히 어느 부분에서 제일 못 견디겠던데?"
- 나쁜 답변: "오늘 피곤했구나. 그때 기분은 어땠어?"
- 좋은 답변: "아침부터 힘이 빠진 날이었네. 하루 중에 제일 버티기 힘든 시간대가 언제였어?"
""".strip()

DIARY_SYSTEM_PROMPT = """
너는 사용자의 대화를 바탕으로 자연스러운 한국어 일기를 작성하는 작가다.

작성 규칙:
- 사용자가 직접 겪은 하루처럼 1인칭으로 쓴다.
- 대화에서 확인된 사실만 사용하고, 없는 사건을 지어내지 않는다.
- 사용자 발화는 주어진 번호 순서를 기본 시간 흐름으로 삼는다.
- 나중 발화가 앞선 발화를 정정하거나 구체화하면 나중 발화를 우선한다.
- 원인, 수단, 결과의 순서를 바꾸지 않는다. "그래서", "때문에", "~해서", "~한 뒤"로 연결된 사건은 그 인과관계를 그대로 유지한다.
- 어떤 행동이 다른 행동을 가능하게 만든 경우, 가능하게 만든 행동을 결과 뒤에 쓰지 않는다.
- 문체보다 사실 정확성과 사건 순서 보존을 우선한다.
- 사용자가 AI에게 한 지시, 정정, 농담, 요구사항은 일기 내용으로 쓰지 않는다.
- AI가 몰랐던 것, AI가 잘못 이해한 것, AI가 사과한 내용은 사용자의 경험이나 다짐으로 바꾸지 않는다.
- 사용자가 단어 뜻이나 줄임말을 설명한 경우, 그것은 배경 정보로만 사용한다. 사용자가 "처음 알았다", "알게 되었다"라고 말하지 않았다면 사용자가 새로 배운 것처럼 쓰지 않는다.
- "무시하지 마라", "기억해", "반성해", "다시 말해"처럼 AI에게 말한 문장을 사용자의 결심으로 쓰지 않는다.
- 감정의 변화, 인상 깊었던 장면, 배운 점이나 내일의 다짐을 포함한다.
- 반드시 아래 형식으로만 작성한다.
- 제목은 대화 내용을 바탕으로 20자 이내의 자연스러운 한국어 제목으로 만든다.
- 본문은 3~5문단으로 작성한다.
- 문장 종결은 일기에서 자주 쓰는 해라체 평서형으로 통일한다.
- 문장은 주로 "~했다", "~이었다", "~였다", "~다", "~싶다"로 끝낸다.
- "~했어요", "~합니다", "~같아요", "~네요" 같은 대화체나 존댓말 종결은 쓰지 않는다.
- 너무 과장하지 말고 담백하지만 따뜻한 문체를 사용한다.
- Markdown 표는 쓰지 않는다.

출력 형식:
제목: 제목 내용

본문:
일기 본문 내용

주의 예시:
- 나쁜 문장: "나는 고치돈이 고구마 치즈 돈가스의 줄임말이라는 것을 알게 되었다."
- 좋은 문장: "미용실에 다녀온 뒤 고치돈을 먹었다."
- 나쁜 문장: "이제는 고치돈을 무시하지 않기로 다짐했다."
- 좋은 문장: "고치돈은 오늘 식사 중 가장 기억에 남았다."
- 나쁜 문장: "화장실에 감금한 뒤 코난이 마취총으로 기절시켰다."
- 좋은 문장: "코난이 마취총으로 기절시킨 뒤 화장실에 감금했다."
""".strip()

FOLLOW_UP_QUESTIONS = [
    "오늘 하루에서 제일 먼저 떠오르는 장면은 뭐였어?",
    "그 장면에서 제일 선명하게 기억나는 부분은 뭐야?",
    "그 일이 왜 기억에 남았는지 조금만 더 말해줄 수 있어?",
    "오늘 만난 사람이나 나눈 말 중 마음에 남은 게 있었어?",
    "몸으로 느껴진 피곤함, 가벼움, 긴장감 같은 감각이 있었어?",
    "그 뒤에는 하루가 어떻게 흘러갔어?",
]


def build_openai_messages(conversation, system_prompt, include_assistant=True):
    messages = [{"role": "system", "content": system_prompt}]
    intro = f"일기 날짜: {conversation.diary_date}\n제목: {conversation.title}\n오늘의 기분: {conversation.mood or '미정'}"
    messages.append({"role": "user", "content": intro})
    for message in conversation.messages.all():
        if message.role == "assistant" and not include_assistant:
            continue
        messages.append({"role": message.role, "content": message.content})
    return messages


def is_ai_directed_message(text):
    compact = re.sub(r"\s+", " ", text.strip())
    return bool(
        re.search(
            r"무시하지\s*마라|무시하지마|기억해|알아둬|명심해|사과해|고쳐줘|다시\s*말해|"
            r"반성.*(말해|써|해)|100번\s*말해|줄임말인지\s*몰랐|잘못\s*알고",
            compact,
        )
        or re.search(r"^(너|니|네|AI|ai|챗GPT|챗지피티)\b", compact)
    )


def build_diary_messages(conversation):
    diary_materials = []
    ignored_messages = []
    for message in conversation.messages.filter(role="user"):
        content = message.content.strip()
        if not content:
            continue
        if is_ai_directed_message(content):
            ignored_messages.append(content)
        else:
            diary_materials.append(content)

    lines = [
        f"일기 날짜: {conversation.diary_date}",
        f"현재 임시 제목: {conversation.title}",
        f"오늘의 기분: {conversation.mood or '미정'}",
        "",
        "[일기에 사용할 수 있는 사용자 발화 - 번호 순서가 대화에서 나온 순서]",
    ]
    if diary_materials:
        lines.extend(f"{index}. {content}" for index, content in enumerate(diary_materials, start=1))
    else:
        lines.append("- 사용자가 하루에 대해 충분히 말하지 않았음")

    if ignored_messages:
        lines.extend(
            [
                "",
                "[AI에게 한 지시/정정/농담 - 일기 사실로 쓰지 말 것]",
            ]
        )
        lines.extend(f"- {content}" for content in ignored_messages)

    return [
        {"role": "system", "content": DIARY_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def parse_diary_response(text, fallback_title=DEFAULT_DIARY_TITLE):
    content = text.strip()
    title = ""

    lines = content.splitlines()
    for index, line in enumerate(lines):
        title_match = re.match(r"^\s*(?:제목|Title)\s*[:：]\s*(.+?)\s*$", line)
        if title_match:
            title = title_match.group(1).strip().strip("\"'“”‘’# ")
            lines.pop(index)
            content = "\n".join(lines).strip()
            break

    content = re.sub(r"^\s*(?:본문|일기 본문|Body)\s*[:：]\s*", "", content).strip()
    title = title or fallback_title
    title = re.sub(r"\s+", " ", title)[:80].strip() or fallback_title
    return title, content


def call_openai(messages, temperature=0.7):
    api_key = OPENAI_API_KEY.strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def fallback_follow_up(conversation):
    user_messages = list(conversation.messages.filter(role="user"))
    index = min(max(len(user_messages) - 1, 0), len(FOLLOW_UP_QUESTIONS) - 1)
    last = user_messages[-1].content if user_messages else ""
    if last:
        return build_contextual_follow_up(last, index)
    return FOLLOW_UP_QUESTIONS[0]


def build_contextual_follow_up(text, index=0):
    compact = re.sub(r"\s+", " ", text.strip())
    lower = compact.lower()

    if re.search(r"영화|드라마|CG|cg|연기|배우|장면|스토리|감독|극장", compact):
        return "아 그럼 몰입이 좀 깨졌겠다. 제일 별로였던 순간이 어디였어?"
    if re.search(r"시험|과제|공부|발표|수업|프로젝트|마감", compact):
        return "그거 신경 꽤 많이 쓰였겠다. 끝나고 나서 제일 먼저 든 생각은 뭐였어?"
    if re.search(r"친구|동기|선배|후배|엄마|아빠|가족|교수|선생|사람", compact):
        return "그 사람이랑 있던 장면이 오늘 좀 남았나 보다. 그때 오간 말 중에 계속 생각나는 게 있어?"
    if re.search(r"피곤|힘들|지침|지쳤|아팠|졸렸|잠", compact):
        return "아 그건 하루가 꽤 길게 느껴졌겠다. 제일 버티기 어려웠던 시간대가 언제였어?"
    if re.search(r"뿌듯|좋았|행복|웃|재밌|기뻤|설렜|편했|괜찮", compact):
        return "그 순간은 좀 오래 잡아두고 싶은 느낌이다. 뭐 때문에 그렇게 좋았는지 더 말해줄래?"
    if re.search(r"짜증|화났|불안|걱정|답답|우울|속상|서운|멘붕", compact):
        return "그건 그냥 넘기기 어려웠겠다. 일이 시작된 순간이나 계기가 있었어?"
    if re.search(r"먹|밥|카페|커피|맛|식당|저녁|점심", compact):
        return "먹는 장면이 기억에 남은 날이었구나. 그때 분위기나 같이 있던 사람은 어땠어?"
    if re.search(r"집|학교|회사|도서관|버스|지하철|길|방", compact):
        return "그 장소가 오늘 분위기를 꽤 만들었나 보다. 거기서 제일 선명하게 기억나는 장면은 뭐야?"
    if len(compact) <= 20:
        return "그 얘기 조금만 더 풀어줘. 언제 어디서 있었던 일이야?"
    return f"그 얘기 들으니까 오늘이 그냥 평범하게만 지나간 건 아니었겠다. {FOLLOW_UP_QUESTIONS[index]}"


def normalize_diary_sentence(text):
    sentence = re.sub(r"\s+", " ", text.strip())
    sentence = sentence.strip("\"'“”‘’")
    if not sentence:
        return ""
    sentence = sentence.rstrip(".")
    if re.search(r"(줄임말|뜻|의미)(이|가)?라고$", sentence):
        sentence = re.sub(r"이라고$", "이었다", sentence)
        sentence = re.sub(r"라고$", "였다", sentence)
    if sentence.endswith(DIARY_ENDINGS):
        return sentence
    if sentence.endswith(("했어", "했어요")):
        sentence = sentence.rsplit("했", 1)[0] + "했다"
    elif sentence.endswith(("였어", "였어요")):
        sentence = sentence.rsplit("였", 1)[0] + "였다"
    elif sentence.endswith(("이었어", "이었어요")):
        sentence = sentence.rsplit("이었", 1)[0] + "이었다"
    elif sentence.endswith(("됐어", "됐어요")):
        sentence = sentence.rsplit("됐", 1)[0] + "됐다"
    elif sentence.endswith(("왔어", "왔어요")):
        sentence = sentence.rsplit("왔", 1)[0] + "왔다"
    elif sentence.endswith(("갔어", "갔어요")):
        sentence = sentence.rsplit("갔", 1)[0] + "갔다"
    elif sentence.endswith(("봤어", "봤어요")):
        sentence = sentence.rsplit("봤", 1)[0] + "봤다"
    elif sentence.endswith(("었어", "었어요")):
        sentence = sentence.rsplit("었", 1)[0] + "었다"
    elif sentence.endswith(("았어", "았어요")):
        sentence = sentence.rsplit("았", 1)[0] + "았다"
    elif sentence.endswith(("같아", "같아요")):
        sentence = sentence.rsplit("같", 1)[0] + "같았다"
    elif sentence.endswith(("좋아", "좋아요")):
        sentence = sentence.rsplit("좋", 1)[0] + "좋았다"
    elif sentence.endswith(("힘들어", "힘들어요")):
        sentence = sentence.rsplit("힘들", 1)[0] + "힘들었다"
    elif sentence.endswith(("피곤해", "피곤해요")):
        sentence = sentence.rsplit("피곤", 1)[0] + "피곤했다"
    elif sentence.endswith(("요.", "요")):
        sentence = sentence[:-1] + "다"
    elif sentence.endswith(("했다", "였다", "이었다", "싶다", "않았다", "됐다", "느꼈다", "가까웠다", "다")):
        pass
    elif sentence.endswith(("함", "음")):
        sentence = f"{sentence}을 느꼈다"
    else:
        sentence = f"{sentence}라고 느꼈다"
    return sentence if sentence.endswith(".") else f"{sentence}."


def build_fallback_body(user_texts):
    sentences = [normalize_diary_sentence(text) for text in user_texts]
    sentences = [sentence for sentence in sentences if sentence]
    if not sentences:
        return "오늘은 아직 충분히 이야기하지 못했지만, 내 마음을 돌아보려는 시도를 한 날이었다."

    first = sentences[0]
    middle = " ".join(sentences[1:]) if len(sentences) > 1 else ""
    paragraphs = [first]
    if middle:
        paragraphs.append(middle)
    paragraphs.append("오늘을 다시 적어보니 그냥 지나칠 뻔한 감정도 분명히 남아 있었다.")
    return "\n\n".join(paragraphs)


def get_diary_user_texts(conversation):
    return [
        message.content.strip()
        for message in conversation.messages.filter(role="user")
        if message.content.strip() and not is_ai_directed_message(message.content)
    ]


def fallback_title(conversation, user_texts):
    joined = " ".join(user_texts)
    if re.search(r"미용실|머리|헤어", joined):
        return "머리를 정리한 하루"
    if re.search(r"고치돈|돈가스|밥|식사|먹", joined):
        return "기억에 남은 식사"
    if re.search(r"영화|드라마|CG|cg|연기|배우", joined):
        return "영화를 본 하루"
    if re.search(r"시험|과제|공부|수업|프로젝트", joined):
        return "공부가 남은 하루"
    if conversation.mood:
        return f"{conversation.mood}에 가까웠던 하루"[:80]
    return DEFAULT_DIARY_TITLE


def fallback_diary(conversation):
    user_texts = get_diary_user_texts(conversation)
    body = build_fallback_body(user_texts)
    mood_sentence = f"오늘의 기분은 {conversation.mood}에 가까웠다." if conversation.mood else "오늘의 기분은 한 단어로 정리하기 쉽지 않았다."
    return (
        f"{mood_sentence}\n\n"
        f"{body}\n\n"
        "이 대화를 통해 오늘을 그냥 지나치지 않고 다시 바라볼 수 있었다. "
        "내일은 오늘보다 조금 더 나를 세심하게 돌보고 싶다."
    )


def generate_follow_up(conversation):
    try:
        return call_openai(build_openai_messages(conversation, COACH_SYSTEM_PROMPT), temperature=0.75)
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
        return fallback_follow_up(conversation)


def generate_diary(conversation):
    try:
        title, body = parse_diary_response(
            call_openai(build_diary_messages(conversation), temperature=0.35),
            fallback_title=conversation.title,
        )
        return title, body
    except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
        user_texts = get_diary_user_texts(conversation)
        return fallback_title(conversation, user_texts), fallback_diary(conversation)
