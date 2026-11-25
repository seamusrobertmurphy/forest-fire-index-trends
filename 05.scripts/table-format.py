"""Gives every data table in a rendered Word manuscript one uniform look.

Run on the rendered file after forestry-layout.py and before landscape-tables.py:
  python3 ../05.scripts/table-format.py manuscript-2026-11-24.docx

Quarto builds the flextable tables (2 to 5 and the supplement's S1 to S4) and the one kable pipe
table (Table 1, left a pipe table so pandoc resolves the citations in its cells) with different
fonts, sizes, borders and spacing, and the R side cannot reach the pipe table at all. This pass
rewrites all of them the same way, so the submission's tables match (Seamus, 2026-11-24):

  font      Arial on every run of the table block, the caption included
  size      9 pt in the data grid (the caption keeps its own size)
  header    bold, centred
  body      a text column left, a column of values only centred
  cells     centred top to bottom, with a taller uniform top and bottom margin so the rows are even
  columns   autofit, so a column with more content is given more width
  borders   one line above the header, one under it and one below the last row, nothing else

The real grid sits nested inside a one-cell wrapper table that carries the "Table N." caption, so
each data table is found by that caption and formatted on its inner table. Equation tables (three
columns, no caption) and figure tables (a drawing, a "Figure" caption) carry no "Table N." caption
and are left alone. Which tables turn to landscape is landscape-tables.py's job, run after this.
"""
import copy, os, re, shutil, sys, tempfile, zipfile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
q = lambda tag: f"{{{W}}}{tag}"

BORDER_SZ = "8"        # eighths of a point, so 1 pt
BORDER_CLR = "000000"  # black
PAD = 60               # twips (3 pt) of top and bottom cell margin, for an even, readable row height
SIZE = 18              # half-points, so 9 pt

cap_re = re.compile(r"^Table[\s\xa0  ]+S?[\s\xa0  ]*\d+[.:]")

PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
    "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
    "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind",
    "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline",
    "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing", "w",
    "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl",
    "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"]
TCPR_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar",
    "textDirection", "tcFit", "vAlign", "hideMark", "headers", "cellIns", "cellDel", "cellMerge"]
TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
    "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook",
    "tblCaption", "tblDescription"]


def place(parent, child, order):
    """Drop any existing element of the same tag, then insert child at its schema position."""
    tag = etree.QName(child).localname
    for e in parent.findall(q(tag)):
        parent.remove(e)
    idx = order.index(tag)
    pos = len(parent)
    for i, e in enumerate(parent):
        name = etree.QName(e).localname
        if (order.index(name) if name in order else 999) > idx:
            pos = i
            break
    parent.insert(pos, child)
    return child


def ensure(parent, tag, order):
    """Return the parent's child of this tag, adding it at its schema position when absent."""
    e = parent.find(q(tag))
    if e is None:
        e = place(parent, etree.Element(q(tag)), order)
    return e


def text(el):
    return "".join(t.text or "" for t in el.iter(q("t")))


UNITS = {"db", "%", "na"}


def numeric(tok):
    t = tok.strip().strip("*").replace(" ", "").replace(" ", "").replace(",", "")
    t = t.replace("–", "-").replace("−", "-")
    if t == "":
        return None
    try:
        float(t)
        return True
    except ValueError:
        return False


def cell_is_value(s):
    # True if every token is a number (ignoring units and significance stars), with at least one number present.
    s = s.strip()
    if s == "":
        return None
    seen = False
    for tok in re.split(r"[\s  ,()]+", s):
        if tok == "" or tok.strip("*").lower() in UNITS:
            continue
        r = numeric(tok)
        if r is False:
            return False
        seen = seen or (r is True)
    return seen


def is_value_column(cells):
    saw = False
    for s in cells:
        v = cell_is_value(s)
        if v is False:
            return False
        saw = saw or (v is True)
    return saw


# Superscript characters Arial has no glyph for (it draws a .notdef box). The precomposed character is
# replaced by its plain character raised as a real superscript, which Arial can draw. 1, 2 and 3 are left
# alone, since Arial carries U+00B9/B2/B3 and they render, e.g. in km².
SUP = {"⁰": "0", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8",
       "⁹": "9", "⁺": "+", "⁻": "-", "ⁿ": "n", "ⁱ": "i"}


def split_superscripts(r):
    t = r.find(q("t"))
    if t is None or not any(c in SUP for c in (t.text or "")):
        return
    segs, buf, cur = [], "", False
    for c in (t.text or ""):
        sup = c in SUP
        if sup != cur and buf:
            segs.append((buf, cur)); buf = ""
        cur = sup; buf += SUP.get(c, c)
    if buf:
        segs.append((buf, cur))
    parent = r.getparent()
    at = parent.index(r)
    parent.remove(r)
    for k, (txt, is_sup) in enumerate(segs):
        nr = copy.deepcopy(r)
        nt = nr.find(q("t"))
        nt.text = txt
        nt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        if is_sup:
            rpr = nr.find(q("rPr"))
            if rpr is None:
                rpr = etree.Element(q("rPr")); nr.insert(0, rpr)
            va = etree.Element(q("vertAlign")); va.set(q("val"), "superscript")
            place(rpr, va, RPR_ORDER)
        parent.insert(at + k, nr)


def set_run(r, size=None, bold=None):
    rpr = r.find(q("rPr"))
    if rpr is None:
        rpr = etree.Element(q("rPr"))
        r.insert(0, rpr)
    rf = ensure(rpr, "rFonts", RPR_ORDER)
    for a in ("ascii", "hAnsi", "cs", "eastAsia"):
        rf.set(q(a), "Arial")
    if size is not None:
        for tag in ("sz", "szCs"):
            ensure(rpr, tag, RPR_ORDER).set(q("val"), str(size))
    if bold is not None:
        for tag in ("b", "bCs"):
            ensure(rpr, tag, RPR_ORDER).set(q("val"), "true" if bold else "false")


def set_jc(p, val):
    pp = p.find(q("pPr"))
    if pp is None:
        pp = etree.Element(q("pPr"))
        p.insert(0, pp)
    jc = etree.Element(q("jc"))
    jc.set(q("val"), val)
    place(pp, jc, PPR_ORDER)


def format_cell(tc, is_header, jc_val):
    for r in tc.iter(q("r")):
        set_run(r, size=SIZE, bold=(True if is_header else None))
    for p in tc.findall(q("p")):
        set_jc(p, jc_val)
    tcpr = tc.find(q("tcPr"))
    if tcpr is None:
        tcpr = etree.Element(q("tcPr"))
        tc.insert(0, tcpr)
    for b in tcpr.findall(q("tcBorders")):
        tcpr.remove(b)
    if is_header:
        tb = etree.Element(q("tcBorders"))
        bot = etree.SubElement(tb, q("bottom"))
        bot.set(q("val"), "single"); bot.set(q("sz"), BORDER_SZ); bot.set(q("space"), "0"); bot.set(q("color"), BORDER_CLR)
        place(tcpr, tb, TCPR_ORDER)
    tm = ensure(tcpr, "tcMar", TCPR_ORDER)
    for side in ("top", "bottom"):
        e = tm.find(q(side))
        if e is None:
            e = etree.SubElement(tm, q(side))
        e.set(q("w"), str(PAD)); e.set(q("type"), "dxa")
    ensure(tcpr, "vAlign", TCPR_ORDER).set(q("val"), "center")


def format_table(outer):
    inner = next((t for t in outer.iter(q("tbl")) if t is not outer), outer)
    rows = inner.findall(q("tr"))
    if not rows:
        return 0
    hdr = [i for i, tr in enumerate(rows)
           if tr.find(q("trPr")) is not None and tr.find(q("trPr")).find(q("tblHeader")) is not None]
    if not hdr:
        hdr = [0]
    body = [i for i in range(len(rows)) if i not in hdr]
    ncol = max(len(tr.findall(q("tc"))) for tr in rows)
    value = []
    for j in range(ncol):
        cells = [text(rows[i].findall(q("tc"))[j]) for i in body if j < len(rows[i].findall(q("tc")))]
        value.append(is_value_column(cells))
    tp = inner.find(q("tblPr"))
    ensure(tp, "tblLayout", TBLPR_ORDER).set(q("type"), "autofit")
    tw = ensure(tp, "tblW", TBLPR_ORDER)
    tw.set(q("type"), "pct"); tw.set(q("w"), "5000")
    # A pipe table (Table 1) carries a fixed column grid, and the renderer keeps those widths even under
    # autofit, so a short grid width leaves a column a sliver that breaks words. The widths are reset in
    # proportion to each column's longest cell, which gives the content-led layout autofit should. Flextable
    # tables carry no grid and are sized from content already, so this leaves them alone.
    grid = inner.find(q("tblGrid"))
    if grid is not None:
        cols = grid.findall(q("gridCol"))
        longest = [1] * len(cols)   # longest cell, which sets the share of width
        word = [1] * len(cols)      # longest single word, the floor so no word breaks mid-letter
        for tr in rows:
            for j, tc in enumerate(tr.findall(q("tc"))):
                if j < len(cols):
                    s = text(tc).strip()
                    longest[j] = max(longest[j], len(s))
                    word[j] = max([word[j]] + [len(w) for w in s.split()])
        total_w = sum(int(c.get(q("w")) or 0) for c in cols) or 9000
        weight = [l ** 0.5 for l in longest]   # the square root keeps a long prose column from starving the rest
        total_u = sum(weight)
        for j, c in enumerate(cols):
            c.set(q("w"), str(max(word[j] * 130, round(total_w * weight[j] / total_u))))
    tb = place(tp, etree.Element(q("tblBorders")), TBLPR_ORDER)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = etree.SubElement(tb, q(side))
        if side in ("top", "bottom"):
            e.set(q("val"), "single"); e.set(q("sz"), BORDER_SZ); e.set(q("space"), "0"); e.set(q("color"), BORDER_CLR)
        else:
            e.set(q("val"), "none"); e.set(q("sz"), "0"); e.set(q("space"), "0"); e.set(q("color"), "auto")
    for i, tr in enumerate(rows):
        is_h = i in hdr
        for j, tc in enumerate(tr.findall(q("tc"))):
            jc = "center" if (is_h or (j < ncol and value[j])) else "left"
            format_cell(tc, is_h, jc)
    inner_runs = {id(r) for r in inner.iter(q("r"))}
    for r in outer.iter(q("r")):      # the caption, which sits in the wrapper cell, takes the font but keeps its size
        if id(r) not in inner_runs:
            set_run(r)
    for r in list(outer.iter(q("r"))):   # after the font is Arial, raise the superscripts Arial cannot draw
        split_superscripts(r)
    return 1


def main(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    root = etree.fromstring(data["word/document.xml"])
    body = root.find(q("body"))
    n = 0
    for el in list(body):
        if el.tag == q("tbl") and any(cap_re.match(text(p).strip()) for p in el.iter(q("p"))):
            n += format_table(el)
    data["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    tmp = tempfile.mktemp(suffix=".docx", dir=os.path.dirname(os.path.abspath(path)))
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.writestr(name, data[name])
    shutil.move(tmp, path)
    print(f"{path}: {n} data tables set to Arial 9 pt, bold centred headers, value columns centred, even rows, uniform borders")


if __name__ == "__main__":
    main([a for a in sys.argv[1:] if not a.startswith("--")][0])
