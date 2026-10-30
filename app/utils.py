import html

NEWLINE = chr(10)

COLOR_MAP = {
    "blue": "primary",
    "green": "success",
    "red": "danger",
    "primary": "primary",
    "success": "success",
    "danger": "danger",
}


def esc(text):
    return html.escape(text or "", quote=False)


def normalize_color(color):
    color = str(color or "blue").strip().lower()
    return COLOR_MAP.get(color, "primary")


def render_plain_table(table):
    headers = table.get("headers") or []
    rows = table.get("rows") or []
    matrix = ([headers] + rows) if headers else rows

    if not matrix:
        return ""

    columns = max(len(row) for row in matrix)
    normalized = [list(row) + [""] * (columns - len(row)) for row in matrix]

    widths = [
        max(len(str(row[column])) for row in normalized)
        for column in range(columns)
    ]

    lines = []

    for index, row in enumerate(normalized):
        line = " | ".join(
            str(row[column]).ljust(widths[column])
            for column in range(columns)
        )
        lines.append(line)

        if index == 0 and headers:
            separator = "-+-".join("-" * width for width in widths)
            lines.append(separator)

    table_text = NEWLINE.join(lines)
    return "<pre>" + esc(table_text) + "</pre>"


def render_rich_table(table):
    headers = table.get("headers") or []
    rows = table.get("rows") or []

    if not headers and not rows:
        return ""

    parts = ["<table>"]

    if headers:
        parts.append("<tr>")

        for header in headers:
            parts.append("<th>" + esc(str(header)) + "</th>")

        parts.append("</tr>")

    for row in rows:
        parts.append("<tr>")

        for cell in row:
            parts.append("<td>" + esc(str(cell)) + "</td>")

        parts.append("</tr>")

    parts.append("</table>")
    return "".join(parts)


def build_caption(draft):
    parts = []

    if draft.get("text"):
        parts.append(draft["text"])

    if draft.get("table"):
        rendered_table = render_plain_table(draft["table"])
        if rendered_table:
            parts.append(rendered_table)

    return NEWLINE.join(part for part in parts if part)


def build_caption_button_html(caption_button_rows):
    parts = []

    for row in caption_button_rows or []:
        if not row:
            continue

        button_tags = []

        for button in row:
            style = normalize_color(button.get("color"))

            button_tags.append(
                '<tg-button type="url" url="'
                + esc(button["url"])
                + '" style="'
                + style
                + '">'
                + esc(button["text"])
                + "</tg-button>"
            )

        parts.append(
            "<tg-button-row>" + "".join(button_tags) + "</tg-button-row>"
        )

    return NEWLINE.join(part for part in parts if part)


def build_rich_html(draft):
    parts = []

    if draft.get("text"):
        parts.append(draft["text"])

    if draft.get("table"):
        rich_table = render_rich_table(draft["table"])
        if rich_table:
            parts.append(rich_table)

    caption_buttons = build_caption_button_html(
        draft.get("caption_button_rows")
    )

    if caption_buttons:
        parts.append(caption_buttons)

    return NEWLINE.join(part for part in parts if part)


def parse_table_input(raw_text):
    lines = [
        line.strip()
        for line in (raw_text or "").splitlines()
        if line.strip()
    ]

    if len(lines) < 2:
        return None

    parsed_rows = []

    for line in lines:
        cells = [cell.strip() for cell in line.split("|")]

        if len(cells) < 2:
            return None

        parsed_rows.append(cells)

    return {
        "headers": parsed_rows[0],
        "rows": parsed_rows[1:],
    }


def parse_button_rows(raw_text):
    button_rows = []

    for line in (raw_text or "").splitlines():
        line = line.strip()

        if not line:
            continue

        row = []

        for button_text in line.split("||"):
            button_text = button_text.strip()

            if not button_text:
                continue

            parts = [part.strip() for part in button_text.split("|")]

            if len(parts) < 2:
                continue

            label = parts[0]
            url = parts[1]
            color = parts[2] if len(parts) >= 3 else "blue"

            if not label:
                continue

            if not url.startswith(("http://", "https://")):
                continue

            row.append(
                {
                    "text": label,
                    "url": url,
                    "color": normalize_color(color),
                }
            )

        if row:
            button_rows.append(row)

    return button_rows


def convert_old_buttons_to_rows(draft):
    if draft.get("button_rows") or draft.get("caption_button_rows"):
        return draft

    old_buttons = draft.get("buttons") or []

    if not old_buttons:
        return draft

    per_row = int(draft.get("buttons_per_row") or 2)
    button_rows = []

    for index in range(0, len(old_buttons), per_row):
        row = []

        for button in old_buttons[index:index + per_row]:
            row.append(
                {
                    "text": button.get("text", "Button"),
                    "url": button.get("url", "https://t.me/telegram"),
                    "color": normalize_color(button.get("style", "blue")),
                }
            )

        button_rows.append(row)

    draft["button_rows"] = button_rows
    return draft


def human_time(seconds):
    seconds = int(seconds or 0)

    if not seconds:
        return "Permanent"

    time_units = (
        (86400, "day"),
        (3600, "hour"),
        (60, "minute"),
    )

    for unit_seconds, unit_name in time_units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            suffix = "" if count == 1 else "s"
            return f"{count} {unit_name}{suffix}"

    return f"{seconds} seconds"