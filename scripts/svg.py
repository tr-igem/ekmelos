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
## The template file may include the following replacement fields
## with overall data:
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
##  {0.path}        Sequence of <path> elements of all glyphs
##
## The first <path> element in the template file is used for each glyph.
## It is replaced internally with "{0.path}".
## It may include the above and the following replacement fields
## with glyph specific data:
##
##  {1.unicode}     Codepoint
##  {1.code}        Codepoint as hex string
##  {1.name}        Glyphname
##  {1.desc}        Comment
##  {1.ascent}      Extent acc. to bounding box
##  {1.descent}
##  {1.width}
##  {1.height}
##  {1.path}        SVG path, for attribute "d"
##
## The glyphs are stacked in a line with a padding of 1/20 em.
## Another padding can be specified immediately after the <path> element.
##
##
## Written by Thomas Richter (thomas-richter@aon.at), 2026-01-25
## 2026-01-26: Add codepoint, title, desc.
##
## This program is free software. Use, redistribute, and modify it as you wish.
##

import fontforge

font = fontforge.activeFont()

basepath = font.path.rsplit("/", 1)[0]
svgpath = basepath + "/svg"

glyphnames = []

pathElement = '''\
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
        self.path = ''

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
        self.path = "\n".join([str(g) for g in self.glyphs])


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

        self.path_element = ''
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
        self.path_element = pathElement.format(svg, self)

    def __str__(self):
        return self.path_element


svg = SvgData(font)


## read list of glyphs

path = svgpath + "/svg.txt"
try:
    file = open(path)
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

path = svgpath + "/template.svg"
file = open(path)
tpl = file.read(-1)
file.close()

p = tpl.partition("<path")
if len(p[1]) != 0:
    e = p[2].partition("/>")
    if len(e[1]) != 0:
        n = ''
        for c in e[2]:
            if c.isdigit(): n += c
            else: break
        tpl = p[0] + "{0.path}" + e[2][len(n):]
        pathElement = p[1] + e[0] + e[1]
        if len(n) != 0:
            svg.pad = int(n)


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
    path = svgpath + "/" + svg.filename + ".svg"
    file = open(path, 'w', newline = "\n")
    file.write(tpl.format(svg))
    file.close()
