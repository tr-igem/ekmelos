#! /usr/bin/env python
# -*- coding: utf-8 -*-

##
## svg.py
##
## Script for FontForge generating an SVG file with one or more glyphs
## in the currently active font.
## Takes either the selected glyphs or the glyphs listed in the file
## "FONTPATH/svg/svg.txt".
## Format: Each line is one of:
##    = TITLE
##    == DESCRIPTION
##    Glyphname
##    #xCodepoint or U+Codepoint
##    Empty or with ## (comment), is ignored
##
## Reads "FONTPATH/svg/template.svg" and saves it with the glyphs
## under "FONTPATH/svg/FILENAME.svg".
## FILENAME is TITLE in kebab-case, or the glyphname or codepoint
## of the first glyph.
##
## The template file may include replacement fields:
##
##  {0.font}        Font name (fullname)
##  {0.copyright}   Font copyright notice
##  {0.filename}    FILENAME
##  {0.title}       TITLE
##  {0.desc}        Font comment or DESCRIPTION
##  {0.ascent}      Extent acc. to all glyph bounding boxes
##  {0.descent}
##  {0.width}
##  {0.height}
##  {0.max_height}  Maximum height of all glyphs
##  {0.x}           Position for the next glyph
##  {0.elements}    Sequence of the elements of all glyphs
##
## and an element "sub-template" used for each glyph:
##
##  {}ELEMENT{}
##  {}ELEMENT{}PADDING{}
##
## It is replaced internally with "{0.elements}".
## It may include further replacement fields for glyph specific data:
##
##  {1.unicode}     Codepoint
##  {1.code}        Codepoint as hex string
##  {1.name}        Glyphname
##  {1.desc}        Comment
##  {1.ascent}      Extent acc. to bounding box
##  {1.descent}
##  {1.width}
##  {1.height}
##  {1.path}        SVG path for <path d="..." />
##
## The glyphs are stacked in a line with PADDING (must be a number).
## Default is 1/20 em.
##
##
## Written by Thomas Richter (thomas-richter@aon.at), 2026-01-25
## 2026-01-26: Add codepoint, title, desc.
## 2026-01-27: Add element template. Change 0.path to 0.elements.
##
## This program is free software. Use, redistribute, and modify it as you wish.
##

import fontforge

font = fontforge.activeFont()

basepath = font.path.rsplit("/", 1)[0]
svgpath = basepath + "/svg"

glyphnames = []

element_tpl = '''\
  <path transform="translate({0.x} 0)" style="fill:#000000"
    d="{1.path}"
  />'''


class SvgData:
    """Overall data for the SVG file"""
    def __init__(self, font):
        self.font = font.fullname
        self.copyright = font.copyright
        self.filename = None
        self.title = None
        self.desc = font.comment
        self.pad = int(font.em / 20)
        self.glyphs = []
        self.ascent = 0
        self.descent = 0
        self.width = 0
        self.height = 0
        self.max_height = 0
        self.x = 0

    def name(self, n):
        n = n.strip()
        if not self.title:
            self.title = n
        if not self.filename:
            self.filename = "-".join(n.casefold().split())

    def add(self, g, n):
        if g.layers[1].isEmpty():
            return
        g = SvgGlyph(g)
        self.glyphs.append(g)
        self.ascent = max(self.ascent , g.ascent)
        self.descent = min(self.descent, g.descent)
        self.height = int(self.ascent - self.descent)
        self.max_height = max(self.max_height, g.height)
        if self.width > 0: self.x = self.width + self.pad
        self.width = self.x + g.width
        g.format(self)
        self.name(n)

    def finish(self):
        self.elements = "".join([g.element for g in self.glyphs])


class SvgGlyph:
    """Glyph data with SVG path generated from spline points"""
    def __init__(self, g):
        self.unicode = g.unicode
        self.code = "%04X" % g.unicode
        self.name = g.glyphname
        self.desc = g.comment

        box = g.boundingBox()
        self.ascent = int(box[3])
        self.descent = int(box[1])
        self.width = int(box[2] - box[0])
        self.height = int(box[3] - box[1])

        self.path = ''
        self.m = None
        self.closepath()

        for contour in g.layers[1]:
            for p in contour: self.point(p)
            self.closepath()

    def point(self, p):
        xy = "%d %d" % (p.x - self.x, - (p.y - self.y))
        if p.on_curve:
            if not self.m:
                self.path += "M" + xy
                self.m = p
            elif self.c != '':
                self.path += "c" + self.c + " " + xy
                self.c = ''
            else:
                self.path += "l" + xy
            self.x = p.x
            self.y = p.y
        else:
            if self.c != '': self.c += " "
            self.c += xy

    def closepath(self):
        if self.m:
            self.point(self.m)
            self.path += "z"
        self.x = 0
        self.y = 0
        self.m = None
        self.c = ''

    def format(self, svg):
        self.element = element_tpl.format(svg, self)


svg = SvgData(font)


## read list of glyphs

try:
    file = open(svgpath + "/svg.txt")
except OSError:
    pass
else:
    for l in file:
        if l.isspace() or "##" in l:
            continue
        elif l.startswith("="):
            if l.startswith("=="):
                svg.desc = l[2:].strip()
            else:
                svg.name(l[1:])
        else:
            glyphnames.append(l.strip())
    file.close()


## read template

file = open(svgpath + "/template.svg")
tpl = file.read(-1)
file.close()

p = tpl.split("{}", 3)
if len(p) > 2:
    tpl = p[0] + "{0.elements}" + p[-1]
    element_tpl = p[1]
    if len(p) > 3:
        svg.pad = int(p[2])


## generate SVG for all glyphs

if len(glyphnames) == 0:
    for g in font.selection.byGlyphs:
        svg.add(g, g.glyphname)
else:
    for n in glyphnames:
        try:
            if n.startswith(("#x", "U+")):
                n = n[2:]
                g = font[int(n, 16)]
            else:
                g = font[n]
        except Exception:
            continue
        else:
            svg.add(g, n)

svg.finish()


if svg.filename:
    file = open(svgpath + "/" + svg.filename + ".svg", 'w', newline = "\n")
    file.write(tpl.format(svg))
    file.close()
