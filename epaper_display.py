#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EpaperState:
    enabled: bool = False
    width: int = 250
    height: int = 122


class EpaperDisplay:
    """
    Lightweight wrapper for Waveshare 2.13" V4 e-paper.
    Falls back gracefully if dependencies are not available.
    """

    def __init__(self, enabled: bool = False) -> None:
        self.state = EpaperState(enabled=enabled)
        self._epd = None
        self._image = None
        self._draw = None
        self._font = None
        self._ok = False

        if not enabled:
            return

        try:
            from PIL import Image, ImageDraw, ImageFont
            from waveshare_epd import epd2in13_V4
        except Exception:
            return

        try:
            self._epd = epd2in13_V4.EPD()
            self._epd.init()
            self._epd.Clear(0xFF)
            self.state.width = self._epd.height
            self.state.height = self._epd.width
            self._image = Image.new("1", (self.state.width, self.state.height), 255)
            self._draw = ImageDraw.Draw(self._image)
            self._font = ImageFont.load_default()
            self._ok = True
        except Exception:
            self._ok = False

    @property
    def ready(self) -> bool:
        return self._ok

    def show(self, title: str, lines: list[str]) -> None:
        if not self._ok:
            return

        assert self._draw is not None
        assert self._image is not None
        assert self._font is not None
        assert self._epd is not None

        self._draw.rectangle((0, 0, self.state.width, self.state.height), fill=255)
        y = 2
        self._draw.text((2, y), title[:36], font=self._font, fill=0)
        y += 16
        for line in lines[:6]:
            self._draw.text((2, y), line[:38], font=self._font, fill=0)
            y += 16

        self._epd.display(self._epd.getbuffer(self._image))

    def sleep(self) -> None:
        if not self._ok:
            return
        try:
            self._epd.sleep()
        except Exception:
            pass
