from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def styled_button(text, callback_data, style=None):
    try:
        if style:
            return InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
                style=style,
            )
    except Exception:
        pass

    return InlineKeyboardButton(
        text=text,
        callback_data=callback_data,
    )


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛠 Create Post", callback_data="menu:create")
    builder.button(text="📺 My Channels", callback_data="menu:channels")
    builder.button(text="💾 Saved Posts", callback_data="menu:saved")
    builder.button(text="❓ Help", callback_data="menu:help")
    builder.adjust(1)
    return builder.as_markup()


def draft_choice_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Continue Editing", callback_data="post:continue")
    builder.button(text="🆕 Start New Post", callback_data="post:new")
    builder.button(text="⬅️ Back", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def builder_menu(draft):
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Add Caption", callback_data="edit:text")
    builder.button(text="🖼 Add Media", callback_data="edit:media")
    builder.button(text="🔗 Add Buttons", callback_data="btns:menu")
    builder.button(text="📊 Add Table", callback_data="edit:table")
    builder.button(text="📺 Select Channel", callback_data="edit:channel")
    builder.button(text="⏱ Auto Delete", callback_data="edit:autodelete")

    silent_text = "🔕 Silent: ON" if draft.get("silent") else "🔔 Silent: OFF"
    builder.button(text=silent_text, callback_data="edit:silent")

    builder.button(text="👁 Refresh Preview", callback_data="post:preview")
    builder.button(text="💾 Save Post", callback_data="post:save")
    builder.button(text="🚀 Publish Now", callback_data="post:publish")
    builder.button(text="🆕 New Post", callback_data="post:reset")
    builder.button(text="🏠 Main Menu", callback_data="menu:main")
    builder.adjust(2, 2, 2, 1, 1, 1, 1, 1)
    return builder.as_markup()


def buttons_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Inline Buttons", callback_data="btns:inline")
    builder.button(text="✨ Caption Buttons", callback_data="btns:caption")
    builder.button(text="⬅️ Back to Builder", callback_data="post:back")
    builder.adjust(1)
    return builder.as_markup()


def back_to_builder():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back to Builder", callback_data="post:back")
    builder.adjust(1)
    return builder.as_markup()


def back_to_buttons_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back to Buttons", callback_data="btns:menu")
    builder.adjust(1)
    return builder.as_markup()


def channels_menu(channels):
    builder = InlineKeyboardBuilder()

    for channel in channels:
        title = channel.get("title") or str(channel.get("chat_id"))
        builder.button(
            text="📺 " + title,
            callback_data="pickch:" + str(channel.get("chat_id")),
        )

    builder.button(text="➕ Add Channel", callback_data="ch:add")
    builder.button(text="⬅️ Back", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def channel_select_menu(channels, selected_channel_id=None):
    builder = InlineKeyboardBuilder()

    for channel in channels:
        title = channel.get("title") or str(channel.get("chat_id"))
        chat_id = channel.get("chat_id")

        if selected_channel_id is not None and chat_id == selected_channel_id:
            title = "✅ " + title

        builder.button(
            text=title,
            callback_data="pickch:" + str(chat_id),
        )

    builder.button(text="➕ Add Channel", callback_data="ch:add")
    builder.button(text="⬅️ Back to Builder", callback_data="post:back")
    builder.adjust(1)
    return builder.as_markup()


def autodelete_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="♾ Permanent", callback_data="autodel:0")
    builder.button(text="5 Minutes", callback_data="autodel:300")
    builder.button(text="1 Hour", callback_data="autodel:3600")
    builder.button(text="1 Day", callback_data="autodel:86400")
    builder.button(text="1 Week", callback_data="autodel:604800")
    builder.button(text="⬅️ Back to Builder", callback_data="post:back")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def media_menu(has_media):
    builder = InlineKeyboardBuilder()

    if has_media:
        builder.button(text="🗑 Remove Media", callback_data="media:remove")

    builder.button(text="⬅️ Back to Builder", callback_data="post:back")
    builder.adjust(1)
    return builder.as_markup()


def saved_posts_menu(posts):
    builder = InlineKeyboardBuilder()

    for post in posts:
        title = post.get("title") or "Untitled Post"
        builder.button(
            text="💾 " + title,
            callback_data="loadpost:" + str(post.get("_id")),
        )

    builder.button(text="⬅️ Back", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def confirm_publish(channel_title, auto_delete):
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Yes, Publish Now", callback_data="post:publish_confirm")
    builder.button(text="❌ Cancel", callback_data="post:back")
    builder.adjust(1)
    return builder.as_markup()


def published_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🆕 Create New Post", callback_data="post:new")
    builder.button(text="🏠 Main Menu", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()