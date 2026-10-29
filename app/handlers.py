import asyncio
from datetime import datetime, timezone
from bson import ObjectId

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import db
from app.keyboards import (
    main_menu,
    builder_menu,
    back_to_builder,
    channels_menu,
    channel_select_menu,
    autodelete_menu,
    media_menu,
    saved_posts_menu,
    button_layout_menu,
    confirm_publish,
    published_menu,
)
from app.utils import build_caption, parse_table_input, human_time, esc

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
    await db.drafts.update_one(
        {"user_id": user_id},
        {"$set": update, "$unset": {"waiting_for": ""}},
        upsert=True,
    )


def builder_text(draft):
    return (
        "🛠 <b>Advanced Post Builder</b>

"
        "अपना post step-by-step बनाइए। हर option में simple instructions मिलेंगे।

"
        f"📝 <b>Caption:</b> {'Added' if draft.get('text') else 'Not added'}
"
        f"🖼 <b>Media:</b> {esc(draft.get('media_type') or 'No media')}
"
        f"🔗 <b>Buttons:</b> {len(draft.get('buttons') or [])}
"
        f"📊 <b>Table:</b> {'Yes' if draft.get('table') else 'No'}
"
        f"📺 <b>Channel:</b> {esc(draft.get('channel_title') or 'Not selected')}
"
        f"⏱ <b>Auto Delete:</b> {esc(human_time(draft.get('auto_delete_seconds')))}
"
        f"🔕 <b>Silent:</b> {'ON' if draft.get('silent') else 'OFF'}

"
        "<i>Tip: Caption -> Media/Buttons/Table -> Channel -> Preview -> Publish</i>"
    )


async def show_builder(callback_or_message, user_id):
    draft = await get_draft(user_id)
    text = builder_text(draft)
    keyboard = builder_menu(draft)

    if isinstance(callback_or_message, CallbackQuery):
        try:
            await callback_or_message.message.edit_text(
                text,
                reply_markup=keyboard,
            )
        except TelegramBadRequest:
            await callback_or_message.message.answer(
                text,
                reply_markup=keyboard,
            )
    else:
        await callback_or_message.answer(text, reply_markup=keyboard)


HELP_TEXT = (
    "❓ <b>How to Use</b>

"
    "<b>1. Channel जोड़ें</b>
"
    "Bot को channel admin बनाएं और Post Messages permission दें।
"
    "फिर <b>My Channels → Add Channel</b> में <code>@channelusername</code> भेजें "
    "या channel से कोई message forward करें।

"
    "<b>2. Caption</b>
"
    "Telegram HTML support है:
"
    "<code>&lt;b&gt;Bold&lt;/b&gt;</code>, "
    "<code>&lt;i&gt;Italic&lt;/i&gt;</code>, "
    "<code>&lt;u&gt;Underline&lt;/u&gt;</code>, "
    "<code>&lt;s&gt;Strike&lt;/s&gt;</code>, "
    "<code>&lt;code&gt;Code&lt;/code&gt;</code>, "
    "<code>&lt;a href="https://example.com"&gt;Link&lt;/a&gt;</code>

"
    "<b>3. Buttons</b>
"
    "हर button एक line में भेजें:
"
    "<code>Button Text | https://example.com</code>

"
    "उदाहरण:
"
    "<code>Visit Website | https://example.com</code>
"
    "<code>Join Channel | https://t.me/telegram</code>

"
    "फिर 1, 2 या 3 buttons per row चुनें।

"
    "<b>4. Table</b>
"
    "पहली line header है, बाकी lines rows हैं।
"
    "<code>Product | Price</code>
"
    "<code>Apple | ₹100</code>
"
    "<code>Mango | ₹120</code>

"
    "<b>5. Auto Delete</b>
"
    "Permanent, 1 minute, 10 minutes, 1 hour या 24 hours चुनें।

"
    "<b>6. Publish</b>
"
    "Channel चुनें, Preview देखें, फिर Publish Now दबाएं।"
)


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
        "👋 <b>Welcome to Advanced Post Creator Bot!</b>

"
        "इस bot से आप अपने Telegram channels के लिए professional posts बना सकते हैं।

"
        "🟢 <b>Create Post</b> — नया post बनाएं
"
        "📺 <b>My Channels</b> — अपने channels जोड़ें
"
        "💾 <b>Saved Posts</b> — पुराने posts reuse करें
"
        "❓ <b>Help</b> — full guide देखें",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(HELP_TEXT, reply_markup=back_to_builder())


@router.callback_query(F.data == "menu:main")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 <b>Main Menu</b>

नीचे से option चुनें:",
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
    await show_builder(callback, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "menu:channels")
async def channels_callback(callback: CallbackQuery):
    channels = await db.channels.find(
        {"user_id": callback.from_user.id}
    ).to_list(100)

    await callback.message.edit_text(
        "📺 <b>My Channels</b>

Channel चुनें या नया channel add करें।",
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
            "💾 <b>Saved Posts</b>

अभी कोई saved post नहीं है।

"
            "Post Builder में <b>💾 Save Post</b> दबाएं।",
            reply_markup=back_to_builder(),
        )
    else:
        await callback.message.edit_text(
            "💾 <b>Saved Posts</b>

Post select करें; यह builder में load हो जाएगा।",
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
        await callback.answer("Post नहीं मिला।", show_alert=True)
        return

    post["user_id"] = callback.from_user.id
    post["waiting_for"] = None

    await db.drafts.replace_one(
        {"user_id": callback.from_user.id},
        post,
        upsert=True,
    )

    await show_builder(callback, callback.from_user.id)
    await callback.answer("Post loaded ✅")


@router.callback_query(F.data == "ch:add")
async def add_channel_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "channel_add"})

    await callback.message.edit_text(
        "➕ <b>Add Channel</b>

"
        "<code>@channelusername</code> भेजें या private channel से कोई message forward करें।

"
        "⚠️ Bot को पहले channel में Admin बनाएं और Post Messages permission दें।",
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
        await callback.answer("Channel नहीं मिला।", show_alert=True)
        return

    await save_draft(
        callback.from_user.id,
        {
            "channel_id": chat_id,
            "channel_title": channel.get("title"),
        },
    )

    await show_builder(callback, callback.from_user.id)
    await callback.answer("Channel selected ✅")


@router.callback_query(F.data == "edit:text")
async def edit_text_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "text"})

    await callback.message.edit_text(
        "📝 <b>Caption / Text भेजें</b>

"
        "Telegram HTML support है:
"
        "<code>&lt;b&gt;Bold&lt;/b&gt;</code>
"
        "<code>&lt;i&gt;Italic&lt;/i&gt;</code>
"
        "<code>&lt;u&gt;Underline&lt;/u&gt;</code>
"
        "<code>&lt;a href="https://example.com"&gt;Link&lt;/a&gt;</code>",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:media")
async def edit_media_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)
    await save_draft(callback.from_user.id, {"waiting_for": "media"})

    await callback.message.edit_text(
        "🖼 <b>Media भेजें</b>

"
        "Photo, Video, Audio, Document या Animation भेजें।",
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

    await show_builder(callback, callback.from_user.id)
    await callback.answer("Media removed ✅")


@router.callback_query(F.data == "edit:buttons")
async def edit_buttons_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "buttons"})

    await callback.message.edit_text(
        "🔗 <b>Inline Buttons जोड़ें</b>

"
        "हर button एक line में भेजें:
"
        "<code>Button Text | https://example.com</code>

"
        "उदाहरण:
"
        "<code>Visit Website | https://example.com</code>
"
        "<code>Join Channel | https://t.me/telegram</code>",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("btnrow:"))
async def button_row_callback(callback: CallbackQuery):
    per_row = int(callback.data.split(":", 1)[1])

    await save_draft(
        callback.from_user.id,
        {"buttons_per_row": per_row},
    )

    await show_builder(callback, callback.from_user.id)
    await callback.answer(f"{per_row} buttons per row saved ✅")


@router.callback_query(F.data == "edit:table")
async def edit_table_callback(callback: CallbackQuery):
    await save_draft(callback.from_user.id, {"waiting_for": "table"})

    await callback.message.edit_text(
        "📊 <b>Table बनाएं</b>

"
        "पहली line header है, बाकी lines rows हैं।
"
        "Columns को <code>|</code> से अलग करें।

"
        "उदाहरण:
"
        "<code>Product | Price</code>
"
        "<code>Apple | ₹100</code>
"
        "<code>Mango | ₹120</code>",
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
        "📺 <b>Post Channel चुनें</b>",
        reply_markup=channel_select_menu(channels, draft.get("channel_id")),
    )
    await callback.answer()


@router.callback_query(F.data == "edit:autodelete")
async def autodelete_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "⏱ <b>Auto Delete चुनें</b>

"
        "Permanent चुनने पर post delete नहीं होगा।",
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

    await show_builder(callback, callback.from_user.id)
    await callback.answer("Auto delete set ✅")


@router.callback_query(F.data == "edit:silent")
async def toggle_silent_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    await save_draft(
        callback.from_user.id,
        {"silent": not draft.get("silent", False)},
    )

    await show_builder(callback, callback.from_user.id)
    await callback.answer("Silent mode updated ✅")


@router.callback_query(F.data == "post:reset")
async def reset_post_callback(callback: CallbackQuery):
    draft = db.empty_draft()
    draft["user_id"] = callback.from_user.id

    await db.drafts.replace_one(
        {"user_id": callback.from_user.id},
        draft,
        upsert=True,
    )

    await show_builder(callback, callback.from_user.id)
    await callback.answer("New post started ✅")


def post_keyboard(draft):
    keyboard = InlineKeyboardBuilder()

    for button in draft.get("buttons") or []:
        keyboard.button(
            text=button["text"],
            url=button["url"],
        )

    if draft.get("buttons"):
        keyboard.adjust(draft.get("buttons_per_row") or 2)
        return keyboard.as_markup()

    return None


@router.callback_query(F.data == "post:preview")
async def preview_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)
    caption = build_caption(draft) or "<i>(No caption)</i>"
    keyboard = post_keyboard(draft)

    try:
        if draft.get("media_file_id"):
            await send_media(callback.message, draft, caption, keyboard)
        else:
            await callback.message.answer(
                caption,
                reply_markup=keyboard,
            )

        await callback.answer("Preview नीचे भेजा गया ✅")
    except TelegramBadRequest as error:
        await callback.answer(
            f"Preview error: {error.message}",
            show_alert=True,
        )


async def send_media(message, draft, caption, keyboard):
    file_id = draft["media_file_id"]
    media_type = draft.get("media_type")

    if media_type == "photo":
        await message.answer_photo(
            file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    elif media_type == "video":
        await message.answer_video(
            file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    elif media_type == "audio":
        await message.answer_audio(
            file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    elif media_type == "document":
        await message.answer_document(
            file_id,
            caption=caption,
            reply_markup=keyboard,
        )
    elif media_type == "animation":
        await message.answer_animation(
            file_id,
            caption=caption,
            reply_markup=keyboard,
        )


@router.callback_query(F.data == "post:save")
async def save_post_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    if not (
        draft.get("text")
        or draft.get("media_file_id")
        or draft.get("table")
    ):
        await callback.answer(
            "पहले caption, media या table add करें।",
            show_alert=True,
        )
        return

    await save_draft(callback.from_user.id, {"waiting_for": "save_title"})

    await callback.message.edit_text(
        "💾 <b>Post का नाम भेजें</b>

"
        "यह नाम केवल आपके Saved Posts में दिखेगा।

"
        "उदाहरण: <code>Daily Offer Post</code>",
        reply_markup=back_to_builder(),
    )
    await callback.answer()


@router.callback_query(F.data == "post:publish")
async def publish_callback(callback: CallbackQuery):
    draft = await get_draft(callback.from_user.id)

    if not draft.get("channel_id"):
        await callback.answer(
            "पहले channel select करें।",
            show_alert=True,
        )
        return

    if not (
        draft.get("text")
        or draft.get("media_file_id")
        or draft.get("table")
    ):
        await callback.answer(
            "पहले caption, media या table add करें।",
            show_alert=True,
        )
        return

    channel_title = draft.get("channel_title") or str(draft["channel_id"])
    auto_delete = human_time(draft.get("auto_delete_seconds"))

    await callback.message.edit_text(
        "🚀 <b>Publish Confirmation</b>

"
        f"📺 Channel: <b>{esc(channel_title)}</b>
"
        f"⏱ Auto Delete: <b>{esc(auto_delete)}</b>

"
        "क्या आप इस post को publish करना चाहते हैं?",
        reply_markup=confirm_publish(channel_title, auto_delete),
    )
    await callback.answer()


@router.callback_query(F.data == "post:publish_confirm")
async def publish_confirm_callback(callback: CallbackQuery, bot: Bot):
    draft = await get_draft(callback.from_user.id)
    caption = build_caption(draft)
    keyboard = post_keyboard(draft)

    try:
        if draft.get("media_file_id"):
            sent_message = await send_media_to_chat(
                bot,
                draft["channel_id"],
                draft,
                caption,
                keyboard,
            )
        else:
            sent_message = await bot.send_message(
                draft["channel_id"],
                caption,
                reply_markup=keyboard,
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

    channel_title = draft.get("channel_title") or str(draft["channel_id"])

    await callback.message.edit_text(
        "✅ <b>Post published successfully!</b>

"
        f"📺 Channel: <b>{esc(channel_title)}</b>
"
        f"⏱ Auto Delete: <b>{esc(human_time(draft.get('auto_delete_seconds')))}</b>",
        reply_markup=published_menu(),
    )
    await callback.answer("Published ✅")


async def send_media_to_chat(bot, chat_id, draft, caption, keyboard):
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
    draft = await get_draft(user_id)
    waiting_for = draft.get("waiting_for")

    if message.text and message.text.startswith("/"):
        return

    if waiting_for == "channel_add":
        chat_id, title = await resolve_channel(bot, message)

        if not chat_id:
            await message.reply(
                "❌ <code>@channelusername</code> भेजें या channel से message forward करें।"
            )
            return

        try:
            member = await bot.get_chat_member(chat_id, bot.id)

            if member.status not in ("administrator", "creator"):
                raise ValueError("Bot is not admin")

            if not getattr(member, "can_post_messages", True):
                raise ValueError("Bot cannot post messages")
        except Exception:
            await message.reply(
                "❌ Bot इस channel में admin नहीं है या "
                "<b>Post Messages</b> permission नहीं है।"
            )
            return

        await db.channels.update_one(
            {"user_id": user_id, "chat_id": chat_id},
            {
                "$set": {
                    "user_id": user_id,
                    "chat_id": chat_id,
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

        updated_draft = await get_draft(user_id)

        await message.answer(
            "✅ Caption saved। अब अगला step चुनें।",
            reply_markup=builder_menu(updated_draft),
        )
        return

    if waiting_for == "media":
        media = extract_media(message)

        if not media:
            await message.reply(
                "❌ Photo, Video, Audio, Document या Animation भेजें।"
            )
            return

        await save_draft(
            user_id,
            {
                "media_type": media[0],
                "media_file_id": media[1],
            },
        )

        updated_draft = await get_draft(user_id)

        await message.answer(
            "✅ Media saved।",
            reply_markup=builder_menu(updated_draft),
        )
        return

    if waiting_for == "buttons":
        buttons = []

        for line in (message.text or "").splitlines():
            if "|" not in line:
                continue

            label, url = [part.strip() for part in line.split("|", 1)]

            if label and url.startswith(("http://", "https://")):
                buttons.append({"text": label, "url": url})

        if not buttons:
            await message.reply(
                "❌ Format सही नहीं है।

"
                "<code>Button Text | https://example.com</code>"
            )
            return

        await save_draft(user_id, {"buttons": buttons})

        await message.answer(
            f"✅ {len(buttons)} buttons added।

"
            "अब चुनें कि एक row में कितने buttons दिखें:",
            reply_markup=button_layout_menu(),
        )
        return

    if waiting_for == "table":
        table = parse_table_input(message.text)

        if not table:
            await message.reply(
                "❌ कम से कम 2 lines और हर line में 2 columns चाहिए।

"
                "<code>Product | Price</code>
"
                "<code>Apple | ₹100</code>"
            )
            return

        await save_draft(user_id, {"table": table})

        updated_draft = await get_draft(user_id)

        await message.answer(
            "✅ Table saved।",
            reply_markup=builder_menu(updated_draft),
        )
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

        updated_draft = await get_draft(user_id)

        await message.answer(
            f"💾 <b>Post saved:</b> {esc(title)}",
            reply_markup=builder_menu(updated_draft),
        )
        return

    await message.answer(
        "पहले <b>Create Post</b> पर click करें।",
        reply_markup=main_menu(),
    )