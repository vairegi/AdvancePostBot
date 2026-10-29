import html


def esc(text):
    return html.escape(text or "", quote=False)


def render_table(table):
    headers = table.get("headers") or []
    rows = table.get("rows") or []
    matrix = ([headers] + rows) if headers else rows
    if not matrix:
        return ""

    columns = max(len(r) for r in matrix)
    normalized = [list(r) + [""] * (columns - len(r)) for r in matrix]
    widths = [max(len(str(row[c])) for row in normalized) for c in range(columns)]

    lines = []
    for i, row in enumerate(normalized):
        lines.append(" | ".join(str(row[c]).ljust(widths[c]) for c in range(columns)))
        if i == 0 and headers:
            lines.append("-+-".join("-" * w for w in widths))

    return "<pre>" + esc("
".join(lines)) + "</pre>"


def build_caption(draft):
    parts = []
    if draft.get("text"):
        parts.append(draft["text"])
    if draft.get("table"):
        rendered = render_table(draft["table"])
        if rendered:
            parts.append(rendered)
    return "

".join(p for p in parts if p)


def parse_table_input(raw):
    lines = [x.strip() for x in (raw or "").splitlines() if x.strip()]
    if len(lines) < 2:
        return None

    parsed = []
    for line in lines:
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 2:
            return None
        parsed.append(cells)

    return {"headers": parsed[0], "rows": parsed[1:]}


def human_time(seconds):
    seconds = int(seconds or 0)
    if not seconds:
        return "Permanent"

    for value, name in ((86400, "day"), (3600, "hour"), (60, "minute")):
        if seconds >= value:
            n = seconds // value
            return f"{n} {name}{'' if n == 1 else 's'}"

    return f"{seconds} seconds"