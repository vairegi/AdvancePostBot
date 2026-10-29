from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🟢 Create Post", callback_data="menu:create")
    keyboard.button(text="📺 My Channels", callback_data="menu:channels")
    keyboard.button(text="💾 Saved Posts", callback_data="menu:saved")
    keyboard.button(text="❓ Help", callback_data="menu:help")
    keyboard.button(text="🔄 Refresh", callback_data="menu:main")
    keyboard.adjust(1, 2, 1)
    return keyboard.as_markup()


def builder_menu(draft):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📝 Caption / Text", callback_data="edit:text")
    keyboard.button(text="🖼 Media", callback_data="edit:media")
    keyboard.button(text="🔗 Inline Buttons", callback_data="edit:ibuttons")
    keyboard.button(text="✨ Caption Buttons", callback_data="edit:cbuttons")
    keyboard.button(text="📊 Table", callback_data="edit:table")
    keyboard.button(text="📺 Select Channel", callback_data="edit:channel")
    keyboard.button(text="⏱ Auto Delete", callback_data="edit:autodelete")
    keyboard.button(
        text="🔕 Silent: " + ("ON" if draft.get("silent") else "OFF"),
        callback_data="edit:silent",
    )
    keyboard.button(
        text="✨ Rich Mode: " + ("ON" if draft.get("rich_mode") else "OFF"),
        callback_data="edit:rich",
    )
    keyboard.button(text="👁 Preview", callback_data="post:preview")
    keyboard.button(text="💾 Save Post", callback_data="post:save")
    keyboard.button(text="🚀 Publish Now", callback_data="post:publish")
    keyboard.button(text="🗑 Reset Post", callback_data="post:reset")
    keyboard.button(text="🏠 Main Menu", callback_data="menu:main")
    keyboard.adjust(2, 2, 2, 1, 1, 1, 2, 2, 1)
    return keyboard.as_markup()


def back_to_builder():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⬅️ Back to Post Builder", callback_data="menu:create")
    keyboard.button(text="🏠 Main Menu", callback_data="menu:main")
    keyboard.adjust(1)
    return keyboard.as_markup()


def channels_menu(channels):
    keyboard = InlineKeyboardBuilder()

    for channel in channels:
        keyboard.button(
            text="✅ " + str(channel.get("title") or channel["chat_id"]),
            callback_data="pickch:" + str(channel["chat_id"]),
        )

    keyboard.button(text="➕ Add Channel", callback_data="ch:add")
    keyboard.button(text="⬅️ Back", callback_data="menu:main")
    keyboard.adjust(1)
    return keyboard.as_markup()


def channel_select_menu(channels, current_channel_id):
    keyboard = InlineKeyboardBuilder()

    for channel in channels:
        if channel["chat_id"] == current_channel_id:
            marker = "🟢"
        else:
            marker = "⚪️"

        keyboard.button(
            text=marker + " " + str(channel.get("title") or channel["chat_id"]),
            callback_data="pickch:" + str(channel["chat_id"]),
        )

    keyboard.button(text="➕ Add New Channel", callback_data="ch:add")
    keyboard.button(text="⬅️ Back to Builder", callback_data="menu:create")
    keyboard.adjust(1)
    return keyboard.as_markup()


def autodelete_menu():
    keyboard = InlineKeyboardBuilder()
    options = (
        ("Permanent", 0),
        ("1 Minute", 60),
        ("10 Minutes", 600),
        ("1 Hour", 3600),
        ("24 Hours", 86400),
    )

    for label, seconds in options:
        keyboard.button(text=label, callback_data="autodel:" + str(seconds))

    keyboard.button(text="⬅️ Back to Builder", callback_data="menu:create")
    keyboard.adjust(2, 2, 1, 1)
    return keyboard.as_markup()


def media_menu(has_media=False):
    keyboard = InlineKeyboardBuilder()

    if has_media:
        keyboard.button(text="🗑 Remove Media", callback_data="media:remove")

    keyboard.button(text="⬅️ Back to Builder", callback_data="menu:create")
    keyboard.adjust(1)
    return keyboard.as_markup()


def saved_posts_menu(posts):
    keyboard = InlineKeyboardBuilder()

    for post in posts:
        title = (post.get("title") or "Untitled")[:30]
        keyboard.button(
            text="📄 " + title,
            callback_data="loadpost:" + str(post["_id"]),
        )

    keyboard.button(text="⬅️ Back", callback_data="menu:main")
    keyboard.adjust(1)
    return keyboard.as_markup()


def confirm_publish(channel_title, auto_delete):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="🚀 Yes, Publish",
        callback_data="post:publish_confirm",
        style="success",
    )
    keyboard.button(
        text="✏️ Edit Post",
        callback_data="menu:create",
        style="primary",
    )
    keyboard.button(
        text="🏠 Main Menu",
        callback_data="menu:main",
        style="danger",
    )
    keyboard.adjust(1, 2)
    return keyboard.as_markup()


def published_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="🆕 Create Another Post",
        callback_data="menu:create",
        style="primary",
    )
    keyboard.button(
        text="🏠 Main Menu",
        callback_data="menu:main",
        style="danger",
    )
    keyboard.adjust(1)
    return keyboard.as_markup()