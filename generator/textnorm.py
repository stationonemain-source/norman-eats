"""Shared normalisers: names and street addresses, so every join in the pipeline keys the same way."""
import re

STREET_ABBR = {
    "avenue": "ave", "av": "ave", "street": "st", "boulevard": "blvd", "parkway": "pkwy", "pky": "pkwy", "drive": "dr",
    "road": "rd", "highway": "hwy", "place": "pl", "lane": "ln", "court": "ct", "circle": "cir", "terrace": "ter",
    "north": "n", "south": "s", "east": "e", "west": "w", "northwest": "nw", "northeast": "ne", "southwest": "sw",
    "southeast": "se",
}
ORDINAL = {"first": "1st", "second": "2nd", "third": "3rd", "fourth": "4th", "fifth": "5th", "sixth": "6th",
           "seventh": "7th", "eighth": "8th", "ninth": "9th", "tenth": "10th", "twelfth": "12th",
           "twenty-fourth": "24th", "thirty-sixth": "36th"}
SUFFIX_WORDS = {"n", "s", "e", "w", "nw", "ne", "sw", "se", "ave", "st", "blvd", "pkwy", "dr", "rd", "hwy", "pl", "ln",
                "ct", "cir", "ter", "way"}
NAME_STOP = {"the", "llc", "inc", "co", "ltd", "of", "norman", "and", "a", "at", "restaurant", "bar", "grill", "cafe",
             "kitchen", "company", "house", "ok", "oklahoma", "lounge", "pub", "bistro", "deli", "eatery", "cantina",
             "steakhouse", "brewing", "brewery", "pizza", "sushi", "mexican", "italian", "thai", "chinese", "japanese",
             "indian", "cuisine", "food", "foods", "store", "shop", "no", "ii", "iii", "on", "in"}


def simplify_name(s):
    s = (s or "").lower().replace("’", "'").replace("`", "'")
    s = re.sub(r"#\s*\d+|\bno\.?\s*\d+\b|\bstore\s*\d+\b", " ", s)   # chain unit numbers
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    s = re.sub(r"'s\b", "s", s).replace("'", "")
    return [t for t in s.split() if t]


def name_key(s):
    toks = [t for t in simplify_name(s) if t not in NAME_STOP]
    return " ".join(toks) or " ".join(simplify_name(s))


def _stem(t):
    return t[:-1] if len(t) > 3 and t.endswith("s") else t


def name_sim(a, b):
    ta, tb = simplify_name(a), simplify_name(b)
    if ta and tb and "".join(ta) == "".join(tb):        # "Isushi" vs "I Sushi"
        return 1.0
    A, B = {_stem(t) for t in ta} - NAME_STOP, {_stem(t) for t in tb} - NAME_STOP
    if not A or not B:
        A, B = {_stem(t) for t in ta}, {_stem(t) for t in tb}
    if not A or not B:
        return 0.0
    inter = len(A & B)
    if not inter:
        # one-letter spelling slips ("Baracuda" / "Barracuda"): a near-identical token counts as shared
        for x in A:
            for y in B:
                if len(x) >= 6 and len(y) >= 6 and (x in y or y in x or _edit1(x, y)):
                    inter += 1
                    break
    return inter / min(len(A), len(B)) if inter else 0.0


def _edit1(x, y):
    if abs(len(x) - len(y)) > 1:
        return False
    if len(x) == len(y):
        return sum(1 for p, q in zip(x, y) if p != q) == 1
    s, l = (x, y) if len(x) < len(y) else (y, x)
    for i in range(len(l)):
        if l[:i] + l[i + 1:] == s:
            return True
    return False


TYPO = {"lindsay": "lindsey", "tecumesh": "tecumseh", "techumseh": "tecumseh", "opprotunity": "opportunity",
        "chautaqua": "chautauqua", "mt": "mount", "avew": "ave", "constitutio": "constitution"}
UNIT_WORDS = {"ste", "suite", "unit", "bldg", "rm", "room", "spc", "space", "apt"}


def street_key(street):
    """'2627 Classen Blvd' / '2627 CLASSEN BOULEVARD' / '2627 N Classen Blvd. Ste 104' / '2627 Classen #104' -> ('2627', 'classen')
    The unit is dropped on purpose: the DOOR is the join key, the unit only separates neighbours at the same door."""
    s = (street or "").lower().replace(".", " ").replace(",", " ")
    s = re.sub(r"#\s*[\w-]+", " ", s)
    s = re.sub(r"\b(?:e|w|n|s)?\s*(?:st|state)\s+(?:hwy|highway)\s*", " hwy ", s)   # 'E State Highway 9' / 'E St Hwy 9' -> 'hwy 9'
    s = re.sub(r"\s+", " ", s).strip()
    m = re.match(r"^(\d+)(?:\s*[/-]\s*\d+)?\s*(?:1/2\s*)?(.*)$", s)
    if not m:
        return ("", re.sub(r"\W+", "", s))
    num, rest = m.group(1), m.group(2)
    toks = []
    for t in rest.split():
        if t in UNIT_WORDS:
            break
        t = TYPO.get(t, t)
        t = STREET_ABBR.get(ORDINAL.get(t, t), ORDINAL.get(t, t))
        toks.append(t)
    core = [t for t in toks if t not in SUFFIX_WORDS]
    if not core and toks:
        core = toks[:1]
    return (num, " ".join(core))


SMALL = {"and", "of", "the", "at", "on", "in", "de", "la", "el", "y", "a", "&"}
FIXUPS = [(r"\bBbq\b", "BBQ"), (r"\bLlc\b", "LLC"), (r"\bNced\b", "NCED"), (r"\bOu\b", "OU"), (r"\bBj's\b", "BJ's"),
          (r"\bAmc\b", "AMC"), (r"\bViii\b", "VIII"), (r"\bIi\b", "II"), (r"\bNw\b", "NW"), (r"\bNe\b", "NE"),
          (r"\bSw\b", "SW"), (r"\bSe\b", "SE"), (r"\bP\.f\.", "P.F."), (r"\bLtd\b", "Ltd"), (r"\bUs\b", "US")]


def title_name(s):
    """Portal names are often ALL CAPS. Keep names that already mix case; title-case the shouting ones."""
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if s and s == s.upper() and any(c.isalpha() for c in s):
        words = []
        for i, w in enumerate(s.lower().split()):
            if w in SMALL and i:
                words.append(w)
                continue
            w = "-".join(p[:1].upper() + p[1:] for p in w.split("-"))
            parts = w.split("'")
            w = "'".join(p[:1].upper() + p[1:] if (j == 0 or len(p) > 1) else p for j, p in enumerate(parts))
            w = re.sub(r"^Mc(\w)", lambda m: "Mc" + m.group(1).upper(), w)
            words.append(w)
        s = " ".join(words)
        for pat, rep in FIXUPS:
            s = re.sub(pat, rep, s)
    return s
