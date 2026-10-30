import asyncio
from datetime import datetime, timezone
from bson import ObjectId

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InputRichMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import db
from app.utils import NEWLINE
from app.keyboards import (
    main_menu,
    draft_choice_menu,
    builder_menu,
    buttons_menu,
    back_to_builder,
    back_to_buttons_menu,
    channels_menu,
    channel_select_menu,
    autodelete_menu,
    media_menu,
    saved_posts_menu,
    confirm_publish,
    published_menu,
)
from app.utils import (
    build_caption,
    build_rich_html,
    parse_table_input,
    parse_button_rows,
    convert_old_buttons_to_rows,
    human_time,
    esc,
)

router = Router()


async def get_draft(user_id, create=True):
    draft = await db.drafts.find_one({"user_id": user_id})
    if draft or not create:
        return draft

    new_draft = db.empty_draft()
    new_draft["user_id"] = user_id
    await db.drafts.insert_one(new_draft)
    return new_draft


async def save_draft(user_id, update):
    set_update = dict(update)
    unset_update = {}

    if "waiting_for" not in set_update:
        unset_update["waiting_for"] = ""

    update_operation = {"$set": set_update}

    if unset_update:
        update_operation["$unset"] = unset_update

    await db.drafts.update_one(
        {"user_id": user_id},
        update_operation,
        upsert=True,
    )


async def delete_message_safe(bot, chat_id, message_id):
    if not message_id:
        return

    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


def builder_text(draft):
    draft = convert_old_buttons_to_rows(draft)

    caption = "Added" if draft.get("text") else "Not added"
    media = esc(draft.get("media_type") or "No media")

    inline_rows = draft.get("button_rows") or []
    inline_count = sum(len(row) for row in inline_rows)

    caption_rows = draft.get("caption_button_rows") or []
    caption_button_count = sum(len(row) for row in caption_rows)

    table = "Yes" if draft.get("table") else "No"
    channel = esc(draft.get("channel_title") or "Not selected")
    auto_delete = esc(human_time(draft.get("auto_delete_seconds")))
    silent = "ON" if draft.get("silent") else "OFF"
    rich_mode = "ON" if draft.get("rich_mode") else "OFF"

    return f"""━━━━━━━━━━━━━━━━━━━━
🛠 <b>ADVANCED POST BUILDER</b>
━━━━━━━━━━━━━━━━━━━━

Your post preview is shown above.
Every change you make will update the preview automatically.

━━━━━━━━━━━━━━━━━━━━
<b>POST DETAILS</b>
━━━━━━━━━━━━━━━━━━━━

📝 <b>Caption:</b> {caption}
🖼 <b>Media:</b> {media}
🔗 <b>Inline Buttons:</b> {inline_count} buttons in {len(inline_rows)} rows
✨ <b>Caption Buttons:</b> {caption_button_count} buttons in {len(caption_rows)} rows
📊 <b>Table:</b> {table}
📺 <b>Channel:</b> {channel}
⏱ <b>Auto Delete:</b> {auto_delete}
🔕 <b>Silent:</b> {silent}
✨ <b>Rich Mode:</b> {rich_mode}"""


async def refresh_builder(bot: Bot, chat_id: int, user_id: int):
    draft = await get_draft(user_id)
    draft = convert_old_buttons_to_rows(draft)

    await delete_message_safe(bot, chat_id, draft.get("preview_message_id"))
    await delete_message_safe(bot, chat_id, draft.get("builder_message_id"))

    caption = build_caption(draft)
    keyboard = post_keyboard(draft)

    try:
        if draft.get("rich_mode") and not draft.get("media_file_id"):
            rich_html = build_rich_html(draft)

            if rich_html:
                preview = await bot.send_rich_message(
                    chat_id,
                    rich_message=InputRichMessage(html=rich_html),
                    reply_markup=keyboard,
                )
            else:
                preview = await bot.send_message(
                    chat_id,
                    "👁 <b>LIVE PREVIEW</b>"
                    + NEWLINE
                    + NEWLINE
                    + "<i>No caption added yet.</i>",
                    reply_markup=keyboard,
                )

        elif draft.get("media_file_id"):
            media_type = draft.get("media_type")
            file_id = draft["media_file_id"]
            media_caption = caption or "No caption added yet."

            if media_type == "photo":
                preview = await bot.send_photo(
                    chat_id,
                    file_id,
                    caption=media_caption,
                    reply_markup=keyboard,
                )
            elif media_type == "video":
                preview = await bot.send_video(
                    chat_id,
                    file_id,
                    caption=media_caption,
                    reply_markup=keyboard,
                )
            elif media_type == "audio":
                preview = await bot.send_audio(
                    chat_id,
                    file_id,
                    caption=media_caption,
                    reply_markup=keyboard,
                )
            elif media_type == "document":
                preview = await bot.send_document(
                    chat_id,
                    file_id,
                    caption=media_caption,
                    reply_markup=keyboard,
                )
            elif media_type == "animation":
                preview = await bot.send_animation(
                    chat_id,
                    file_id,
                    caption=media_caption,
                    reply_markup=keyboard,
                )
            else:
                preview = await bot.send_message(
                    chat_id,
                    media_caption,
                    reply_markup=keyboard,
                )

        else:
            preview_text = (
                "👁 <b>LIVE PREVIEW</b>"
                + NEWLINE
                + NEWLINE
                + (caption or "<i>No caption added yet.</i>")
            )

            preview = await bot.send_message(
                chat_id,
                preview_text,
                reply_markup=keyboard,
            )

        builder_message = await bot.send_message(
            chat_id,
            builder_text(draft),
            reply_markup=builder_menu(draft),
        )

        await save_draft(
            user_id,
            {
                "preview_message_id": preview.message_id,
                "builder_message_id": builder_message.message_id,
            },
        )
    except TelegramBadRequest as error:
        await bot.send_message(
            chat_id,
            "⚠️ Preview error: " + error.message,
        )


async def refresh_builder_from_callback(callback: CallbackQuery):
    await delete_message_safe(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
    )

    await refresh_builder(
        callback.bot,
        callback.message.chat.id,
        callback.from_user.id,
    )


def post_keyboard(draft):
    draft = convert_old_buttons_to_rows(draft)
    button_rows = draft.get("button_rows") or []

    if not button_rows:
        return None

    inline_rows = []

    for row in button_rows:
        inline_row = []

        for button in row:
            inline_row.append(
                InlineKeyboardButton(
                    text=button["text"],
                    url=button["url"],
                )
            )

        inline_rows.append(inline_row)

    return InlineKeyboardMarkup(inline_keyboard=inline_rows)


HELP_TEXT = """━━━━━━━━━━━━━━━━━━━━
❓ <b>HOW TO USE</b>
━━━━━━━━━━━━━━━━━━━━

<b>1. Add a Channel</b>
Make the bot an administrator in your channel and enable Post Messages permission.

Then open <b>My Channels -> Add Channel</b> and send <code>@channelusername</code>, or forward any message from the channel.

━━━━━━━━━━━━━━━━━━━━
<b>2. Add Caption</b>
━━━━━━━━━━━━━━━━━━━━

Telegram HTML is supported:

<code>&lt;b&gt;Bold&lt;/b&gt;</code>
<code>&lt;i&gt;Italic&lt;/i&gt;</code>
<code>&lt;u&gt;Underline&lt;/u&gt;</code>
<code>&lt;a href="https://example.com"&gt;Link&lt;/a&gt;</code>

━━━━━━━━━━━━━━━━━━━━
<b>3. Add Buttons</b>
━━━━━━━━━━━━━━━━━━━━

<b>Inline Buttons</b> appear below the post.
They do not support custom colors.

<b>Caption Buttons</b> appear inside a Rich Message.
They support colors: blue, green, red.

Each line creates one button row.

💡 One button in a row:
<code>Join Channel | https://t.me/telegram | green</code>

💡 Two buttons in one row:
<code>Visit Website | https://example.com | blue || Help | https://example.com | red</code>

💡 No color means a normal transparent button:
<code>Visit Website | https://example.com</code>

━━━━━━━━━━━━━━━━━━━━
<b>4. Add Table</b>
━━━━━━━━━━━━━━━━━━━━

The first line is the header. Other lines are rows.
Separate columns using <code>|</code>.

💡 Example:
<code>Product | Price</code>
<code>Apple | $1.00</code>
<code>Mango | $1.20</code>

━━━━━━━━━━━━━━━━━━━━
<b>5. Rich Mode</b>
━━━━━━━━━━━━━━━━━━━━

Rich Mode publishes a Rich Message.
It supports a real styled table and colored caption buttons.

Caption Buttons automatically turn Rich Mode ON.

━━━━━━━━━━━━━━━━━━━━
<b>6. Publish</b>
━━━━━━━━━━━━━━━━━━━━

Select a channel, check the live preview, then tap Publish Now."""


@router.message(CommandStart())
async def start_command(message: Message):
    await db.users.update_one(
        {"user_id": message.from_user.id},
        {
            "$set": {
                "user_id": message.from_user.id,
                "first_name": message.from_user.first_name,
                "username": message.from_user.username,
                "last_seen": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    await message.answer(
        """━━━━━━━━━━━━━━━━━━━━
👋 <b>WELCOME</b>
━━━━━━━━━━━━━━━━━━━━

<b>Advanced Post Creator Bot</b>

Create beautiful, professional and rich posts for your Telegram channels.

━━━━━━━━━━━━━━━━━━━━
<b>WHAT YOU CAN DO</b>
━━━━━━━━━━━━━━━━━━━━

• Create posts with captions and media
• Add inline buttons and caption buttons
• Create clean tables
• Publish directly to your channels
• Save and reuse posts
• Set automatic deletion

━━━━━━━━━━━━━━━━━━━━
💡 <i>Tap <b>Create Post</b> to get started.</i>""",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(HELP_TEXT, reply_markup=back_to_builder())


@router.callback_query(F.data == "menu:main")
async def main_menu_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    await delete_message_safe(
        callback.bot,
        callback.message.chat.id,
        draft.get("preview_message_id"),
    )

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
👋 <b>MAIN MENU</b>
━━━━━━━━━━━━━━━━━━━━

Choose an option below.""",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def help_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:create")
async def create_post_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    if db.draft_has_content(draft):
        await callback.message.edit_text(
            """━━━━━━━━━━━━━━━━━━━━
🛠 <b>UNFINISHED POST FOUND</b>
━━━━━━━━━━━━━━━━━━━━

You already have an unfinished post.

💡 Do you want to continue editing it, or start a new post?""",
            reply_markup=draft_choice_menu(),
        )
        await callback.answer()
        return

    await refresh_builder_from_callback(callback)
    await callback.answer()


@router.callback_query(F.data == "post:continue")
async def continue_post_callback(callback: CallbackQuery):
    await refresh_builder_from_callback(callback)
    await callback.answer("Continuing your post ✅")


@router.callback_query(F.data == "post:new")
async def new_post_callback(callback: CallbackQuery):
    draft = db.empty_draft()
    draft["user_id"] = callback.from_user.id

    await db.drafts.replace_one(
        {"user_id": callback.from_user.id},
        draft,
        upsert=True,
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("New post started ✅")


@router.callback_query(F.data == "menu:channels")
async def channels_callback(callback: CallbackQuery):
    channels = await db.channels.find(
        {"user_id": callback.from_user.id}
    ).to_list(100)

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
📺 <b>MY CHANNELS</b>
━━━━━━━━━━━━━━━━━━━━

Select a channel or add a new one.""",
        reply_markup=channels_menu(channels),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:saved")
async def saved_posts_callback(callback: CallbackQuery):
    posts = await db.saved_posts.find(
        {"user_id": callback.from_user.id}
    ).sort("_id", -1).to_list(50)

    if not posts:
        await callback.message.edit_text(
            """━━━━━━━━━━━━━━━━━━━━
💾 <b>SAVED POSTS</b>
━━━━━━━━━━━━━━━━━━━━

You have no saved posts yet.

💡 Open the Post Builder and tap <b>Save Post</b>.""",
            reply_markup=back_to_builder(),
        )
    else:
        await callback.message.edit_text(
            """━━━━━━━━━━━━━━━━━━━━
💾 <b>SAVED POSTS</b>
━━━━━━━━━━━━━━━━━━━━

Select a post to load it into the Post Builder.""",
            reply_markup=saved_posts_menu(posts),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("loadpost:"))
async def load_post_callback(callback: CallbackQuery):
    post_id = callback.data.split(":", 1)[1]

    post = await db.saved_posts.find_one(
        {
            "_id": ObjectId(post_id),
            "user_id": callback.from_user.id,
        }
    )

    if not post:
        await callback.answer("Post not found.", show_alert=True)
        return

    post["user_id"] = callback.from_user.id
    post["waiting_for"] = None
    post = convert_old_buttons_to_rows(post)

    await db.drafts.replace_one(
        {"user_id": callback.from_user.id},
        post,
        upsert=True,
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("Post loaded ✅")


@router.callback_query(F.data == "ch:add")
async def add_channel_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "channel_add"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
➕ <b>ADD CHANNEL</b>
━━━━━━━━━━━━━━━━━━━━

Send your channel username:
<code>@channelusername</code>

For a private channel, forward any message from that channel to this bot.

⚠️ First, add the bot as an administrator in the channel and enable Post Messages permission.""",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pickch:"))
async def pick_channel_callback(callback: CallbackQuery):
    raw_channel_id = callback.data.split(":", 1)[1]

    try:
        chat_id = int(raw_channel_id)
    except ValueError:
        chat_id = raw_channel_id

    channel = await db.channels.find_one(
        {
            "user_id": callback.from_user.id,
            "chat_id": chat_id,
        }
    )

    if not channel:
        await callback.answer("Channel not found.", show_alert=True)
        return

    await save_draft(
        callback.from_user.id,
        {
            "channel_id": chat_id,
            "channel_title": channel.get("title"),
        },
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("Channel selected ✅")


@router.callback_query(F.data == "edit:text")
async def edit_text_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "text"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
📝 <b>ADD CAPTION</b>
━━━━━━━━━━━━━━━━━━━━

Send your caption or post text now.

💡 Telegram HTML is supported:

<code>&lt;b&gt;Bold&lt;/b&gt;</code>
<code>&lt;i&gt;Italic&lt;/i&gt;</code>
<code>&lt;u&gt;Underline&lt;/u&gt;</code>
<code>&lt;a href="https://example.com"&gt;Link&lt;/a&gt;</code>""",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:media")
async def edit_media_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)
    await save_draft(callback.from_user.id, {"waiting_for": "media"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
🖼 <b>ADD MEDIA</b>
━━━━━━━━━━━━━━━━━━━━

Send a photo, video, audio file, document, or animation.

💡 Your media will appear in the live preview above.""",
        reply_markup=media_menu(bool(draft.get("media_file_id"))),
    )
    await callback.answer()


@router.callback_query(F.data == "media:remove")
async def remove_media_callback(callback: CallbackQuery):
    await save_draft(
        callback.from_user.id,
        {
            "media_type": None,
            "media_file_id": None,
        },
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("Media removed ✅")


@router.callback_query(F.data == "btns:menu")
async def buttons_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
🔗 <b>ADD BUTTONS</b>
━━━━━━━━━━━━━━━━━━━━

Choose the type of buttons you want to add.

💡 <b>Inline Buttons</b> appear below the post.
They do not support custom colors.

💡 <b>Caption Buttons</b> appear inside a Rich Message and support colors.""",
        reply_markup=buttons_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "btns:inline")
async def inline_buttons_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "inline_buttons"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
🔗 <b>ADD INLINE BUTTONS</b>
━━━━━━━━━━━━━━━━━━━━

Each line creates one button row.

💡 One button in a row:
<code>Join Channel | https://t.me/telegram</code>

💡 Two buttons in one row:
<code>Visit Website | https://example.com || Help | https://example.com</code>

⚠️ Inline buttons do not support custom colors.

Send your buttons now.""",
        reply_markup=back_to_buttons_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "btns:caption")
async def caption_buttons_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "caption_buttons"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
✨ <b>ADD CAPTION BUTTONS</b>
━━━━━━━━━━━━━━━━━━━━

These buttons appear inside a Rich Message.

Each line creates one button row.

💡 One button in a row:
<code>Join Channel | https://t.me/telegram | green</code>

💡 Two buttons in one row:
<code>Visit Website | https://example.com | blue || Help | https://example.com | red</code>

💡 No color means a normal transparent button:
<code>Visit Website | https://example.com</code>

💡 Colors: <code>blue</code>, <code>green</code>, <code>red</code>

Send your caption buttons now.""",
        reply_markup=back_to_buttons_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:table")
async def edit_table_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "table"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
📊 <b>ADD TABLE</b>
━━━━━━━━━━━━━━━━━━━━

The first line is the header. Other lines are rows.
Separate columns using <code>|</code>.

💡 Example:
<code>Product | Price</code>
<code>Apple | $1.00</code>
<code>Mango | $1.20</code>

With Rich Mode ON, this becomes a real styled table.""",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:channel")
async def edit_channel_callback(callback: CallbackQuery):
    channels = await db.channels.find(
        {"user_id": callback.from_user.id}
    ).to_list(100)

    draft = await get_draft(callback.from_user.id)

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
📺 <b>SELECT CHANNEL</b>
━━━━━━━━━━━━━━━━━━━━

Choose the channel where this post will be published.""",
        reply_markup=channel_select_menu(channels, draft.get("channel_id")),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:autodelete")
async def autodelete_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
⏱ <b>AUTO DELETE</b>
━━━━━━━━━━━━━━━━━━━━

Choose when the post should be deleted automatically.

💡 If you choose Permanent, the post will not be deleted.""",
        reply_markup=autodelete_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("autodel:"))
async def set_autodelete_callback(callback: CallbackQuery):
    seconds = int(callback.data.split(":", 1)[1])

    await save_draft(
        callback.from_user.id,
        {"auto_delete_seconds": seconds},
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("Auto delete set ✅")


@router.callback_query(F.data == "edit:silent")
async def toggle_silent_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    await save_draft(
        callback.from_user.id,
        {"silent": not draft.get("silent", False)},
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("Silent mode updated ✅")


@router.callback_query(F.data == "edit:rich")
async def toggle_rich_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    await save_draft(
        callback.from_user.id,
        {"rich_mode": not draft.get("rich_mode", False)},
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("Rich Mode updated ✅")


@router.callback_query(F.data == "post:reset")
async def reset_post_callback(callback: CallbackQuery):
    draft = db.empty_draft()
    draft["user_id"] = callback.from_user.id

    await db.drafts.replace_one(
        {"user_id": callback.from_user.id},
        draft,
        upsert=True,
    )

    await refresh_builder_from_callback(callback)
    await callback.answer("New post started ✅")


@router.callback_query(F.data == "post:preview")
async def preview_callback(callback: CallbackQuery):
    await refresh_builder_from_callback(callback)
    await callback.answer("Live preview refreshed ✅")


async def send_media_message(bot, chat_id, draft, caption, keyboard):
    file_id = draft["media_file_id"]
    media_type = draft.get("media_type")
    silent = draft.get("silent", False)

    if media_type == "photo":
        return await bot.send_photo(
            chat_id,
            file_id,
            caption=caption,
            reply_markup=keyboard,
            disable_notification=silent,
        )

    if media_type == "video":
        return await bot.send_video(
            chat_id,
            file_id,
            caption=caption,
            reply_markup=keyboard,
            disable_notification=silent,
        )

    if media_type == "audio":
        return await bot.send_audio(
            chat_id,
            file_id,
            caption=caption,
            reply_markup=keyboard,
            disable_notification=silent,
        )

    if media_type == "document":
        return await bot.send_document(
            chat_id,
            file_id,
            caption=caption,
            reply_markup=keyboard,
            disable_notification=silent,
        )

    if media_type == "animation":
        return await bot.send_animation(
            chat_id,
            file_id,
            caption=caption,
            reply_markup=keyboard,
            disable_notification=silent,
        )

    raise ValueError("Unsupported media type")


@router.callback_query(F.data == "post:save")
async def save_post_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    if not (
        draft.get("text")
        or draft.get("media_file_id")
        or draft.get("table")
    ):
        await callback.answer(
            "Add a caption, media, or table first.",
            show_alert=True,
        )
        return

    await save_draft(callback.from_user.id, {"waiting_for": "save_title"})

    await callback.message.edit_text(
        """━━━━━━━━━━━━━━━━━━━━
💾 <b>SAVE POST</b>
━━━━━━━━━━━━━━━━━━━━

Send a name for this post.

💡 This name will appear only in your Saved Posts.

Example: <code>Daily Offer Post</code>""",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data == "post:publish")
async def publish_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    if not draft.get("channel_id"):
        await callback.answer(
            "Select a channel first.",
            show_alert=True,
        )
        return

    if not (
        draft.get("text")
        or draft.get("media_file_id")
        or draft.get("table")
    ):
        await callback.answer(
            "Add a caption, media, or table first.",
            show_alert=True,
        )
        return

    channel_title = draft.get("channel_title") or str(draft["channel_id"])
    auto_delete = human_time(draft.get("auto_delete_seconds"))

    await callback.message.edit_text(
        f"""━━━━━━━━━━━━━━━━━━━━
🚀 <b>PUBLISH POST</b>
━━━━━━━━━━━━━━━━━━━━

📺 <b>Channel:</b> {esc(channel_title)}
⏱ <b>Auto Delete:</b> {esc(auto_delete)}
✨ <b>Rich Mode:</b> {'ON' if draft.get('rich_mode') else 'OFF'}

Do you want to publish this post?""",
        reply_markup=confirm_publish(channel_title, auto_delete),
    )
    await callback.answer()


@router.callback_query(F.data == "post:publish_confirm")
async def publish_confirm_callback(callback: CallbackQuery, bot: Bot):
    draft = await get_draft(callback.from_user.id)
    draft = convert_old_buttons_to_rows(draft)

    sent_message = None
    rich_failed = False

    try:
        if draft.get("rich_mode"):
            rich_html = build_rich_html(draft)

            if rich_html:
                try:
                    sent_message = await bot.send_rich_message(
                        draft["channel_id"],
                        rich_message=InputRichMessage(html=rich_html),
                        reply_markup=post_keyboard(draft),
                        disable_notification=draft.get("silent", False),
                    )
                except Exception:
                    rich_failed = True

        if sent_message is None:
            if draft.get("media_file_id"):
                sent_message = await send_media_message(
                    bot,
                    draft["channel_id"],
                    draft,
                    build_caption(draft),
                    post_keyboard(draft),
                )
            else:
                sent_message = await bot.send_message(
                    draft["channel_id"],
                    build_caption(draft),
                    reply_markup=post_keyboard(draft),
                    disable_notification=draft.get("silent", False),
                )
    except Exception as error:
        await callback.answer(
            f"Publish failed: {str(error)[:150]}",
            show_alert=True,
        )
        return

    if draft.get("auto_delete_seconds"):
        asyncio.create_task(
            delete_later(
                bot,
                draft["channel_id"],
                sent_message.message_id,
                draft["auto_delete_seconds"],
            )
        )

    await delete_message_safe(
        bot,
        callback.message.chat.id,
        draft.get("preview_message_id"),
    )

    channel_title = draft.get("channel_title") or str(draft["channel_id"])
    rich_status = "ON" if draft.get("rich_mode") and not rich_failed else "OFF"

    await callback.message.edit_text(
        f"""━━━━━━━━━━━━━━━━━━━━
✅ <b>POST PUBLISHED</b>
━━━━━━━━━━━━━━━━━━━━

📺 <b>Channel:</b> {esc(channel_title)}
⏱ <b>Auto Delete:</b> {esc(human_time(draft.get('auto_delete_seconds')))}
✨ <b>Rich Mode:</b> {rich_status}""",
        reply_markup=published_menu(),
    )
    await callback.answer("Published ✅")


async def delete_later(bot, chat_id, message_id, seconds):
    await asyncio.sleep(seconds)

    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


def extract_media(message):
    if message.photo:
        return "photo", message.photo[-1].file_id

    if message.video:
        return "video", message.video.file_id

    if message.audio:
        return "audio", message.audio.file_id

    if message.document:
        return "document", message.document.file_id

    if message.animation:
        return "animation", message.animation.file_id

    return None


async def resolve_channel(bot, message):
    if message.forward_origin and getattr(message.forward_origin, "chat", None):
        chat = message.forward_origin.chat
        return chat.id, chat.title or str(chat.id)

    if message.text and message.text.startswith("@"):
        try:
            chat = await bot.get_chat(message.text.strip())
            return chat.id, chat.title or chat.username
        except Exception:
            return None, None

    return None, None


@router.message(F.text | F.photo | F.video | F.audio | F.document | F.animation)
async def input_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    draft = await get_draft(user_id)
    waiting_for = draft.get("waiting_for")

    if message.text and message.text.startswith("/"):
        return

    if waiting_for == "channel_add":
        channel_id, title = await resolve_channel(bot, message)

        if not channel_id:
            await message.reply(
                "❌ Send <code>@channelusername</code> or forward a message from the channel."
            )
            return

        try:
            member = await bot.get_chat_member(channel_id, bot.id)

            if member.status not in ("administrator", "creator"):
                raise ValueError("Bot is not an administrator")

            if not getattr(member, "can_post_messages", True):
                raise ValueError("Bot cannot post messages")
        except Exception:
            await message.reply(
                """❌ The bot is not an administrator in this channel, or it does not have the <b>Post Messages</b> permission.

Add the bot as an administrator first, then try again."""
            )
            return

        await db.channels.update_one(
            {"user_id": user_id, "chat_id": channel_id},
            {
                "$set": {
                    "user_id": user_id,
                    "chat_id": channel_id,
                    "title": title,
                }
            },
            upsert=True,
        )

        await save_draft(user_id, {"waiting_for": None})

        channels = await db.channels.find(
            {"user_id": user_id}
        ).to_list(100)

        await message.answer(
            f"✅ <b>Channel added:</b> {esc(title)}",
            reply_markup=channels_menu(channels),
        )
        return

    if waiting_for == "text":
        await save_draft(
            user_id,
            {"text": message.html_text or message.text or ""},
        )

        await delete_message_safe(bot, chat_id, message.message_id)
        await refresh_builder(bot, chat_id, user_id)
        return

    if waiting_for == "media":
        media = extract_media(message)

        if not media:
            await message.reply(
                "❌ Send a photo, video, audio file, document, or animation."
            )
            return

        await save_draft(
            user_id,
            {
                "media_type": media[0],
                "media_file_id": media[1],
            },
        )

        await delete_message_safe(bot, chat_id, message.message_id)
        await refresh_builder(bot, chat_id, user_id)
        return

    if waiting_for in ("inline_buttons", "caption_buttons"):
        button_rows = parse_button_rows(message.text)

        if not button_rows:
            await message.reply(
                """❌ Invalid button format.

Each line is one row.

💡 One button:
<code>Join Channel | https://t.me/telegram | green</code>

💡 Two buttons in one row:
<code>Visit Website | https://example.com | blue || Help | https://example.com | red</code>

💡 No color means a normal transparent button:
<code>Visit Website | https://example.com</code>"""
            )
            return

        if waiting_for == "inline_buttons":
            field = "button_rows"
            button_type = "Inline buttons"
            rich_mode = draft.get("rich_mode", False)
        else:
            field = "caption_button_rows"
            button_type = "Caption buttons"
            rich_mode = True

        row_count = len(button_rows)
        button_count = sum(len(row) for row in button_rows)

        await save_draft(
            user_id,
            {
                field: button_rows,
                "rich_mode": rich_mode,
            },
        )

        await delete_message_safe(bot, chat_id, message.message_id)
        await refresh_builder(bot, chat_id, user_id)

        await bot.send_message(
            chat_id,
            f"✅ <b>{button_type} saved</b>{NEWLINE}{NEWLINE}{button_count} buttons in {row_count} rows.",
        )
        return

    if waiting_for == "table":
        table = parse_table_input(message.text)

        if not table:
            await message.reply(
                """❌ You need at least 2 lines, and each line must contain at least 2 columns.

💡 Example:
<code>Product | Price</code>
<code>Apple | $1.00</code>"""
            )
            return

        await save_draft(user_id, {"table": table})

        await delete_message_safe(bot, chat_id, message.message_id)
        await refresh_builder(bot, chat_id, user_id)
        return

    if waiting_for == "save_title":
        title = (message.text or "Untitled Post").strip()[:60]

        current_draft = await get_draft(user_id)
        saved_post = dict(current_draft)
        saved_post.pop("_id", None)
        saved_post["title"] = title
        saved_post["saved_at"] = datetime.now(timezone.utc)

        await db.saved_posts.insert_one(saved_post)
        await save_draft(user_id, {"waiting_for": None})

        await delete_message_safe(bot, chat_id, message.message_id)
        await refresh_builder(bot, chat_id, user_id)

        await bot.send_message(
            chat_id,
            f"💾 <b>Post saved:</b> {esc(title)}",
        )
        return

    await message.answer(
        "Tap <b>Create Post</b> first.",
        reply_markup=main_menu(),
    )
