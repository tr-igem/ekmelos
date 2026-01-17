#! /usr/bin/env python
# -*- coding: utf-8 -*-

##
## glyphnametable.py
##
## Script for FontForge generating a LilyPond glyph name table
## from the currently active font.
## Reads "FONTPATH/ly/template-map.ily" and saves it with the
## included glyph name table under "FONTPATH/ly/FONTNAME-map.ily".
##
## Table format:
## A Scheme alist with the code points mapped onto glyph names,
## except for Unicode glyphs with a simple glyph name uHHHH.
##
##  ("GLYPHNAME" CODEPOINT)
##
##
## Written by Thomas Richter (thomas-richter@aon.at)
## 2026-01-17: Extracted from metadata.py
##
## This program is free software. Use, redistribute, and modify it as you wish.
##

import fontforge

font = fontforge.activeFont()

basepath = font.path.rsplit("/", 1)[0]
lilypath = basepath + "/ly"

filename = font.fullname.lower().split()
filename.append("map")
filename = "-".join(filename)


names = {}
tab = ''

for n in font:
    names[font[n].unicode] = n

for c in sorted(names.keys()):
    n = names[c]
    if n != ("u%04X" % c):
        tab += '  ("%s" . #x%04X)\n' % (n, c)

path = lilypath + "/template-map.ily"
file = open(path)
tpl = file.read(-1)
file.close()

path = lilypath + "/" + filename + ".ily"
file = open(path, 'w', newline = "\n")
file.write(tpl.format(font.copyright, font.fullname, tab))
file.close()
