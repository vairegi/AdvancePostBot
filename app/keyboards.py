from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🟢 Create Post", callback_data="menu:create")
    kb.button(text="📺 My Channels", callback_data="menu:channels")
    kb.button(text="💾 Saved Posts", callback_data="menu:saved")
    kb.button(text="❓ Help", callback_data="menu:help")
    kb.button(text="🔄 Refresh", callback_data="menu:main")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def builder_menu(draft):
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Caption / Text", callback_data="edit:text")
    kb.button(text="🖼 Media", callback_data="edit:media")
    kb.button(text="🔗 Buttons", callback_data="edit:buttons")
    kb.button(text="📊 Table", callback_data="edit:table")
    kb.button(text="📺 Select Channel", callback_data="edit:channel")
    kb.button(text="⏱ Auto Delete", callback_data="edit:autodelete")
    kb.button(
        text="🔕 Silent: " + ("ON" if draft.get("silent") else "OFF"),
        callback_data="edit:silent",
    )
    kb.button(text="👁 Preview", callback_data="post:preview")
    kb.button(text="💾 Save Post", callback_data="post:save")
    kb.button(text="🚀 Publish Now", callback_data="post:publish")
    kb.button(text="🗑 Reset Post", callback_data="post:reset")
    kb.button(text="🏠 Main Menu", callback_data="menu:main")
    kb.adjust(2, 2, 2, 1, 2, 2, 1)
    return kb.as_markup()


def back_to_builder():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Back to Post Builder", callback_data="menu:create")
    kb.button(text="🏠 Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def channels_menu(channels):
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(
            text=f"✅ {ch.get('title') or ch['chat_id']}",
            callback_data=f"pickch:{ch['chat_id']}",
        )
    kb.button(text="➕ Add Channel", callback_data="ch:add")
    kb.button(text="⬅️ Back", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def channel_select_menu(channels, current):
    kb = InlineKeyboardBuilder()
    for ch in channels:
        mark = "🟢" if ch["chat_id"] == current else "⚪️"
        kb.button(
            text=f"{mark} {ch.get('title') or ch['chat_id']}",
            callback_data=f"pickch:{ch['chat_id']}",
        )
    kb.button(text="➕ Add New Channel", callback_data="ch:add")
    kb.button(text="⬅️ Back to Builder", callback_data="menu:create")
    kb.adjust(1)
    return kb.as_markup()


def autodelete_menu():
    kb = InlineKeyboardBuilder()
    options = (
        ("Permanent", 0),
        ("1 Minute", 60),
        ("10 Minutes", 600),
        ("1 Hour", 3600),
        ("24 Hours", 86400),
    )
    for label, seconds in options:
        kb.button(text=label, callback_data=f"autodel:{seconds}")
    kb.button(text="⬅️ Back to Builder", callback_data="menu:create")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


def media_menu(has_media=False):
    kb = InlineKeyboardBuilder()
    if has_media:
        kb.button(text="🗑 Remove Media", callback_data="media:remove")
    kb.button(text="⬅️ Back to Builder", callback_data="menu:create")
    kb.adjust(1)
    return kb.as_markup()


def saved_posts_menu(posts):
    kb = InlineKeyboardBuilder()
    for post in posts:
        title = (post.get("title") or "Untitled")[:30]
        kb.button(text=f"📄 {title}", callback_data=f"loadpost:{post['_id']}")
    kb.button(text="⬅️ Back", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def button_layout_menu():
    kb = InlineKeyboardBuilder()
    for count in (1, 2, 3):
        kb.button(text=f"{count} per row", callback_data=f"btnrow:{count}")
    kb.button(text="⬅️ Back to Builder", callback_data="menu:create")
    kb.adjust(3, 1)
    return kb.as_markup()


def confirm_publish(channel_title, autodel):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Yes, Publish", callback_data="post:publish_confirm")
    kb.button(text="✏️ Edit Post", callback_data="menu:create")
    kb.button(text="🏠 Main Menu", callback_data="menu:main")
    kb.adjust(1, 2)
    return kb.as_markup()


def published_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🆕 Create Another Post", callback_data="menu:create")
    kb.button(text="🏠 Main Menu", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()