from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command
from aiogram.enums import ParseMode
from ..services.users import get_user
from ..services.mentorship import (
    create_mentor_application,
    get_incoming_for_mentor,
    get_mentor_list,
    get_user_applications,
    set_application_status,
)
from ..storage.models import MentorTopic  # Добавляем импорт для MentorTopic
from ..keyboards.common import (
    mentorship_root_kb,
    mentor_list_kb,
    mentor_topics_kb,
    mentor_confirm_kb,
    mentor_inbox_kb,
    main_menu_kb,
)

router = Router(name="mentorship")


@router.callback_query(F.data == "menu:open:mentorship")
async def mentorship_root(cb: CallbackQuery):
    text = (
        "🤝 <b>Менторство</b>\n"
        "Нужна помощь ментора? Выбери наставника по теме или посмотри свои заявки."
    )
    await cb.message.edit_text(
        text, reply_markup=mentorship_root_kb(), parse_mode=ParseMode.HTML
    )
    await cb.answer()


# Просмотр списка наставников
@router.message(Command("mentors"))
async def show_mentors(msg: Message):
    mentors = get_mentor_list()
    if not mentors:
        await msg.answer("Нет доступных наставников.")
        return

    # Создаем клавиатуру для выбора наставника
    buttons = [
        InlineKeyboardButton(
            text=f"{mentor.username} ({mentor.role})",
            callback_data=f"mentor:{mentor.id}",
        )
        for mentor in mentors
    ]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(*buttons)

    await msg.answer("Выберите наставника:", reply_markup=kb)


# Выбор наставника
@router.callback_query(F.data == "mentor:choose")
async def choose_mentor(cb: CallbackQuery):
    mentors = get_mentor_list()
    if not mentors:
        await cb.message.edit_text(
            "Пока нет доступных наставников.", reply_markup=mentorship_root_kb()
        )
        return await cb.answer()
    await cb.message.edit_text(
        "Выберите наставника:", reply_markup=mentor_list_kb(mentors)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("mentor:pick:"))
async def pick_mentor(cb: CallbackQuery):
    mentor_id = int(cb.data.split(":")[2])
    mentor = get_user(mentor_id)
    if not mentor:
        await cb.answer("Наставник не найден")
        return
    name = f"@{mentor.username}" if mentor.username else f"ID {mentor.tg_id}"
    await cb.message.edit_text(
        f"Наставник: <b>{name}</b>\nВыбери тему:",
        reply_markup=mentor_topics_kb(mentor_id),
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()


@router.callback_query(F.data.startswith("mentor:topic:"))
async def pick_topic(cb: CallbackQuery):
    _, _, mentor_id, topic = cb.data.split(":")
    mentor_id = int(mentor_id)
    topic_title = {
        MentorTopic.CAREER.value: "Карьера",
        MentorTopic.CONTENT.value: "Контент",
        MentorTopic.PROJECTS.value: "Проекты",
        MentorTopic.IDEAS.value: "Идеи",
    }.get(topic, topic)

    await cb.message.edit_text(
        f"Тема: <b>{topic_title}</b>\n\nОтправить заявку этому наставнику?",
        reply_markup=mentor_confirm_kb(mentor_id, topic),
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()


@router.callback_query(F.data.startswith("mentor:topic_back:"))
async def back_to_topics(cb: CallbackQuery):
    mentor_id = int(cb.data.split(":")[2])
    await cb.message.edit_text("Выбери тему:", reply_markup=mentor_topics_kb(mentor_id))
    await cb.answer()


@router.callback_query(F.data.startswith("mentor:confirm:"))
async def confirm_application(cb: CallbackQuery):
    _, _, mentor_id, topic = cb.data.split(":")
    mentor_id = int(mentor_id)
    try:
        topic_enum = MentorTopic(topic)
    except Exception:
        await cb.answer("Некорректная тема")
        return
    app = create_mentor_application(cb.from_user.id, mentor_id, topic_enum)
    if app.status == "pending":
        await cb.message.edit_text(
            "Заявка отправлена ✅\nСтатус: pending", reply_markup=mentorship_root_kb()
        )
        # уведомим ментора (если есть его tg id)
        mentor = get_user(mentor_id)
        if mentor and mentor.tg_id:
            try:
                await cb.bot.send_message(
                    mentor.tg_id,
                    f"🆕 Новая заявка на менторство от @{cb.from_user.username or cb.from_user.id}\n"
                    f"Тема: <b>{topic_enum.name}</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
    else:
        await cb.message.edit_text(
            "Заявка обновлена.", reply_markup=mentorship_root_kb()
        )
    await cb.answer()


# Мои заявки
@router.callback_query(F.data == "mentor:myapps")
async def my_apps(cb: CallbackQuery):
    apps = get_user_applications(cb.from_user.id)
    if not apps:
        await cb.message.edit_text(
            "У вас пока нет заявок.", reply_markup=mentorship_root_kb()
        )
        return await cb.answer()
    lines = []
    for a in apps:
        topic = a.topic
        status = a.status
        mn = get_user(a.mentor_id)
        mname = f"@{mn.username}" if mn and mn.username else f"ID {a.mentor_id}"
        lines.append(f"• {topic} → {mname} — <b>{status}</b>")
    await cb.message.edit_text(
        "🗂 <b>Мои заявки</b>\n\n" + "\n".join(lines),
        reply_markup=mentorship_root_kb(),
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()


# Инбокс ментора (pending заявки)
@router.callback_query(F.data == "mentor:inbox")
async def mentor_inbox(cb: CallbackQuery):
    inbox = get_incoming_for_mentor(cb.from_user.id, status="pending")
    if not inbox:
        await cb.message.edit_text(
            "Входящих заявок нет.", reply_markup=mentorship_root_kb()
        )
        return await cb.answer()
    # Покажем по одной (простая версия): последнюю
    app = inbox[0]
    usr = get_user(app.user_id)
    uname = f"@{usr.username}" if usr and usr.username else f"ID {app.user_id}"
    text = (
        f"📥 Заявка #{app.id}\n"
        f"От: {uname}\n"
        f"Тема: <b>{app.topic}</b>\n"
        f"Статус: {app.status}"
    )
    await cb.message.edit_text(
        text, reply_markup=mentor_inbox_kb(app.id), parse_mode=ParseMode.HTML
    )
    await cb.answer()


# Апрув/реджект
@router.callback_query(F.data.startswith("mentor:app:"))
async def app_decision(cb: CallbackQuery):
    _, _, app_id, action = cb.data.split(":")
    app_id = int(app_id)
    if action not in {"approve", "reject"}:
        return await cb.answer("Неизвестное действие")
    updated = set_application_status(
        app_id, cb.from_user.id, "approved" if action == "approve" else "rejected"
    )
    if not updated:
        await cb.answer("Заявка не найдена или уже обработана")
        return
    # уведомим пользователя
    usr = get_user(updated.user_id)
    if usr and usr.tg_id:
        try:
            await cb.bot.send_message(
                usr.tg_id,
                f"📢 Ваша заявка #{updated.id} {'принята ✅' if updated.status == 'approved' else 'отклонена ❌'}",
            )
        except Exception:
            pass
    await cb.message.edit_text(
        f"Заявка #{updated.id}: статус → {updated.status}",
        reply_markup=mentorship_root_kb(),
    )
    await cb.answer()


# Отправка заявки на менторство
@router.callback_query(F.data.startswith("mentor:choose"))
async def mentor_callback(cb: CallbackQuery):
    mentor_id = int(cb.data.split(":")[1])
    topic = MentorTopic.CONTENT  # По умолчанию, или сделаем выбор темы
    user_id = cb.from_user.id

    # Проверка, что наставник существует
    mentor = get_user(mentor_id)
    if not mentor:
        await cb.answer("Наставник не найден.")
        return

    # Отправка заявки
    create_mentor_application(user_id=user_id, mentor_id=mentor_id, topic=topic)
    await cb.answer("Ваша заявка на менторство отправлена!")


@router.callback_query(F.data == "menu:open:main")
async def back_to_main_menu(cb: CallbackQuery):
    text = "Вы вернулись в главное меню."
    await cb.message.edit_text(text, reply_markup=main_menu_kb())  # Главное меню
    await cb.answer()

    print(f"Received callback with data: {cb.data}")  # Для отладки
