#! /usr/bin/env python
# -*- coding: utf-8 -*-

##
## pathtable.py
##
## Script for FontForge generating a LilyPond path table
## from the currently active font.
##
## Format:
## A Scheme alist with all glyphs of the font mapped onto codepoints,
## except for glyphs without contour (space, glyphs with reference).
## Each value (cdr) is a command list describing the path of the glyph
## for use with (make-path-stencil):
##
##  (codepoint M x y command ... x y ... z ...)
##
## x,y: integers
## command: l or c
##
##
## Written by Thomas Richter (<thomas-richter@aon.at>), March 2024
## This program is free software. Use, redistribute, and modify it as you wish.
##

import fontforge
from datetime import date


font = fontforge.activeFont()

basepath = font.path.rsplit("/", 1)[0]  # "/Ekmelik/Software/Ekmelos"
lilypath = basepath + "/ly"

filename = font.fullname.lower().split()
filename.append("paths")
filename = "-".join(filename)  # "ekmelos-paths"

now = date.today()


class PathTable:
    """Generate path table from spline points"""
    def __init__(self):
        self.tab = {}
        self.m = None
        self.closepath()

    def point(self, p):
        xy = " %d %d" % (p.x - self.x, p.y - self.y)
        if p.on_curve:
            if not self.m:
                self.v += " M" + xy
                self.m = p
            elif self.c != '':
                self.v += " c" + self.c + xy
                self.c = ''
            else:
                self.v += " l" + xy
            self.x = p.x
            self.y = p.y
        else:
            self.c += xy

    def closepath(self):
        if self.m:
            self.point(self.m)
            self.v += " z"
        self.x = 0
        self.y = 0
        self.m = None
        self.c = ''

    def glyph(self, g = None):
        if g:
            self.k = g.unicode
            self.v = ''
        else:
            self.tab[self.k] = self.v

    def __str__(self):
        s = ''
        for k in sorted(self.tab.keys()):
            s += "  (#x%04X" % (k) + self.tab[k] + ")\n"
        return s


tab = PathTable()

for n in font:
    g = font[n]
    if not g.layers[1].isEmpty():
        tab.glyph(g)
        for contour in g.layers[1]:
            for p in contour: tab.point(p)
            tab.closepath()
        tab.glyph()

path = lilypath + "/" + filename + "-template.ily"
file = open(path)
tpl = file.read(-1)
file.close()

path = lilypath + "/" + filename + ".ily"
file = open(path, 'w', newline = "\n")
file.write(tpl.format(now.year, font.fullname, filename, str(tab)))
file.close()
