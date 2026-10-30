from aiogram.types import InlineKeyboardButton
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
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Create Post", "menu:create", "success")
    )
    keyboard.row(
        styled_button("My Channels", "menu:channels", "primary"),
        styled_button("Saved Posts", "menu:saved", "primary"),
    )
    keyboard.row(
        styled_button("Help", "menu:help", "primary"),
        styled_button("Refresh", "menu:main", "primary"),
    )
    return keyboard.as_markup()


def draft_choice_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Continue Editing", "post:continue", "success")
    )
    keyboard.row(
        styled_button("Start New Post", "post:new", "danger")
    )
    keyboard.row(
        styled_button("Main Menu", "menu:main", "primary")
    )
    return keyboard.as_markup()


def builder_menu(draft):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Add Caption", "edit:text", "primary"),
        styled_button("Add Media", "edit:media", "primary"),
    )
    keyboard.row(
        styled_button("Add Buttons", "btns:menu", "success"),
        styled_button("Add Table", "edit:table", "primary"),
    )
    keyboard.row(
        styled_button("Select Channel", "edit:channel", "primary"),
        styled_button("Auto Delete", "edit:autodelete", "primary"),
    )
    keyboard.row(
        styled_button(
            "Silent: " + ("ON" if draft.get("silent") else "OFF"),
            "edit:silent",
            "primary",
        ),
        styled_button(
            "Rich Mode: " + ("ON" if draft.get("rich_mode") else "OFF"),
            "edit:rich",
            "success" if draft.get("rich_mode") else "primary",
        ),
    )
    keyboard.row(
        styled_button("Preview", "post:preview", "primary"),
        styled_button("Save Post", "post:save", "success"),
    )
    keyboard.row(
        styled_button("Publish Now", "post:publish", "success")
    )
    keyboard.row(
        styled_button("Reset Post", "post:reset", "danger"),
        styled_button("Main Menu", "menu:main", "primary"),
    )
    return keyboard.as_markup()


def buttons_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Add Inline Buttons", "btns:inline", "primary")
    )
    keyboard.row(
        styled_button("Add Caption Buttons", "btns:caption", "success")
    )
    keyboard.row(
        styled_button("Back to Post Builder", "menu:create", "primary")
    )
    return keyboard.as_markup()


def back_to_builder():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Back to Post Builder", "menu:create", "primary")
    )
    keyboard.row(
        styled_button("Main Menu", "menu:main", "primary")
    )
    return keyboard.as_markup()


def back_to_buttons_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Back to Buttons Menu", "btns:menu", "primary")
    )
    keyboard.row(
        styled_button("Back to Post Builder", "menu:create", "primary")
    )
    return keyboard.as_markup()


def channels_menu(channels):
    keyboard = InlineKeyboardBuilder()

    for channel in channels:
        keyboard.row(
            styled_button(
                str(channel.get("title") or channel["chat_id"]),
                "pickch:" + str(channel["chat_id"]),
                "primary",
            )
        )

    keyboard.row(
        styled_button("Add Channel", "ch:add", "success")
    )
    keyboard.row(
        styled_button("Back", "menu:main", "primary")
    )
    return keyboard.as_markup()


def channel_select_menu(channels, current_channel_id):
    keyboard = InlineKeyboardBuilder()

    for channel in channels:
        if channel["chat_id"] == current_channel_id:
            marker = "Selected"
            style = "success"
        else:
            marker = "Select"
            style = "primary"

        keyboard.row(
            styled_button(
                marker + " - " + str(channel.get("title") or channel["chat_id"]),
                "pickch:" + str(channel["chat_id"]),
                style,
            )
        )

    keyboard.row(
        styled_button("Add New Channel", "ch:add", "success")
    )
    keyboard.row(
        styled_button("Back to Post Builder", "menu:create", "primary")
    )
    return keyboard.as_markup()


def autodelete_menu():
    keyboard = InlineKeyboardBuilder()
    options = (
        ("Permanent", 0, "primary"),
        ("1 Minute", 60, "primary"),
        ("10 Minutes", 600, "primary"),
        ("1 Hour", 3600, "danger"),
        ("24 Hours", 86400, "danger"),
    )

    for label, seconds, style in options:
        keyboard.row(
            styled_button(
                label,
                "autodel:" + str(seconds),
                style,
            )
        )

    keyboard.row(
        styled_button("Back to Post Builder", "menu:create", "primary")
    )
    return keyboard.as_markup()


def media_menu(has_media=False):
    keyboard = InlineKeyboardBuilder()

    if has_media:
        keyboard.row(
            styled_button("Remove Media", "media:remove", "danger")
        )

    keyboard.row(
        styled_button("Back to Post Builder", "menu:create", "primary")
    )
    return keyboard.as_markup()


def saved_posts_menu(posts):
    keyboard = InlineKeyboardBuilder()

    for post in posts:
        title = (post.get("title") or "Untitled")[:30]
        keyboard.row(
            styled_button(
                "Load - " + title,
                "loadpost:" + str(post["_id"]),
                "primary",
            )
        )

    keyboard.row(
        styled_button("Back", "menu:main", "primary")
    )
    return keyboard.as_markup()


def confirm_publish(channel_title, auto_delete):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Yes, Publish Now", "post:publish_confirm", "success")
    )
    keyboard.row(
        styled_button("Edit Post", "menu:create", "primary"),
        styled_button("Main Menu", "menu:main", "primary"),
    )
    return keyboard.as_markup()


def published_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        styled_button("Create Another Post", "menu:create", "success")
    )
    keyboard.row(
        styled_button("Main Menu", "menu:main", "primary")
    )
    return keyboard.as_markup()