import html

NEWLINE = chr(10)


def esc(text):
    return html.escape(text or "", quote=False)


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


def build_rich_html(draft):
    parts = []

    if draft.get("text"):
        parts.append(draft["text"])

    if draft.get("table"):
        rich_table = render_rich_table(draft["table"])
        if rich_table:
            parts.append(rich_table)

    buttons = draft.get("buttons") or []

    if buttons:
        button_tags = []

        for button in buttons:
            style = button.get("style") or "primary"

            if style not in ("primary", "success", "danger"):
                style = "primary"

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


def parse_button_input(raw_text):
    buttons = []

    for line in (raw_text or "").splitlines():
        if "|" not in line:
            continue

        parts = [part.strip() for part in line.split("|")]

        if len(parts) < 2:
            continue

        label = parts[0]
        url = parts[1]
        style = parts[2].lower() if len(parts) >= 3 else "primary"

        if style not in ("primary", "success", "danger"):
            style = "primary"

        if label and url.startswith(("http://", "https://")):
            buttons.append(
                {
                    "text": label,
                    "url": url,
                    "style": style,
                }
            )

    return buttons


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