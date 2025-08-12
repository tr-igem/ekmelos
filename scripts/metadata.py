#! /usr/bin/env python
# -*- coding: utf-8 -*-

##
## metadata.py
##
## Script for FontForge generating metadata for the currently active font,
## actually intended for the Ekmelos font.
##
## Source files (additional to the font):
## glyphnames.json           SMuFL metadata
## classes.json              SMuFL metadata
## classes-extra.json        supplement classes (for optional glyphs)
## glyphdata-extra.json      supplement data ("description" for optional glyphs)
## aglfn.txt                 Adobe Glyph List For New Fonts
## UnicodeData.txt           Unicode UCD file
## Ekmelily/tunings.txt      Ekmelily tunings and notation styles
## alterations-TUNING.csv    accidentals for Ekmelily notation styles
## ekmelib/glyphs.txt        glyphs used by ekmelib
##
## Target files in the "metadata" folder:
## metadata.json             font-specific metadata
## classes.json              classes with glyphs of the font
## glyphnames.json           glyph names of the font
## glyphdata.json            summarized glyph metadata
## ekmelily.json             glyphs grouped by Ekmelily tunings and notation styles
## ekmelib.json              glyphs grouped by ekmelib tunings
## FONTNAME-map.ily          Scheme alist of glyph names for LilyPond
##
## Written by Thomas Richter (<thomas-richter@aon.at>), July 2017
## Revised for Ekmelily 3.0, June 2019
## Revised for ekmelib and Ekmelos 2.6, January 2020
## Revised for Ekmelily/tunings.txt and alterations-TUNING.csv, April 2020
## Revised for classes-extra, June 2020
## Revised for bounding box cut-outs and stem anchor, September 2020
## Revised for repeatOffset and noteheadOrigin, October 2020
## Revised for FONTNAME-map.ily, November 2020
## Revised for lilypond/ekmelos-map.ily, February 2021
## Revised for glyphdata-extra, March 2021
## Revised for further Unicode blocks, May 2021
## Revised for recursive classes-extra, Dingbats, alternates, ligatures, 13 July 2021
## Revised for Arrows, Miscellaneous Symbols and Arrows, 13 August 2021
## Revised for glyph-map file, 23 August 2021
## Revised for Mathematical Operators, 25 November 2021
## Revised for Block Elements, Geometric Shapes, Supplemental Arrows-A/B, 9 June 2022
## Revised for Geometric Shapes Extended, Supplemental Arrows-C,
##  Supplemental Symbols and Pictographs, Symbols and Pictographs Extended-A,
##  9 February 2023
## Revised for LilyPond path ly, 13 March 2023
## Revised for size variants, 19 June 2023
## Revised for engravingDefaults, 29 August 2023
## Revised for path to SMuFL metadata, 23 March 2024
## Revised for accidentals-TUNING.csv and FONTNAME.json,
##  Selecting noteheads and flags for stem anchors, 30 July 2025
## Revised for stem length of flags, 11 August 2025
##
## Inspired from generate_font_metadata.py by Robert Piéchaud
## This program is free software. Use, redistribute, and modify it as you wish.
##

import fontforge
import json
import csv
from datetime import date


font = fontforge.activeFont()  # or fontforge.fonts()[0]

basepath = font.path.rsplit("/", 1)[0]  # "/Ekmelik/Software/Ekmelos"
metapath = basepath + "/metadata"
lilypath = basepath + "/ly"
smuflpath = metapath + "/smufl"
aglpath = metapath + "/agl"
unicodepath = metapath + "/unicode"
ekmelilypath = "/Ekmelik/Software/Ekmelily"
accpath = "/Ekmelik/Software/Tables/accidentals"

mapname = font.fullname.lower().split()
mapname.append("map")
mapname = "-".join(mapname)  # "ekmelos-map"

staffSpace = font.em / 4.0  # usually 250

MAX = 10000

now = date.today()


# staff-line thickness in upm (for engravingDefaults)
thick = 28
n = "staff1Line"
if n in font:
    g = font[n]
    o = g.boundingBox()
    thick = o[3] - o[1]


log = open(basepath + "/log.txt", "a")
log.write("\nName: %s, %s\nVer:  %s\nPath: %s\nEM:   %d\nMap:  %s\n" % (font.fullname, font.fontname, font.version, font.path.lstrip("C:"), font.em, mapname))

countRecommended = 0
countOptional = 0
countAccidental = 0
countLatin = 0
countPunctuation = 0
countArrows = 0
countMathematical = 0
countTechnical = 0
countBlock = 0
countGeometric = 0
countSymbols = 0
countDingbats = 0
countSymbolsArrows = 0
countMusical = 0
countSymbolsPict = 0


# Summarized glyph metadata mapped onto glyphname
# with attributes:
# code                codepoint as a number
# codepoint           codepoint as a string 'U+...'
# alternateCodepoint  from SMuFL
# description         from SMuFL, comment, Unicode name, or other glyph
# alternates          list of alternate encodings (stylistic alternates)
# ligature            list of component glyphnames
# alternateOf         name of glyph for which it is an alternate
# classes             list of classes including this glyph
# block               name of block range including this glyph
# ekmelily            True if used by Ekmelily
# ekmelib             True if used by ekmelib
# ref                 name of referenced glyph (will be deleted)
# name                glyphname (will be deleted)
glyphdata = {}


def getGlyphData(n):
    """Retrieve the (possibly new) dict with the metadata for glyphname n"""
    d = glyphdata.get(n)
    if not d:
        d = {}
        glyphdata[n] = d
    return d


def getClassItems(c, o):
    """Retrieve the glyphnames of class c in dict o recursively"""
    l = []
    for n in o[c]:
        if n in o:
            l += getClassItems(n, o)
        else:
            l.append(n)
    return l


def writeJSON(p, o):
    """Write the object o in JSON format into file path p"""
    file = open(p, 'w')
    json.dump(o, file, indent=2, separators=(",", ": "), sort_keys=True)


class Anchors:
    """Data collected for glyphsWithAnchors"""
    def __init__(self):
        self.d = None
        self.data = {}

    def add(self, k, x, y):
        if None == self.d: self.d = {}
        self.d[k] = (round(x / staffSpace, 3), round(y / staffSpace, 3))

    def addSS(self, k, x, y):
        if None == self.d: self.d = {}
        self.d[k] = (x, y)

    def finish(self, n):
        if self.d != None:
            self.data[n] = self.d
            self.d = None

anchor = Anchors()


class Cutout:
    """Bounding box cut-out of one corner"""
    layer = "Cutout"
    wMin = int(font.em * 0.01)
    hMin = int(font.em * 0.01)

    def __init__(self, n, x, y):
        self.key = 'cutOut' + n
        self.dx = x
        self.dy = y

    def coord(self, co, x, y):
        if co[2].x == x and co[2].y == y: # is 3rd point corner of bbox
            w = (co[0].x - x) * self.dx
            h = (co[0].y - y) * self.dy
            if w >= self.wMin and h >= self.hMin:
                # translate to SW corner of bbox
                anchor.add(self.key, co[0].x - bb[0], co[0].y - bb[1])

NE = Cutout("NE", -1, -1)
NW = Cutout("NW", 1, -1)
SE = Cutout("SE", -1, 1)
SW = Cutout("SW", 1, 1)


# conversion for engravingDefaults

def upm(v):
    """Convert upm to staff spaces (1 ss = 1/4 em)"""
    return round(v / staffSpace, 3)


# read SMuFL metadata for the characters in the font

file = open(smuflpath + "/glyphnames.json")
for n, d in json.load(file).items():
    n = str(n)  # necessary for font
    if n in font:
        g = font[n]
        c = int(d['codepoint'][2:], 16)  # "U+XXXX" -> code
        if c == g.unicode:
            glyphdata[n] = d
        else:
            log.write("%s: Has different codepoint %04X in font.\n" % (n, g.unicode))
file.close()


# read all SMuFL classes

file = open(smuflpath + "/classes.json")
smuflClasses = json.load(file)
file.close()


# read supplement classes

extraClasses = {}
file = open(metapath + "/classes-extra.json")
extraClasses = json.load(file)
for c in extraClasses.keys():
    extraClasses[c] = getClassItems(c, extraClasses)
file.close()


# read supplement glyph data

file = open(metapath + "/glyphdata-extra.json")
extraGlyphdata = json.load(file)
file.close()


# read glyphs used by ekmelib in all tunings

file = open(basepath + "/fonts/ekmelib/glyphs.txt")
tuning = 'x'
ekmelib = { 'x': [] }
ekmelibCode = set()
for l in file:
    if l.startswith("#"): continue  # skip comment
    v = l.split(" ", 1)
    if len(v) == 1: continue  # skip empty (or invalid) line
    if 'tuning' == v[0]:  # 12 24 72
        tuning = v[1].rstrip()
        ekmelib[tuning] = list(ekmelib['x'])  # common glyphs for all tunings
    else:
        ekmelib[tuning].append(v[1].rstrip())
        ekmelibCode.add(int(v[0], 16))
file.close()
del ekmelib['x']


# read Adobe Glyph List For New Fonts
# to map glyph names onto Unicode character names

file = open(aglpath + "/aglfn.txt")
agl = {}
for l in file:
    if l.startswith("#"): continue  # skip comment
    v = l.strip().split(";")
    if len(v) == 3: agl[v[2]] = v[1]
file.close()


# read Unicode glyph name (for description) and General Category (for class)
# of the characters in the Unicode blocks:
# Basic Latin (0020-007E)
# Latin-1 Supplement (00A0-00FF)
# General Punctuation (2000-205F)

unicodeNames = {}
unicodeGC = {
    'L': "letter",
    'M': "mark",
    'N': "number",
    'P': "punctuation",
    'S': "symbol",
    'Z': "separator",
    'C': "other" }
unicodeClasses = { v: [] for v in unicodeGC.values() }

file = open(unicodepath + "/UnicodeData.txt")
for l in file:
    if l.startswith("#"): continue  # skip comment
    v = l.split(";", 3)
    c = int(v[0], 16)  # codepoint
    if c < 0x20 or (c >= 0x7F and c < 0xA0): continue  # skip C0/C1
    if c >= 0x0100 and c < 0x2000: continue  # skip between Latin and Punctuation
    if c >= 0x2060: break  # skip everything else
    unicodeNames[c] = v[1].capitalize()  # glyph name
    cn = unicodeGC[v[2][:1]]  # first letter of gc -> class name
    n = agl.get(v[1], '')  # Unicode character name -> glyph name
    unicodeClasses[cn].append(n)
file.close()


# left edge of noteheads (double whole relative to whole)
# should be determined from the glyphs
noteheadOrigin = {
    0xE0A0: 106,
    0xE0A6: 106,
    0xE0AC: 106,
    0xE0B0: 106,
    0xE0B4: 106,
    0xE0BA: 106,
    0xE0C3: 106,
    0xE0D5: 106,
    0xE0D6: 106,
    0xE0D7: 106,
    0xE0DF: 106,
    0xE0E7: 106,
    0xE0ED: 106,
    0xE0F1: 106,
    0xE10A: 106,
    0xE124: 106,
    0xE128: 106,
    0xE12C: 106,
    0xE12D: 106,
    0xE12E: 106,
    0xECD0: 125,
    0xECD1: 125,
    0xECD2: 125,
    0xECD3: 125,
    0xECD4: 125,
    0xECD5: 125,
    0xECD6: 125,
    0xECD7: 125,
    0xECD8: 125,
    0xECD9: 125,
    0xECDA: 125,
    0xECDB: 125,
    0xECDC: 125,
    0xECDD: 125,
    0xF637: 36,
    0xF638: 36,
    0xF639: 36 }


# stem anchor data of some note heads
# where the data are missing or wrong determined from the glyph
noteheadStemAnchor = {
    0xE117: (422, 161,  68, -161),
    0xE116: (422, 161,  68, -161),
    0xE1C0: (250, 100,  0, 100),
    0xE1C1: (250, 100,  0, 100),
    0xE1B0: (326, 45,   0, -45),
    0xE1B1: (326, 45,   0, -45),
    0xE1BA: (326, -100, 0, -100),
    0xE1BB: (326, -100, 0, -100),
    0xE1BE: (326, 30,   0, 30),
    0xE1BF: (326, 30,   0, 30) }


# stem length (in staff spaces) of flags
flagStemLength = {
    # default
    0xE240: 0,
    0xE242: 0,
    0xE244: 0.73,
    0xE246: 1.45,
    0xE248: 2.18,
    0xE24A: 2.92,
    0xE24C: 3.65,
    0xE24E: 4.39,
    0xE241: 0,
    0xE243: 0,
    0xE245: 0.73,
    0xE247: 1.45,
    0xE249: 2.18,
    0xE24B: 2.92,
    0xE24D: 3.65,
    0xE24F: 4.39,

    # short
    0xF410: 0,
    0xF413: 0,
    0xF416: 0,
    0xF419: 0.53,
    0xF41C: 1.03,
    0xF41F: 1.61,
    0xF422: 2.18,
    0xF425: 2.76,
    0xF6C0: 0,
    0xF6C1: 0,
    0xF6C2: 0,
    0xF6C3: 0.53,
    0xF6C4: 1.03,
    0xF6C5: 1.61,
    0xF6C6: 2.18,
    0xF6C7: 2.76,

    # straight
    0xF40F: 0,
    0xF412: 0,
    0xF415: 0,
    0xF418: 0.85,
    0xF41B: 1.71,
    0xF41E: 2.5,
    0xF421: 3.29,
    0xF424: 4.05,
    0xF411: 0,
    0xF414: 0,
    0xF417: 0,
    0xF41A: 0.85,
    0xF41D: 1.71,
    0xF420: 2.5,
    0xF423: 3.29,
    0xF426: 4.05 }


# classes to which glyphs of the font belong
classes = {}


# read glyph metadata from the active font

glyphsWithAlternates = {}
ligatures = {}
glyphBBoxes = {}
optionalGlyphs = {}
sets = {}  # not used
codename = {}

for n in font:
    g = font[n]         # glyph of name n
    c = g.unicode       # codepoint
    u = "U+%04X" % c    # codepoint as string
    d = getGlyphData(n)

    # alternate encodings (stylistic alternates)
    if g.altuni:
        l = []
        for v in g.altuni:
            # v = (alternate-codepoint, variation-selector, reserved)
            if v[0] in font:
                a = font[v[0]]
                getGlyphData(a.glyphname)['alternateOf'] = n
                l.append({
                    'codepoint': "U+%04X" % a.unicode,
                    'name': a.glyphname })
            else:
                log.write("%s: Has alternate codepoint %04X not in the font.\n" % (n, v[0]))

        if len(l): glyphsWithAlternates[n] = { 'alternates': l }

    # references (only the first one is used for missing description)
    # Note: Ekmelos has only glyphs (mainly alternate codepoints) with a single reference.
    for v in g.references: # v = (glyphname, transformation-matrix)
        if v[0] in font:
            d['ref'] = v[0]
        else:
            log.write("%s: Has referenced glyph %s not in the font.\n" % (n, v[0]))
        break

    # find classes to which the glyph belongs
    cls = []
    for o in [smuflClasses, extraClasses, unicodeClasses]:
        for cn in o.keys():  # available class names
            if n in o[cn]:
                cls.append(cn)
                # found cn for the first time (Python has no autovivification)
                if cn not in classes: classes[cn] = []
                classes[cn].append(n)
    d['classes'] = cls

    # bounding box
    bb = g.boundingBox() # xmin,ymin,xmax,ymax
    l = [ round(v / staffSpace, 4) for v in bb ]
    glyphBBoxes[n] = {
        'bBoxSW': (l[0], l[1]),
        'bBoxNE': (l[2], l[3]) }

    # bounding box cut-outs
    if Cutout.layer in font.layers:
        l = g.layers[Cutout.layer]
        if len(l) > 0: # has contours
            for co in l:
                if len(co) >= 3: # use 1st and 3rd point
                    NE.coord(co, bb[2], bb[3]) # (xmax,ymax)
                    NW.coord(co, bb[0], bb[3]) # (xmin,ymax)
                    SE.coord(co, bb[2], bb[1]) # (xmax,ymin)
                    SW.coord(co, bb[0], bb[1]) # (xmin,ymin)

    # stem anchor of noteheads
    if (("noteheads" in cls) and ("Half" in n or "Black" in n or "White" in n)) or c in noteheadStemAnchor:
        if c in noteheadStemAnchor:
            l = noteheadStemAnchor[c]
            anchor.add('stemUpSE', l[0], l[1])
            anchor.add('stemDownNW', l[2], l[3])
        else:
            x = (bb[0] - g.left_side_bearing,
                 bb[2] + g.right_side_bearing)
            l = MAX
            r = -MAX
            for co in g.layers[1]: # assume one outer (clockwise) contour
                if co.isClockwise():
                    break
            for p in co:
                if p.on_curve:
                    if p.x == x[0]: l = min(l, p.y)
                    if p.x == x[1]: r = max(r, p.y)
            if l != MAX:
                anchor.add('stemDownNW', x[0], l)
            if r != -MAX:
                anchor.add('stemUpSE', x[1], r)

    # stem anchor of flags
    if n.startswith("flag") and not n.startswith("flagInternal") and c in flagStemLength:
        if "Up" in n:
            anchor.addSS('stemUpNW', 0, flagStemLength[c])
        else:
            anchor.addSS('stemDownSW', 0, -flagStemLength[c])

    # offset of repeating glyphs
    # (Combining strokes for trills and mordents, Multi-segment lines)
    if 0xE590 <= c <= 0xE5AF or 0xEAA0 <= c <= 0xEB0F or 0xF642 <= c <= 0xF644:
        anchor.add('repeatOffset', g.width, 0.0)

    # left edge of noteheads (double whole relative to whole)
    if c in noteheadOrigin:
        anchor.add('noteheadOrigin', noteheadOrigin[c], 0.0)

    anchor.finish(n)

    # ligature from lookup table
    for v in g.getPosSub("*"):
        # v = (subtable-name, "Ligature", component-glyphname, ...)
        if "Ligature" == v[1]:
            ligatures[n] = {
                'codepoint': u,
                'componentGlyphs': v[2:] }
            break # ignore other tables

    # block ranges
    if c >= 0xE000 and c <= 0xF3FF:  # Recommended Character
        countRecommended += 1
        # Medieval and Renaissance accidentals have no 'acc..' prefix
        if 'accidental' in n or 'accSagittal' in n or c >= 0xE9E0 and c <= 0xE9EF:
            countAccidental += 1
        d['block'] = 'E000'
    elif c >= 0xF400 and c <= 0xF8FF:  # Optional Glyph
        countOptional += 1
        d['block'] = 'F400'
        optionalGlyphs[n] = { 'classes': cls, 'codepoint': u }
    elif c >= 0x0020 and c <= 0x007F:  # Basic Latin
        countLatin += 1
        d['block'] = '0000'
    elif c >= 0x00A0 and c <= 0x00FF:  # Latin-1 Supplement
        countLatin += 1
        d['block'] = '0080'
    elif c >= 0x2000 and c <= 0x206F:  # General Punctuation
        countPunctuation += 1
        d['block'] = '2000'
    elif c >= 0x2190 and c <= 0x21FF:  # Arrows
        countArrows += 1
        d['block'] = '2190'
    elif c >= 0x2200 and c <= 0x22FF:  # Mathematical Operators
        countMathematical += 1
        d['block'] = '2200'
    elif c >= 0x2300 and c <= 0x23FF:  # Miscellaneous Technical
        countTechnical += 1
        d['block'] = '2300'
    elif c >= 0x2580 and c <= 0x259F:  # Block Elements
        countBlock += 1
        d['block'] = '2580'
    elif c >= 0x25A0 and c <= 0x25FF:  # Geometric Shapes
        countGeometric += 1
        d['block'] = '25A0'
    elif c >= 0x2600 and c <= 0x26FF:  # Miscellaneous Symbols
        countSymbols += 1
        d['block'] = '2600'
    elif c >= 0x2700 and c <= 0x27BF:  # Dingbats
        countDingbats += 1
        d['block'] = '2700'
    elif c >= 0x27F0 and c <= 0x27FF:  # Supplemental Arrows-A
        countArrows += 1
        d['block'] = '27F0'
    elif c >= 0x2900 and c <= 0x297F:  # Supplemental Arrows-B
        countArrows += 1
        d['block'] = '2900'
    elif c >= 0x2B00 and c <= 0x2BFF:  # Miscellaneous Symbols and Arrows
        countSymbolsArrows += 1
        d['block'] = '2B00'
    elif c >= 0x1D100 and c <= 0x1D1FF:  # Musical Symbols
        countMusical += 1
        d['block'] = '1D100'
    elif c >= 0x1F300 and c <= 0x1F5FF:  # Miscellaneous Symbols and Pictographs
        countSymbolsPict += 1
        d['block'] = '1F300'
    elif c >= 0x1F780 and c <= 0x1F7FF:  # Geometric Shapes Extended
        countGeometric += 1
        d['block'] = '1F780'
    elif c >= 0x1F800 and c <= 0x1F8FF:  # Supplemental Arrows-C
        countArrows += 1
        d['block'] = '1F800'
    elif c >= 0x1F900 and c <= 0x1F946:  # Supplemental Symbols and Pictographs
        countSymbolsPict += 1
        d['block'] = '1F900'
    elif c >= 0x1FA70 and c <= 0x1FAFF:  # Symbols and Pictographs Extended-A
        countSymbolsPict += 1
        d['block'] = '1FA70'
    else:
        log.write("%s: Is not in an expected block.\n" % n)

    if c in ekmelibCode: d['ekmelib'] = True

    # complete glyphdata
    d['name'] = n
    d['code'] = c
    d['codepoint'] = u
    if 'description' not in d: d['description'] = g.comment or ''

    # for ligatures and stylistic alternates
    codename[c] = n


# read stylistic alternates

file = open(metapath + "/alternates.txt")
for l in file:
    v = [ int(c) for c in l.split() ]
    n = codename.get(v[0])
    if n:
        r = []
        for c in v[1:]:
            a = codename.get(c)
            if a:
                getGlyphData(a)['alternateOf'] = n
                r.append({
                    'codepoint': "U+%04X" % c,
                    'name': a })
        if len(r):
            glyphsWithAlternates[n] = { 'alternates': r }
file.close()


# read size variants

file = open(metapath + "/variants.txt")
for l in file:
    v = [ int(c) for c in l.split() ]
    n = codename.get(v[0])
    a = codename.get(v[1])
    c = v[2]
    if n and a:
        d = getGlyphData(n)
        v = d.get('variants')
        if not v:
            v = {}
            d['variants'] = v
            if n in extraGlyphdata:
                x = extraGlyphdata[n].get('variantScale')
                if x: v[int(x)] = n
        v[c] = a
        getGlyphData(a)['variantOf'] = n
file.close()


# read ligatures

file = open(metapath + "/ligatures.txt")
for l in file:
    v = [ int(c) for c in l.split() ]
    n = codename.get(v[0])
    if n:
        ligatures[n] = {
            'codepoint': "U+%04X" % v[0],
            'componentGlyphs': [ codename[c] for c in v[1:] ] }
file.close()


# read accidentals used by Ekmelily in all notation styles and tunings

notations = {}
ekmelily = {}
EKM_EQUIV_CODE = 0x0200

file = open(ekmelilypath + "/tunings.txt")
for l in file:
    if "N:" in l:
        c = l.split()
        notations[c[0]] = c[2:]
file.close()

for tuning in notations.keys():
    file = open(accpath + "/accidentals-" + tuning + ".csv")
    tab = csv.DictReader(file, dialect='excel')
    o = {}
    for n in notations[tuning]:
        o[n] = {}

    for l in tab:
        if int(l['code'], 16) & EKM_EQUIV_CODE == 0:  # not enh. equiv. accidentals
            for n, v in o.items():
                c = l[n + "Name"]  # field with glyph name(s)
                if c != "" and " " not in c:  # single glyph only
                    glyphdata[c]['ekmelily'] = True
                    v[c] = int(l['step'])

    ekmelily[tuning] = o
    file.close()


# complete glyphdata (description, ligature, alternates),
# collect glyphnames, and write glyph-map file

glyphnames = {}
l = ''

file = open(lilypath + "/" + mapname + "-template.ily")
tpl = file.read(-1)
file.close()

for d in sorted(glyphdata.values(), key=lambda x: x['code']):
    n = d['name']
    c = d['code']

    v = d['description']
    if v == '':
        if n in extraGlyphdata:
            v = extraGlyphdata[n]['description']
        elif n in ligatures: # concatenation of components' descriptions
            v = []
            for l in ligatures[n]['componentGlyphs']:
                v.append(glyphdata[l]['description'])
            v = ", ".join(v)
        elif d['code'] in unicodeNames: # basic latin Unicode name
            v = unicodeNames[d['code']]
        elif 'alternateOf' in d: # from glyph for which d is an alternate
            v = glyphdata[d['alternateOf']]['description']
        elif 'ref' in d: # from referenced glyph
            v = glyphdata[d['ref']]['description']
        d['description'] = v

    x = glyphsWithAlternates.get(n)
    if x: d['alternates'] = x['alternates']

    x = ligatures.get(n)
    if x: d['ligature'] = x['componentGlyphs']

    # only with real name (SMuFL, Latin, General Punctuation)
    if n != ("u%04X" % c):
        if v == '': log.write("%s: Missing description.\n" % n)

        # glyphnames item from glyphdata
        glyphnames[n] = {
            'codepoint': d['codepoint'],
            'description': v }
        v = d.get('alternateCodepoint')
        if v: glyphnames['alternateCodepoint'] = v

        # Scheme alist element
        l += '  ("%s" . #x%04X)\n' % (n, d['code'])

    d.pop('name', 0)
    d.pop('ref', 0) # del raises an exception if 'ref' is not present

file = open(lilypath + "/" + mapname + ".ily", 'w', newline = "\n")
file.write(tpl.format(now.year, font.fullname, l))
file.close()


# collect metadata

metadata = {
    'fontName': font.fullname,
    'fontVersion': font.version,
    # 'designSize': 100,
    # 'sizeRange': [ 80, 160 ],
    'engravingDefaults': {
        'textFontFamily': [ "sans-serif" ], # not sure
        'staffLineThickness': upm(28),
        'legerLineThickness': upm(56),
        'legerLineExtension': upm(98),
        'stemThickness': upm(30),
        'beamThickness': upm(120),
        'beamSpacing': upm(80),
        'slurEndpointThickness': upm(28.4),
        'slurMidpointThickness': upm(50),
        'tieEndpointThickness': upm(28.4),
        'tieMidpointThickness': upm(42),
        'thinBarlineThickness': upm(47),
        'thickBarlineThickness': upm(147),
        'dashedBarlineThickness': upm(47),
        'dashedBarlineDashLength': upm(150),
        'dashedBarlineGapLength': upm(100),
        'barlineSeparation': upm(76),
        'thinThickBarlineSeparation': upm(76),
        'repeatBarlineDotSeparation': upm(76),
        'bracketThickness': upm(75),
        'subBracketThickness': upm(47),
        'hairpinThickness': upm(28),
        'octaveLineThickness': upm(42),
        'pedalLineThickness': upm(36),
        'repeatEndingLineThickness': 0.16, # from Bravura
        'arrowShaftThickness': upm(40),
        'lyricLineThickness': upm(55),
        'textEnclosureThickness': upm(40), # or upm(32) ?
        'tupletBracketThickness': 0.16, # from Bravura
        'hBarThickness': upm(164) }}


if len(anchor.data): metadata['glyphsWithAnchors'] = anchor.data
if len(glyphsWithAlternates): metadata['glyphsWithAlternates'] = glyphsWithAlternates
if len(ligatures): metadata['ligatures'] = ligatures
if len(glyphBBoxes): metadata['glyphBBoxes'] = glyphBBoxes
if len(optionalGlyphs): metadata['optionalGlyphs'] = optionalGlyphs
if len(sets): metadata['sets'] = sets


# write all json files
writeJSON(metapath + "/" + font.fontname.lower() + ".json", metadata)
writeJSON(metapath + "/classes.json", classes)
writeJSON(metapath + "/glyphnames.json", glyphnames)
writeJSON(metapath + "/glyphdata.json", glyphdata)
writeJSON(metapath + "/ekmelily.json", ekmelily)
writeJSON(metapath + "/ekmelib.json", ekmelib)

log.write("Glyphs:               %d\n" % len(glyphdata))
log.write("  SMuFL:              %d\n" % (countRecommended + countOptional))
log.write("    Recommended:      %d\n" % countRecommended)
log.write("      Accidentals:    %d\n" % countAccidental)
log.write("      Other:          %d\n" % (countRecommended - countAccidental))
log.write("    Optional:         %d\n" % countOptional)
log.write("  Unicode:            %d\n" % (countLatin +
                                          countPunctuation +
                                          countArrows +
                                          countMathematical +
                                          countTechnical +
                                          countBlock +
                                          countGeometric +
                                          countSymbols +
                                          countDingbats +
                                          countSymbolsArrows +
                                          countMusical +
                                          countSymbolsPict))
log.write("    Latin/ASCII:      %d\n" % countLatin)
log.write("    Punctuation:      %d\n" % countPunctuation)
log.write("    Arrows:           %d\n" % countArrows)
log.write("    Mathematical:     %d\n" % countMathematical)
log.write("    Technical:        %d\n" % countTechnical)
log.write("    Block Elements:   %d\n" % countBlock)
log.write("    Geometric Shapes: %d\n" % countGeometric)
log.write("    Symbols:          %d\n" % countSymbols)
log.write("    Dingbats:         %d\n" % countDingbats)
log.write("    Symbols/Arrows:   %d\n" % countSymbolsArrows)
log.write("    Musical Symbols:  %d\n" % countMusical)
log.write("    Symbols/Pict:     %d\n" % countSymbolsPict)
log.close()
