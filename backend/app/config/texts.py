"""Bot message templates."""


class Texts:
    """All bot message texts in Russian."""
    
    # === Welcome & Identification ===
    WELCOME = (
        "Привет! Я бот поддержки. Я аккуратно соберу детали и передам "
        "задачу команде — ничего не потеряется.\n\n"
        "Выберите, что случилось:"
    )
    
    WELCOME_PERSONAL = (
        "Привет, {name}! 👋\n\n"
        "Рады видеть вас снова. Чем можем помочь сегодня?"
    )
    
    WELCOME_BACK = "С возвращением! Выберите, что случилось:"
    
    WELCOME_BACK_PERSONAL = (
        "С возвращением, {name}! 👋\n\n"
        "Чем можем помочь сегодня?"
    )
    
    NO_CODE_PROMPT = (
        "Привет! Чтобы я направил запрос правильно, нужен код проекта.\n\n"
        "Если кода нет — нажмите «Нет кода», мы разберёмся."
    )
    
    INVALID_CODE = (
        "Код не найден. Проверьте и попробуйте ещё раз, "
        "или нажмите «Нет кода»."
    )
    
    CODE_ACCEPTED = "Отлично, код принят! Вы привязаны к проекту: {project_name}\n\nВыберите, что случилось:"
    
    # === Triage ===
    TRIAGE_ASK_COMPANY = "Укажите, пожалуйста, название компании или проекта, с которым работаете:"
    
    TRIAGE_ASK_CONTACT = (
        "Оставьте контакт для связи (email или телефон).\n\n"
        "Можно пропустить — напишем сюда."
    )
    
    TRIAGE_DONE = "Спасибо! Мы получили вашу заявку и свяжемся в ближайшее время."
    
    # === Ticket Creation ===
    ASK_DESCRIPTION = "Опишите проблему подробнее — что произошло и что должно было работать:"
    
    # Custom prompts per category
    ASK_DESCRIPTION_REPORT = (
        "📊 Что-то сломалось в отчёте? Расскажите скорее!\n\n"
        "Какой отчёт, что не так, ссылка — и мы разберёмся 💪"
    )
    
    ASK_DESCRIPTION_RATING = (
        "⭐ Некорректная оценка? Давайте скорее исправим!\n\n"
        "Дайте детали: сотрудник, ссылка на сделку, дата звонка"
    )
    
    ASK_DESCRIPTION_WIDGET = (
        "🔗 Что-то сломалось в виджете? Интеграция барахлит?\n\n"
        "Давайте скорее починим! Расскажите, что случилось 🔧"
    )
    
    ASK_DESCRIPTION_ACCESS = (
        "🔐 Нужны доступы? Давайте скорее предоставим!\n\n"
        "Кому, куда и какая роль — и работа не будет простаивать 🚀"
    )
    
    ASK_DESCRIPTION_HOWTO = (
        "💡 Нужно что-то донастроить? Без проблем!\n\n"
        "Расскажите, что хотите сделать — вместе разберёмся ✨"
    )
    
    ASK_DESCRIPTION_BILLING = (
        "💳 Нужен счёт, акт или договор? А может, реквизиты?\n\n"
        "Давайте скорее всё направим! Что именно нужно? 📄"
    )
    
    ASK_DESCRIPTION_FEATURE = (
        "🌟 У вас есть идея, как нам стать лучше? Супер!\n\n"
        "Скорее поделитесь — мы внимательно читаем все предложения 💡"
    )
    
    ASK_DESCRIPTION_OTHER = (
        "📝 Расскажите, что случилось — вместе разберёмся!\n\n"
        "Чем подробнее опишете, тем быстрее поможем 🤝"
    )
    
    ASK_ATTACHMENTS = (
        "Можно прикрепить скриншот, видео или файл — это поможет быстрее разобраться.\n\n"
        "Или нажмите «Пропустить»."
    )
    
    ATTACHMENTS_MORE = "Файл получен. Ещё что-то? Или нажмите «Готово»."
    
    TICKET_CREATED = (
        "✅ Готово, обращение #{number} принято!\n\n"
        "⏰ Рабочие часы: Пн–Пт 10:00–19:00 CET / 10:00–19:00 МСК\n"
        "📬 {sla_message}"
    )
    
    TICKET_CREATED_OFF_HOURS = (
        "✅ Обращение #{number} принято!\n\n"
        "⏰ Сейчас нерабочее время. Ответим в следующий рабочий день.\n"
        "🕐 Рабочие часы: Пн–Пт 10:00–19:00 CET / 10:00–19:00 МСК"
    )
    
    # SLA messages by category
    SLA_FEATURE = "Спасибо за ваши идеи! Мы их обязательно рассмотрим."
    SLA_OTHER = "Вернёмся к вам с деталями по запросу."
    SLA_DEFAULT = "Среднее время решения: {time}"
    
    # === Urgent Flow ===
    URGENT_ASK_BLOCKING = "Насколько это блокирует работу?"
    
    URGENT_ASK_DETAILS = "Что именно не работает? Опишите кратко:"
    
    # === Active Ticket ===
    MESSAGE_FORWARDED = "Сообщение передано команде поддержки."
    
    ACTIVE_TICKET_EXISTS = "У вас есть открытое обращение #{number}. Ваше сообщение добавлено к нему."
    
    # === After Close ===
    REOPEN_OR_NEW = (
        "Обращение #{number} было закрыто недавно.\n\n"
        "Хотите продолжить его или создать новое?"
    )
    
    TICKET_REOPENED = "Обращение #{number} открыто заново. Мы получили ваше сообщение."
    
    # === Notifications (Bright & Visible with HTML formatting) ===
    TICKET_IN_PROGRESS = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 <b>ВЗЯТО В РАБОТУ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 Обращение <b>#{number}</b>\n"
        "📊 Статус: <b>🔄 В работе</b>\n\n"
        "Ваш запрос взят в работу!\n"
        "Скоро вернёмся с ответом."
    )
    
    TICKET_PAUSED = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏸️ <b>НА ПАУЗЕ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 Обращение <b>#{number}</b>\n"
        "📊 Статус: <b>⏸️ На паузе</b>\n\n"
        "Работа над вашим запросом\n"
        "временно приостановлена.\n"
        "Вернёмся к нему в ближайшее время."
    )
    
    TICKET_PAUSED_WITH_REASON = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏸️ <b>НА ПАУЗЕ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 Обращение <b>#{number}</b>\n"
        "📊 Статус: <b>⏸️ На паузе</b>\n\n"
        "💬 <i>Причина:</i>\n{reason}\n\n"
        "Вернёмся к вашему запросу\n"
        "в ближайшее время."
    )
    
    TICKET_RESUMED = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▶️ <b>ВОЗОБНОВЛЕНО</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 Обращение <b>#{number}</b>\n"
        "📊 Статус: <b>🔄 В работе</b>\n\n"
        "Работа над вашим запросом\n"
        "возобновлена!"
    )
    
    TICKET_CLOSED = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎉 <b>УРА! ОБРАЩЕНИЕ РЕШЕНО!</b> 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 Обращение <b>#{number}</b>\n"
        "📊 Статус: <b>✅ Выполнено</b>\n\n"
        "Ваш запрос успешно закрыт!\n"
        "Спасибо, что обратились к нам 💙"
    )
    
    TICKET_CLOSED_WHATS_NEXT = "Что делаем дальше?"
    
    TICKET_CANCELLED = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "❌ <b>ОБРАЩЕНИЕ ОТМЕНЕНО</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 Обращение <b>#{number}</b>\n"
        "📊 Статус: <b>❌ Отменено</b>\n\n"
        "💬 <i>Причина:</i>\n{reason}\n\n"
        "Если есть вопросы —\n"
        "создайте новое обращение."
    )
    
    OPERATOR_REPLY = "Ответ поддержки:\n\n{message}"
    
    # === Client self-cancel ===
    CLIENT_CANCEL_CONFIRM = (
        "Вы уверены, что хотите отменить обращение #{number}?\n\n"
        "Это действие нельзя отменить."
    )
    
    CLIENT_CANCEL_SUCCESS = (
        "✅ Обращение #{number} отменено.\n\n"
        "Если вопрос снова станет актуальным — создайте новый запрос!"
    )
    
    CLIENT_CANCEL_NOT_ALLOWED = (
        "❌ Это обращение уже взято в работу оператором.\n\n"
        "Если вопрос больше неактуален — напишите об этом, и мы закроем его."
    )
    
    REQUEST_DETAILS = (
        "Нужно чуть больше деталей, чтобы быстрее помочь:\n\n"
        "1. Что вы делали перед проблемой?\n"
        "2. Ссылка на раздел/страницу\n"
        "3. Скриншот или видео (если возможно)"
    )
    
    # === CSAT ===
    CSAT_ASK = "Оцените, пожалуйста, как мы помогли:"
    
    CSAT_THANKS_POSITIVE = "Спасибо за оценку! Рады, что помогли! 🎉🙌"
    
    CSAT_ASK_COMMENT = "Жаль, что не помогли как надо. Что было не так?"
    
    CSAT_THANKS_NEGATIVE = "Спасибо за обратную связь. Учтём это!"
    
    # Detailed CSAT
    CSAT_ASK_DETAILED = (
        "🙏 Помогите нам стать лучше!\n\n"
        "Оцените нашу работу по трём параметрам:"
    )
    
    CSAT_ASK_SPEED = "⚡ <b>Скорость ответа:</b>\nКак быстро мы отреагировали?"
    CSAT_ASK_QUALITY = "✨ <b>Качество решения:</b>\nНасколько полезным был ответ?"
    CSAT_ASK_POLITENESS = "💬 <b>Вежливость:</b>\nКак вам наше общение?"
    
    CSAT_DETAILED_THANKS = (
        "🙏 Большое спасибо за детальную оценку!\n\n"
        "Ваш отзыв помогает нам становиться лучше 💜"
    )
    
    # === /project ===
    PROJECT_LIST = "Ваши проекты:"
    
    PROJECT_SWITCHED = "Переключено на проект: {project_name}"
    
    PROJECT_SINGLE = "Вы привязаны к проекту: {project_name}"
    
    # === /help ===
    HELP_TEXT = (
        "🤖 Бот поддержки\n\n"
        "Доступные команды:\n"
        "/start — начать или выбрать категорию\n"
        "/project — переключить проект (если несколько)\n"
        "/help — эта справка\n\n"
        "Просто напишите сообщение, и я передам его в поддержку.\n\n"
        "⏰ Рабочие часы: Пн–Пт 10:00–19:00 (Europe/Madrid)"
    )
    
    # === Errors ===
    ERROR_GENERIC = "Что-то пошло не так. Попробуйте ещё раз или напишите напрямую."
    
    ERROR_NOT_BOUND = "Вы не привязаны к проекту. Используйте /start с кодом или нажмите «Нет кода»."
    
    ERROR_TICKET_NOT_ACTIVE = "Это обращение уже закрыто или отменено. Создайте новое обращение."
    
    ADD_DETAILS_PROMPT = (
        "📝 Обращение #{number}\n\n"
        "Напишите дополнительную информацию или отправьте файл — "
        "сообщение будет добавлено к вашему обращению."
    )
    
    # === Buttons ===
    BTN_ENTER_CODE = "Ввести код"
    BTN_NO_CODE = "Нет кода"
    BTN_SKIP = "Пропустить"
    BTN_DONE = "Готово"
    BTN_PREVIEW = "📋 Превью и отправить"
    BTN_NEW_TICKET = "Новое обращение"
    BTN_TAKE = "▶️ Взять в работу"
    BTN_PAUSE = "⏸️ На паузу"
    BTN_RESUME = "▶️ Возобновить"
    BTN_CLOSE = "✅ Закрыть"
    BTN_CLOSE_SUCCESS = "✅ Закрыть успешно"
    BTN_CANCEL_TICKET = "❌ Отменить"
    BTN_DETAILS = "❓ Запросить детали"
    
    # Summary/Preview buttons
    BTN_EDIT_CATEGORY = "✏️ Категория"
    BTN_EDIT_DESCRIPTION = "✏️ Описание"
    BTN_EDIT_ATTACHMENTS = "✏️ Вложения"
    BTN_CANCEL = "❌ Отмена"
    BTN_SUBMIT = "✅ Отправить"
    
    # Post-ticket menu buttons
    BTN_MY_TICKETS = "📋 Мои обращения"
    BTN_NEW_REQUEST = "➕ Новый запрос"
    BTN_ADD_DETAILS = "📝 Добавить детали к обращению"
    
    # === My Tickets (Library) ===
    MY_TICKETS_HEADER = "📋 Ваши обращения:\n"
    MY_TICKETS_EMPTY = "У вас пока нет обращений."
    MY_TICKETS_ITEM = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎫 Обращение #{number}\n"
        "📁 {category}\n"
        "💬 {description}\n"
        "📅 {date} в {time}\n"
        "{progress_bar}\n"
        "📊 Статус: {status_emoji} {status}\n"
    )
    
    # Progress bar indicators
    PROGRESS_NEW = "🔴⚪⚪⚪ Новый"
    PROGRESS_IN_PROGRESS = "🟡🟡⚪⚪ В работе"
    PROGRESS_ON_HOLD = "🟠🟠⚪⚪ На паузе"
    PROGRESS_COMPLETED = "🟢🟢🟢🟢 Решён!"
    PROGRESS_CANCELLED = "⚫⚫⚫⚫ Отменён"
    
    # Reopen ticket
    REOPEN_TICKET_CONFIRM = (
        "🔄 Проблема вернулась?\n\n"
        "Обращение #{number} будет переоткрыто, и оператор получит уведомление."
    )
    
    REOPEN_TICKET_SUCCESS = (
        "✅ Обращение #{number} переоткрыто!\n\n"
        "Опишите, что произошло — мы разберёмся."
    )
    
    REOPEN_TICKET_TOO_OLD = (
        "⏰ Это обращение было закрыто слишком давно.\n\n"
        "Пожалуйста, создайте новый запрос — так мы поможем быстрее."
    )
    
    # After ticket created/closed menu
    AFTER_TICKET_MENU = "🚀 Что делаем дальше?"
    
    # === Summary ===
    SUMMARY_HEADER = "📋 Превью вашего обращения:"
    SUMMARY_CATEGORY = "📁 Категория: {category}"
    SUMMARY_DESCRIPTION = "📝 Описание:\n{description}"
    SUMMARY_ATTACHMENTS = "📎 Вложения: {count}"
    SUMMARY_FOOTER = "Всё верно?"
    SUMMARY_NO_ATTACHMENTS = "нет"
    
    TICKET_CANCELLED = "Обращение отменено. Если передумаете — напишите /start"
    
    # Edit prompts
    EDIT_CATEGORY_PROMPT = "Выберите новую категорию:"
    EDIT_DESCRIPTION_PROMPT = "Введите новое описание:"
    EDIT_ATTACHMENTS_PROMPT = (
        "Отправьте новые вложения.\n"
        "Предыдущие вложения будут заменены.\n\n"
        "Или нажмите «Пропустить» чтобы убрать вложения."
    )
    
    # === Urgency Levels ===
    URGENCY_FULL_BLOCK = "Полностью блокирует"
    URGENCY_PARTIAL = "Частично мешает"
    URGENCY_NOT_BLOCKING = "Не блокирует, но важно"
    
    # === Template Methods ===
    @staticmethod
    def ticket_created(
        number: int, 
        category: str = "other",
        off_hours: bool = False
    ) -> str:
        """Get ticket created message with SLA based on category."""
        from app.config.categories import get_sla_time
        
        if off_hours:
            return Texts.TICKET_CREATED_OFF_HOURS.format(number=number)
        
        # Get SLA message based on category
        sla_time = get_sla_time(category)
        
        if category == "feature":
            sla_message = Texts.SLA_FEATURE
        elif category == "other" or sla_time is None:
            sla_message = Texts.SLA_OTHER
        else:
            sla_message = Texts.SLA_DEFAULT.format(time=sla_time)
        
        return Texts.TICKET_CREATED.format(number=number, sla_message=sla_message)
    
    @staticmethod
    def ticket_in_progress(number: int) -> str:
        """Get ticket in progress message."""
        return Texts.TICKET_IN_PROGRESS.format(number=number)
    
    @staticmethod
    def ticket_paused(number: int) -> str:
        """Get ticket paused message."""
        return Texts.TICKET_PAUSED.format(number=number)
    
    @staticmethod
    def ticket_paused_with_reason(number: int, reason: str) -> str:
        """Get ticket paused message with reason."""
        return Texts.TICKET_PAUSED_WITH_REASON.format(number=number, reason=reason)
    
    @staticmethod
    def ticket_resumed(number: int) -> str:
        """Get ticket resumed message."""
        return Texts.TICKET_RESUMED.format(number=number)
    
    @staticmethod
    def ticket_closed(number: int) -> str:
        """Get ticket closed message."""
        return Texts.TICKET_CLOSED.format(number=number)
    
    @staticmethod
    def ticket_cancelled(number: int, reason: str) -> str:
        """Get ticket cancelled message with reason."""
        return Texts.TICKET_CANCELLED.format(number=number, reason=reason)
    
    @staticmethod
    def active_ticket_exists(number: int) -> str:
        """Get active ticket exists message."""
        return Texts.ACTIVE_TICKET_EXISTS.format(number=number)
    
    @staticmethod
    def reopen_or_new(number: int) -> str:
        """Get reopen or new ticket message."""
        return Texts.REOPEN_OR_NEW.format(number=number)
    
    @staticmethod
    def ticket_reopened(number: int) -> str:
        """Get ticket reopened message."""
        return Texts.TICKET_REOPENED.format(number=number)
    
    @staticmethod
    def reopen_button(number: int) -> str:
        """Get reopen button text."""
        return f"Продолжить #{number}"
    
    @staticmethod
    def operator_reply(message: str) -> str:
        """Get operator reply message."""
        return Texts.OPERATOR_REPLY.format(message=message)
    
    @staticmethod
    def code_accepted(project_name: str) -> str:
        """Get code accepted message."""
        return Texts.CODE_ACCEPTED.format(project_name=project_name)
    
    @staticmethod
    def welcome_personal(name: str) -> str:
        """Get personalized welcome message."""
        # Use first name only
        first_name = name.split()[0] if name else "друг"
        return Texts.WELCOME_PERSONAL.format(name=first_name)
    
    @staticmethod
    def welcome_back_personal(name: str) -> str:
        """Get personalized welcome back message."""
        first_name = name.split()[0] if name else "друг"
        return Texts.WELCOME_BACK_PERSONAL.format(name=first_name)
    
    @staticmethod
    def project_switched(project_name: str) -> str:
        """Get project switched message."""
        return Texts.PROJECT_SWITCHED.format(project_name=project_name)
    
    @staticmethod
    def project_single(project_name: str) -> str:
        """Get single project message."""
        return Texts.PROJECT_SINGLE.format(project_name=project_name)
    
    @staticmethod
    def add_details_prompt(number: int) -> str:
        """Get add details prompt message."""
        return Texts.ADD_DETAILS_PROMPT.format(number=number)
    
    @staticmethod
    def ticket_summary(
        category: str,
        description: str,
        attachments_count: int = 0
    ) -> str:
        """
        Format ticket summary/preview message.
        
        Args:
            category: Category name with emoji
            description: Ticket description
            attachments_count: Number of attachments
            
        Returns:
            Formatted summary message
        """
        attachments_text = (
            f"{attachments_count} файл(ов)" 
            if attachments_count > 0 
            else Texts.SUMMARY_NO_ATTACHMENTS
        )
        
        # Truncate description if too long
        desc_display = description
        if len(description) > 500:
            desc_display = description[:497] + "..."
        
        return (
            f"{Texts.SUMMARY_HEADER}\n\n"
            f"{Texts.SUMMARY_CATEGORY.format(category=category)}\n\n"
            f"{Texts.SUMMARY_DESCRIPTION.format(description=desc_display)}\n\n"
            f"{Texts.SUMMARY_ATTACHMENTS.format(count=attachments_text)}\n\n"
            f"{Texts.SUMMARY_FOOTER}"
        )
    
    # === Operator Texts ===
    OPERATOR_MY_TICKETS_HEADER = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>МОИ ТИКЕТЫ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    OPERATOR_NO_TICKETS = "У вас пока нет активных тикетов 🎉"
    
    OPERATOR_TICKET_ITEM = (
        "🎫 <b>#{number}</b> | {status_emoji} {status}\n"
        "📁 {category}\n"
        "💬 {description}\n"
    )
    
    OPERATOR_UNASSIGNED_HEADER = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📥 <b>НОВЫЕ ТИКЕТЫ</b> (не взяты)\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    OPERATOR_NO_UNASSIGNED = "Нет новых тикетов! 🎉"
    
    @staticmethod
    def operator_ticket_item(number: int, status: str, category: str, description: str) -> str:
        """Format single ticket item for operator list."""
        status_map = {
            "new": ("🆕", "Новый"),
            "in_progress": ("🔧", "В работе"),
            "on_hold": ("⏸️", "На паузе"),
            "completed": ("✅", "Выполнен"),
            "cancelled": ("❌", "Отменён"),
        }
        status_emoji, status_text = status_map.get(status, ("❓", status))
        
        # Truncate description
        desc = (description or "")[:40]
        if len(description or "") > 40:
            desc += "…"
        
        return Texts.OPERATOR_TICKET_ITEM.format(
            number=number,
            status_emoji=status_emoji,
            status=status_text,
            category=category,
            description=desc
        )
