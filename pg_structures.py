import pygame as pg
import numpy as np
from win32api import GetSystemMetrics


class DisplayMods:
    BASE_WIDTH = 1728
    BASE_HEIGHT = 972

    current_width = BASE_WIDTH
    current_height = BASE_HEIGHT

    MONITOR_WIDTH = GetSystemMetrics(0)
    MONITOR_HEIGHT = GetSystemMetrics(1)
    # MONITOR_WIDTH = 1680
    # MONITOR_HEIGHT = 1080
    MONITOR_RESOLUTION = (MONITOR_WIDTH, MONITOR_HEIGHT)

    @classmethod
    def get_resolution(cls):
        return cls.current_width, cls.current_height

    @classmethod
    def FullScreen(cls):
        return pg.display.set_mode(cls.MONITOR_RESOLUTION, pg.FULLSCREEN)

    @classmethod
    def FullScreenAccelerated(cls):
        return pg.display.set_mode(cls.MONITOR_RESOLUTION, pg.HWSURFACE)

    @classmethod
    def WindowedFullScreen(cls):
        return pg.display.set_mode(cls.MONITOR_RESOLUTION, pg.NOFRAME, display=0)

    @classmethod
    def Windowed(cls, size):
        cls.current_width, cls.current_height = size
        return pg.display.set_mode((cls.current_width, cls.current_height))

    @classmethod
    def Resizable(cls, size):
        cls.current_width, cls.current_height = size
        return pg.display.set_mode((cls.current_width, cls.current_height), pg.RESIZABLE)


def draw_line_dashed(surface, color, start_pos, end_pos, width=1, dash_length=10, exclude_corners=True):
    # convert tuples to numpy arrays
    start_pos = np.array(start_pos)
    end_pos = np.array(end_pos)

    # get euclidian distance between start_pos and end_pos
    length = np.linalg.norm(end_pos - start_pos)

    # get amount of pieces that line will be split up in (half of it are amount of dashes)
    dash_amount = int(length / dash_length)

    # x-y-value-pairs of where dashes start (and on next, will end)
    dash_knots = np.array([np.linspace(start_pos[i], end_pos[i], dash_amount) for i in range(2)]).transpose()

    return [pg.draw.line(surface, color, tuple(dash_knots[n]), tuple(dash_knots[n + 1]), width)
            for n in range(int(exclude_corners), dash_amount - int(exclude_corners), 3)]
