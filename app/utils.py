import html

NEWLINE = chr(10)


def esc(text):
    return html.escape(text or "", quote=False)


def render_table(table):
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


def build_caption(draft):
    parts = []

    if draft.get("text"):
        parts.append(draft["text"])

    if draft.get("table"):
        rendered_table = render_table(draft["table"])
        if rendered_table:
            parts.append(rendered_table)

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
