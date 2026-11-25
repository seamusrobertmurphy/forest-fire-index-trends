"""Turns the page of every wide captioned table in a rendered Word manuscript to landscape, leaving the other pages portrait.

A table is wide, and turned, when its grid has six or more columns; the narrow tables stay upright
(Seamus, 2026-11-24). Run after table-format.py, which already sets the table font and size, so this
script no longer touches either.

Run on the rendered file after the render:
  python3 ../05.scripts/landscape-tables.py manuscript-jars-2026-11-06.docx

Quarto's own landscape block was not used, because it sets A4 paper and leaves the section before each table
without the template's line numbers and footers. This copies the document's final section settings instead,
so the paper, margins, line numbers and page-number footer of style-formal.docx hold on every page, the page
count runs on through the landscape pages, and only the first section keeps the blank title-page footer.
"""
import copy, os, re, shutil, sys, tempfile, zipfile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
q = lambda tag: f"{{{W}}}{tag}"


def not_first(sect):
    # Later sections neither restart the page count nor use the blank title-page footer.
    for t in sect.findall(q("titlePg")):
        sect.remove(t)
    for p in sect.findall(q("pgNumType")):
        p.attrib.pop(q("start"), None)
    return sect


def landscape(sect, text_w):
    s = not_first(copy.deepcopy(sect))
    sz = s.find(q("pgSz"))
    w, h = sz.get(q("w")), sz.get(q("h"))
    sz.set(q("w"), h); sz.set(q("h"), w); sz.set(q("orient"), "landscape")
    return s


def break_para(sect):
    # An empty paragraph whose properties end a section; it carries no line number.
    p = etree.Element(q("p")); ppr = etree.SubElement(p, q("pPr"))
    etree.SubElement(ppr, q("suppressLineNumbers")); ppr.append(sect)
    return p


def widen(group, width):
    # Scale each table grid in the block to the landscape text width, keeping the columns' proportions.
    for grid in (g for el in group for g in el.iter(q("tblGrid"))):
        cols = grid.findall(q("gridCol")); total = sum(int(c.get(q("w"))) for c in cols)
        for c in cols:
            c.set(q("w"), str(round(int(c.get(q("w"))) * width / total)))


def main(path):
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    body = root.find(q("body")); final = body[-1]
    assert final.tag == q("sectPr"), "the document does not end in its section settings"
    if body.find(f"{q('p')}/{q('pPr')}/{q('sectPr')}/{q('pgSz')}[@{q('orient')}='landscape']") is not None:
        sys.exit(f"{path} already has landscape table pages; render it again first")
    mar = final.find(q("pgMar")); sz = final.find(q("pgSz"))
    text_w = int(sz.get(q("h"))) - int(mar.get(q("left"))) - int(mar.get(q("right")))  # page height becomes the width
    caption = re.compile(r"^Table[\s ]+S?[\s ]*\d+[:.]")  # Table 1: or Table 1. in the main text, Table S1. in the supplement
    kids = list(body); groups = []
    for i, el in enumerate(kids):
        if el.tag == q("tbl") and any(caption.match("".join(t.text or "" for t in p.iter(q("t")))) for p in el.iter(q("p"))):
            j = i
            while j + 1 < len(kids) and kids[j + 1].tag == q("bookmarkEnd"):
                j += 1
            groups.append(kids[i:j + 1])
    if not groups:
        sys.exit(f"{path}: no captioned table found, file left unchanged")
    def group_ncol(g):  # flextable writes no grid, so the columns are counted from the widest row
        return max((len(tr.findall(q("tc"))) for el in g for tr in el.iter(q("tr"))), default=0)
    groups = [g for g in groups if group_ncol(g) >= 6]  # only the wide tables turn; the narrow ones stay upright
    if not groups:
        print(f"{path}: no wide table (six or more columns), every table left upright")
        return
    first, ends = True, set()
    for g in groups:
        prev = g[0].getprevious()
        if prev in ends:  # two tables in a row share one landscape section
            body.remove(prev)
        else:
            g[0].addprevious(break_para(copy.deepcopy(final) if first else not_first(copy.deepcopy(final))))
        first = False
        end = break_para(landscape(final, text_w)); g[-1].addnext(end); ends.add(end)
        widen(g, text_w)
    not_first(final)
    xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    fd, tmp = tempfile.mkstemp(suffix=".docx", dir=os.path.dirname(os.path.abspath(path))); os.close(fd)
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, xml if item.filename == "word/document.xml" else zin.read(item.filename))
    shutil.move(tmp, path)
    print(f"{path}: {len(groups)} table pages turned to landscape")


if __name__ == "__main__":
    main(sys.argv[1])
