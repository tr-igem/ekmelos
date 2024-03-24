#! /usr/bin/env python
# -*- coding: utf-8 -*-

##
## cutout.py
##
## Script for FontForge generating the bounding box cut-outs for each
## selected glyph in the currently active font.
##
## Determines for each corner of the bounding box the largest rectangle
## which lies outside of the contours in the foreground layer.
## Reduces the width and height of each rectangle by 5% or at least
## by 1.5% of the em size.
## Draws those rectangles whose width and height are at least 1% of the
## em size into the special layer "Cutout". Adds this layer to the font
## if necessary.
## The first point of each rectangle is always the inner corner and has
## integer coordinates.
##
## The rectangles can be manually adjusted or removed.
## For the "cutOut*" metadata, only the first and the third (diametric)
## point of each contour is used. The third point must be at a corner
## of the bounding box. The first point must have a minimum distance
## of 10 upm from the bounding box.
##
## Note: A glyph should not have overlapping areas. The result is
## possibly not correct if there are two or more separate countours.
##
## Written by Thomas Richter (<thomas-richter@aon.at>), September 2020
## This program is free software. Use, redistribute, and modify it as you wish.
##

import fontforge
import math


layerName = "Cutout"
font = fontforge.activeFont()

# font (em size) specific metrics
widthMin = int(font.em * 0.01)
heightMin = int(font.em * 0.01)
shrinkBy = 0.05
shrinkMin = int(font.em * 0.015)

MAX = 10000


class Cutout:
    """Data of a cut-out rectangle"""
    def __init__(self, x, y):
        self.dx = x
        self.dy = y
        self.cx = x * MAX  # combined inner corner of all contours
        self.cy = y * MAX

    def reset(self):
        self.x = self.dx * MAX
        self.y = self.dy * MAX
        self.xm = self.dx * MAX
        self.area = 0
        self.go = True

    def extent(self, x, y):
        w = xMax - x if -1 == self.dx else x - xMin
        h = yMax - y if -1 == self.dy else y - yMin
        return (w, h)

    def fit(self, x, y):
        if count == 0:  # first real point
            self.area = 0

        if -1 == self.dx:  # SE,NE
            x = int(math.ceil(x))
            if xMax - x < widthMin:  # too small
                self.go = False
                return True
            x = max(x, self.xm)
        else:  # SW,NW
            x = int(math.floor(x))
            if x - xMin < widthMin:  # too small
                self.go = False
                return True
            x = min(x, self.xm)

        self.xm = x  # outermost x
        (w, h) = self.extent(x, y)
        a = w * h
        if a >= self.area:  # find largest rectangle
            self.x = x  # inner corner
            self.y = y
            self.area = a
        return False

    def finish(self):
        """Reduce the rectangle and return True if it is large enough"""
        if MAX == abs(self.cx):
            return False
        (w, h) = self.extent(self.cx, self.cy)
        sw = max(int(w * shrinkBy), shrinkMin)
        sh = max(int(h * shrinkBy), shrinkMin)
        self.x = self.cx - sw * self.dx
        self.y = self.cy - sh * self.dy
        return w - sw >= widthMin and h - sh >= heightMin


# add new layer for cutout rects
if layerName not in font.layers:
    font.layers.add(layerName, False, True)


# generate cutout rects in all selected glyphs
for g in font.selection.byGlyphs:
    b = g.boundingBox()
    xMin = b[0]
    xMax = b[2]
    yMin = b[1]
    yMax = b[3]
    yMaxI = int(yMax)

    boundsEmpty = (xMax, xMin)

    # cutout rects
    SE = Cutout(-1, 1)
    SW = Cutout(1, 1)
    NE = Cutout(-1, -1)
    NW = Cutout(1, -1)

    # countContours = 0

    # all outer (clockwise) contours in foreground layer
    for c in g.layers[1]:
        if not c.isClockwise(): continue

        # countContours += 1
        # if countContours == 2: continue

        SE.reset()
        SW.reset()
        NE.reset()
        NW.reset()

        # max y of SE and SW = min y of NE and NW
        yMinE = yMaxI
        yMinW = yMaxI

        # determine SE and SW rect from bottom upward
        # until top is reached or width of rect is too small
        count = -1
        for y in range(int(yMin), yMaxI + 1):
            b = c.xBoundsAtY(y)
            if None == b:
                b = boundsEmpty
            else:
                count += 1

            if SE.go and SE.fit(b[1], y):
                yMinE = y

            if SW.go and SW.fit(b[0], y):
                yMinW = y

            if not (SE.go or SW.go):
                break

        # determine NE and NW rect from top downward
        # until top of SE and SW is reached or width of rect is too small
        count = -1
        for y in range(yMaxI, min(yMinE, yMinW), -1):
            b = c.xBoundsAtY(y)
            if None == b:
                b = boundsEmpty
            else:
                count += 1

            if NE.go and y > yMinE:
                NE.fit(b[1], y)

            if NW.go and y > yMinW:
                NW.fit(b[0], y)

            if not (NE.go or NW.go):
                break

        # combine with rects of former contours
        SE.cx = max(SE.cx, SE.x)
        SE.cy = min(SE.cy, SE.y)

        SW.cx = min(SW.cx, SW.x)
        SW.cy = min(SW.cy, SW.y)

        NE.cx = max(NE.cx, NE.x if NE.area else SE.x)
        NE.cy = max(NE.cy, NE.y if NE.area else yMin)

        NW.cx = min(NW.cx, NW.x if NW.area else SW.x)
        NW.cy = max(NW.cy, NW.y if NW.area else yMin)


    # reduce and draw final rects
    g.activeLayer = layerName

    pen = g.glyphPen()

    if NE.finish():
        pen.moveTo(NE.x, NE.y)
        pen.lineTo(NE.x, yMax)
        pen.lineTo(xMax, yMax)
        pen.lineTo(xMax, NE.y)
        pen.closePath()

    if NW.finish():
        pen.moveTo(NW.x, NW.y)
        pen.lineTo(xMin, NW.y)
        pen.lineTo(xMin, yMax)
        pen.lineTo(NW.x, yMax)
        pen.closePath()

    if SE.finish():
        pen.moveTo(SE.x, SE.y)
        pen.lineTo(xMax, SE.y)
        pen.lineTo(xMax, yMin)
        pen.lineTo(SE.x, yMin)
        pen.closePath()

    if SW.finish():
        pen.moveTo(SW.x, SW.y)
        pen.lineTo(SW.x, yMin)
        pen.lineTo(xMin, yMin)
        pen.lineTo(xMin, SW.y)
        pen.closePath()

    pen = None
