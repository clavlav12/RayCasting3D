import pygame as pg
import numpy as np
from win32api import GetSystemMetrics
from typing import Union


def screen_maker(func):
    """Decorator - creates a screen, then updates class's properties"""
    def inner(*args, **kwargs):
        val = func(DisplayMods, *args, **kwargs)
        size = val.get_size()
        DisplayMods.current_width, DisplayMods.current_height = size
        DisplayMods.current_resolution = size
        return val
    return inner


class DisplayMods:
    BASE_WIDTH = 1728
    BASE_HEIGHT = 972

    current_width = BASE_WIDTH
    current_height = BASE_HEIGHT
    current_resolution = (current_width, current_height)

    MONITOR_WIDTH = GetSystemMetrics(0)
    MONITOR_HEIGHT = GetSystemMetrics(1)
    # MONITOR_WIDTH = 1680
    # MONITOR_HEIGHT = 1080
    MONITOR_RESOLUTION = (MONITOR_WIDTH, MONITOR_HEIGHT)

    @classmethod
    def get_resolution(cls):
        """Returns the current resolution of the screen"""
        return cls.current_width, cls.current_height

    @screen_maker
    def FullScreen(cls):
        """Generates a fullscreen display"""
        return pg.display.set_mode(cls.MONITOR_RESOLUTION, pg.FULLSCREEN)

    @screen_maker
    def FullScreenAccelerated(cls):
        """Generates a fullscreen display, hardware accelerated."""
        return pg.display.set_mode(cls.MONITOR_RESOLUTION, pg.HWSURFACE | pg.DOUBLEBUF)

    @screen_maker
    def WindowedFullScreen(cls):
        """Generates a windowed fullscreen display"""
        return pg.display.set_mode(cls.MONITOR_RESOLUTION, pg.NOFRAME, display=0)

    @screen_maker
    def Windowed(cls, size):
        """Generates a windowed display"""
        cls.current_width, cls.current_height = size
        return pg.display.set_mode((cls.current_width, cls.current_height))

    @screen_maker
    def Resizable(cls, size):
        """Generates a resizable windowed display"""
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


class Textures:
    textures_num = 10
    __textures = [None] * textures_num

    def __init__(self, id_: Union[int, type(None)], filename: str):
        if not filename.endswith('.png'):
            filename += '.png'

        if id_ is not None:  # ceiling or floor texture
            if not self.textures_num > id_ > 0:
                raise ValueError(f'id is not between 0 and {self.textures_num}')
            if self.__textures[id_] is not None:
                raise ValueError('id already taken')

            Textures.__textures[id_] = self

        self.texture = pg.image.load('Assets/Images/Textures/' + filename)# .convert()
        self.array = pg.surfarray.array2d(self.texture)
        try:
            self.palette = self.texture.get_palette()
        except pg.error:
            print(filename, 'has no palette')
            self.palette = None
        self.id = id_

