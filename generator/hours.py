"""Turn a simple OpenStreetMap opening_hours string into readable lines. Anything the parser does not understand is
returned as the original string, so nothing is invented."""
import re

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
LONG = {"Mo": "Mon", "Tu": "Tue", "We": "Wed", "Th": "Thu", "Fr": "Fri", "Sa": "Sat", "Su": "Sun"}


def _t(hm):
    h, m = hm.split(":")
    h, m = int(h), int(m)
    if h == 24 and m == 0:
        return "midnight"
    suffix = "am" if h < 12 or h >= 24 else "pm"
    hh = h % 12 or 12
    if h >= 24:
        hh = (h - 24) % 12 or 12
    return f"{hh}:{m:02d} {suffix}" if m else f"{hh} {suffix}"


def _days(spec):
    spec = spec.strip()
    if not spec:
        return "Every day"
    parts = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if "-" in chunk:
            a, b = chunk.split("-")
            if a in LONG and b in LONG:
                parts.append(f"{LONG[a]}-{LONG[b]}")
            else:
                return None
        elif chunk in LONG:
            parts.append(LONG[chunk])
        elif chunk == "PH":
            parts.append("Holidays")
        else:
            return None
    return ", ".join(parts)


def humanize(oh):
    """'Mo-Sa 11:00-21:30; Su 12:00-21:30' -> [('Mon-Sat', '11 am to 9:30 pm'), ('Sun', '12 pm to 9:30 pm')]
    Returns None when the string has constructs we do not handle (the caller then prints the raw string)."""
    if not oh:
        return None
    oh = oh.strip()
    if oh == "24/7":
        return [("Every day", "open 24 hours")]
    out = []
    for rule in oh.split(";"):
        rule = rule.strip()
        if not rule:
            continue
        m = re.match(r"^((?:(?:Mo|Tu|We|Th|Fr|Sa|Su|PH)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))?(?:,\s*)?)*)\s*(.*)$", rule)
        if not m:
            return None
        days, times = m.group(1), m.group(2).strip()
        d = _days(days)
        if d is None:
            return None
        if times.lower() in ("off", "closed"):
            out.append((d, "closed"))
            continue
        spans = []
        for span in times.split(","):
            span = span.strip()
            tm = re.match(r"^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$", span)
            if not tm:
                return None
            spans.append(f"{_t(tm.group(1))} to {_t(tm.group(2))}")
        out.append((d, ", ".join(spans)))
    return out or None
