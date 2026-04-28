document.addEventListener("DOMContentLoaded", () => {
    const scrollChatToBottom = () => {
        const chatList = document.querySelector(".chat-list");
        if (chatList) {
            chatList.scrollTop = chatList.scrollHeight;
        }
    };

    const renderChatText = (element, text) => {
        element.textContent = "";
        text.split("\n").forEach((line, index) => {
            if (index > 0) {
                element.appendChild(document.createElement("br"));
            }
            element.appendChild(document.createTextNode(line));
        });
    };

    const appendChatMessage = (role, content, extraClass = "") => {
        const chatList = document.querySelector(".chat-list");
        if (!chatList) {
            return null;
        }

        const article = document.createElement("article");
        article.className = `chat-message ${role} ${extraClass}`.trim();

        const label = document.createElement("span");
        label.textContent = role === "user" ? "나" : "오늘 하루";

        const body = document.createElement("p");
        renderChatText(body, content);

        article.append(label, body);
        chatList.appendChild(article);
        scrollChatToBottom();
        return article;
    };

    const setDiaryResult = (content, isLoading = false) => {
        const result = document.querySelector(".diary-result");
        if (!result) {
            return;
        }
        const editToggle = document.querySelector(".diary-edit-toggle");
        const editForm = document.querySelector(".diary-edit-form");
        const editor = editForm?.querySelector("textarea");

        result.textContent = "";
        result.hidden = false;
        if (editForm) {
            editForm.hidden = true;
        }
        if (isLoading) {
            if (editToggle) {
                editToggle.hidden = true;
            }
            const loading = document.createElement("div");
            loading.className = "empty-state diary-loading";
            const title = document.createElement("h3");
            title.textContent = "일기 작성 중...";
            const body = document.createElement("p");
            body.textContent = "대화 내용을 바탕으로 오늘의 일기를 정리하고 있습니다.";
            loading.append(title, body);
            result.appendChild(loading);
            return;
        }

        const paper = document.createElement("div");
        paper.className = "diary-paper";
        renderChatText(paper, content);
        result.appendChild(paper);
        if (editor) {
            editor.value = content;
            resetTextareaHeight(editor);
        }
        if (editToggle) {
            editToggle.hidden = false;
        }
    };

    const setConversationTitle = (title) => {
        if (!title) {
            return;
        }
        const heading = document.querySelector(".conversation-title");
        if (heading) {
            heading.textContent = title;
        }
        document.title = `오늘 하루 - ${title}`;
    };

    const setConversationDate = (dateValue) => {
        if (!dateValue) {
            return;
        }
        const dateLabel = document.querySelector(".conversation-date");
        if (dateLabel) {
            dateLabel.textContent = dateValue;
        }
        const dateInput = document.querySelector(".diary-edit-form input[name='diary_date']");
        if (dateInput) {
            dateInput.value = dateValue;
        }
    };

    const resetTextareaHeight = (textarea) => {
        textarea.style.height = "auto";
        textarea.style.height = `${textarea.scrollHeight + 2}px`;
    };

    const decrementNumber = (element) => {
        if (!element) {
            return;
        }
        const current = Number.parseInt(element.textContent.trim(), 10);
        if (Number.isNaN(current)) {
            return;
        }
        element.textContent = Math.max(current - 1, 0).toString();
    };

    const showFlashMessage = (text) => {
        const main = document.querySelector(".page-shell");
        if (!main) {
            return;
        }
        let messages = main.querySelector(".messages");
        if (!messages) {
            messages = document.createElement("section");
            messages.className = "messages";
            main.prepend(messages);
        }
        messages.textContent = "";
        const message = document.createElement("div");
        message.className = "message success";
        message.textContent = text;
        messages.appendChild(message);
        window.setTimeout(() => {
            message.remove();
            if (!messages.children.length) {
                messages.remove();
            }
        }, 2500);
    };

    const updateCalendarAfterDelete = (dateValue) => {
        const summaryCount = document.querySelector("[data-calendar-total] strong");
        decrementNumber(summaryCount);

        const day = document.querySelector(`.calendar-day[data-date="${dateValue}"]`);
        if (!day) {
            return;
        }
        const current = Number.parseInt(day.dataset.count || "0", 10);
        const next = Math.max(current - 1, 0);
        day.dataset.count = next.toString();
        const label = day.querySelector("span");
        if (next > 0) {
            if (label) {
                label.textContent = `일기 ${next}개`;
            }
            return;
        }
        day.classList.remove("written");
        label?.remove();
    };

    const removeConversationCards = (conversationId) => {
        document.querySelectorAll(`[data-conversation-id="${conversationId}"]`).forEach((item) => {
            item.remove();
        });
    };

    const statusLabels = {
        writing: "작성중인 일기",
        finished: "작성된 일기",
    };

    const setStatusPanel = (status, options = {}) => {
        const panel = document.querySelector("#diaryStatusList");
        if (!panel || !statusLabels[status]) {
            return;
        }

        panel.hidden = false;
        const title = panel.querySelector("[data-status-title]");
        if (title) {
            title.textContent = `${statusLabels[status]} 목록`;
        }

        document.querySelectorAll("[data-status-panel]").forEach((section) => {
            section.hidden = section.dataset.statusPanel !== status;
        });
        document.querySelectorAll(".stat-link[data-stat]").forEach((link) => {
            link.classList.toggle("active", link.dataset.stat === status);
        });

        if (options.push) {
            const url = new URL(window.location.href);
            url.searchParams.set("status", status);
            url.hash = "diaryStatusList";
            window.history.pushState({ status }, "", url);
        }
        if (options.scroll) {
            const topbarHeight = document.querySelector(".topbar")?.getBoundingClientRect().height || 72;
            const targetTop = panel.getBoundingClientRect().top + window.scrollY - topbarHeight - 18;
            window.scrollTo({
                top: Math.max(targetTop, 0),
                behavior: "smooth",
            });
        }
    };

    const hideStatusPanel = () => {
        const panel = document.querySelector("#diaryStatusList");
        if (panel) {
            panel.hidden = true;
        }
        document.querySelectorAll(".stat-link[data-stat]").forEach((link) => {
            link.classList.remove("active");
        });
    };

    const scrollToPanel = (element) => {
        if (!element) {
            return;
        }
        const topbarHeight = document.querySelector(".topbar")?.getBoundingClientRect().height || 72;
        const targetTop = element.getBoundingClientRect().top + window.scrollY - topbarHeight - 18;
        window.scrollTo({
            top: Math.max(targetTop, 0),
            behavior: "smooth",
        });
    };

    const replaceCalendarArea = (html, url, options = {}) => {
        const parser = new DOMParser();
        const nextDocument = parser.parseFromString(html, "text/html");
        const currentArea = document.querySelector("#calendarArea");
        const nextArea = nextDocument.querySelector("#calendarArea");
        if (!currentArea || !nextArea) {
            return false;
        }

        currentArea.replaceWith(nextArea);
        if (options.push) {
            window.history.pushState({ calendar: true }, "", url);
        }
        if (options.scrollToCalendar) {
            scrollToPanel(document.querySelector("#calendarArea"));
        }
        return true;
    };

    const loadCalendarArea = async (url, options = {}) => {
        const response = await fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        if (!response.ok) {
            throw new Error("calendar load failed");
        }
        const html = await response.text();
        if (!replaceCalendarArea(html, url, options)) {
            throw new Error("calendar area missing");
        }
    };

    document.addEventListener("click", async (event) => {
        const link = event.target.closest("#calendarArea .calendar-nav a, #calendarArea .calendar-day");
        if (!link || link.classList.contains("blank")) {
            return;
        }

        event.preventDefault();
        const url = new URL(link.getAttribute("href"), window.location.href);
        const shouldScroll = link.classList.contains("calendar-day");
        try {
            await loadCalendarArea(url, { push: true, scrollToCalendar: shouldScroll });
        } catch (error) {
            window.location.href = url.href;
        }
    });

    const search = document.querySelector("#sessionSearch");
    const list = document.querySelector("#sessionList");
    if (search && list) {
        search.addEventListener("input", () => {
            const keyword = search.value.trim().toLowerCase();
            list.querySelectorAll("[data-session-text]").forEach((item) => {
                const text = item.dataset.sessionText.toLowerCase();
                item.hidden = keyword !== "" && !text.includes(keyword);
            });
        });
    }

    document.querySelectorAll(".stat-link[data-stat]").forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            setStatusPanel(link.dataset.stat, { push: true, scroll: true });
        });
    });

    window.addEventListener("popstate", () => {
        const status = new URL(window.location.href).searchParams.get("status");
        if (statusLabels[status]) {
            setStatusPanel(status, { push: false, scroll: false });
        } else {
            hideStatusPanel();
        }
        if (document.querySelector("#calendarArea")) {
            loadCalendarArea(window.location.href, {
                push: false,
                scrollToCalendar: window.location.hash === "#selectedDateDiaries",
            }).catch(() => {});
        }
    });

    document.querySelectorAll("textarea").forEach((textarea) => {
        const resize = () => resetTextareaHeight(textarea);
        textarea.addEventListener("input", resize);
        resize();
    });

    document.querySelectorAll(".chat-form textarea").forEach((textarea) => {
        textarea.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" || event.shiftKey || event.isComposing) {
                return;
            }
            event.preventDefault();
            const form = textarea.closest("form");
            const submitter = form?.querySelector("button[name='action'][value='send']");
            if (form && submitter) {
                form.requestSubmit(submitter);
            }
        });
    });

    document.querySelectorAll(".chat-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const textarea = form.querySelector("textarea");
            const submitter = form.querySelector("button[name='action'][value='send']");
            const content = textarea?.value.trim();
            if (!textarea || !content) {
                return;
            }

            appendChatMessage("user", content);
            const pendingMessage = appendChatMessage("assistant", "답장 쓰는 중...", "pending");
            textarea.value = "";
            resetTextareaHeight(textarea);
            if (submitter) {
                submitter.disabled = true;
            }

            const formData = new FormData(form);
            formData.set("content", content);
            formData.set("action", "send");

            try {
                const requestUrl = form.getAttribute("action") || window.location.href;
                const response = await fetch(requestUrl, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (!response.ok) {
                    throw new Error("message send failed");
                }

                const data = await response.json();
                const pendingBody = pendingMessage?.querySelector("p");
                if (pendingMessage && pendingBody && data.assistant?.content) {
                    pendingMessage.classList.remove("pending");
                    renderChatText(pendingBody, data.assistant.content);
                }
            } catch (error) {
                const pendingBody = pendingMessage?.querySelector("p");
                if (pendingMessage && pendingBody) {
                    pendingMessage.classList.remove("pending");
                    renderChatText(pendingBody, "전송이 잘 안 됐어. 잠시 후 다시 보내줘.");
                }
            } finally {
                if (submitter) {
                    submitter.disabled = false;
                }
                textarea.focus();
                scrollChatToBottom();
            }
        });
    });

    document.querySelectorAll(".diary-generate-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const submitter = form.querySelector("button[name='action'][value='generate']");
            if (submitter) {
                submitter.disabled = true;
                submitter.textContent = "작성 중...";
            }
            setDiaryResult("", true);

            const formData = new FormData(form);
            formData.set("action", "generate");

            try {
                const requestUrl = form.getAttribute("action") || window.location.href;
                const response = await fetch(requestUrl, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (!response.ok) {
                    throw new Error("diary generation failed");
                }

                const data = await response.json();
                if (data.final_diary) {
                    setDiaryResult(data.final_diary);
                }
                if (data.title) {
                    setConversationTitle(data.title);
                }
            } catch (error) {
                const result = document.querySelector(".diary-result");
                if (result) {
                    result.innerHTML = (
                        '<div class="empty-state">' +
                        "<h3>일기 생성에 실패했습니다.</h3>" +
                        "<p>잠시 후 다시 눌러주세요.</p>" +
                        "</div>"
                    );
                }
            } finally {
                if (submitter) {
                    submitter.disabled = false;
                    submitter.textContent = "일기 생성";
                }
            }
        });
    });

    document.querySelectorAll(".diary-edit-toggle").forEach((button) => {
        button.addEventListener("click", () => {
            const result = document.querySelector(".diary-result");
            const form = document.querySelector(".diary-edit-form");
            const textarea = form?.querySelector("textarea");
            if (!result || !form || !textarea) {
                return;
            }

            result.hidden = true;
            form.hidden = false;
            button.hidden = true;
            resetTextareaHeight(textarea);
            textarea.focus();
        });
    });

    document.querySelectorAll(".diary-edit-cancel").forEach((button) => {
        button.addEventListener("click", () => {
            const result = document.querySelector(".diary-result");
            const form = button.closest(".diary-edit-form");
            const toggle = document.querySelector(".diary-edit-toggle");
            if (result) {
                result.hidden = false;
            }
            if (form) {
                form.hidden = true;
            }
            if (toggle) {
                toggle.hidden = false;
            }
        });
    });

    document.querySelectorAll(".diary-edit-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const textarea = form.querySelector("textarea");
            const dateInput = form.querySelector("input[name='diary_date']");
            const submitter = form.querySelector("button[name='action'][value='update_diary']");
            const content = textarea?.value.trim();
            const diaryDate = dateInput?.value.trim();
            if (!textarea || !content) {
                textarea?.focus();
                return;
            }
            if (!dateInput || !diaryDate) {
                dateInput?.focus();
                return;
            }

            if (submitter) {
                submitter.disabled = true;
                submitter.textContent = "저장 중...";
            }

            const formData = new FormData(form);
            formData.set("final_diary", content);
            formData.set("diary_date", diaryDate);
            formData.set("action", "update_diary");

            try {
                const requestUrl = form.getAttribute("action") || window.location.href;
                const response = await fetch(requestUrl, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (!response.ok) {
                    throw new Error("diary update failed");
                }

                const data = await response.json();
                if (data.final_diary) {
                    setDiaryResult(data.final_diary);
                }
                if (data.diary_date) {
                    setConversationDate(data.diary_date);
                }
            } catch (error) {
                textarea.focus();
            } finally {
                if (submitter) {
                    submitter.disabled = false;
                    submitter.textContent = "저장";
                }
            }
        });
    });

    document.querySelectorAll(".delete-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const title = form.dataset.title || "이 하루 대화";
            const confirmed = window.confirm(`"${title}"을 삭제할까요?\n대화와 생성된 일기가 함께 삭제됩니다.`);
            if (!confirmed) {
                return;
            }

            const submitter = form.querySelector("button[type='submit']");
            if (submitter) {
                submitter.disabled = true;
                submitter.textContent = "삭제 중...";
            }

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                if (!response.ok) {
                    throw new Error("delete failed");
                }
                const data = await response.json();
                removeConversationCards(data.id);
                const statKey = data.is_finished ? "finished" : "writing";
                decrementNumber(document.querySelector(`[data-stat="${statKey}"] strong`));
                if (data.is_finished) {
                    updateCalendarAfterDelete(data.diary_date);
                }
                showFlashMessage("하루 대화를 삭제했습니다.");
            } catch (error) {
                if (submitter) {
                    submitter.disabled = false;
                    submitter.textContent = "삭제";
                }
                window.alert("삭제에 실패했습니다. 잠시 후 다시 시도해주세요.");
            }
        });
    });

    requestAnimationFrame(scrollChatToBottom);
});
