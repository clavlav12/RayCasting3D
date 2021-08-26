from collections import namedtuple
from glob import glob
from time import time
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

        self.texture = pg.image.load('Assets/Images/Textures/' + filename)  # .convert()
        self.array = pg.surfarray.array2d(self.texture)
        try:
            self.palette = self.texture.get_palette()
        except pg.error:
            print(filename, 'has no palette')
            self.palette = None
        self.id = id_


class Timer:
    """Used to time stuff eg. jump, fire etc."""

    def __init__(self, delay, active=False):
        self.delay = delay
        self.base_delay = delay
        self._is_counting = False
        self.start_time = -1
        if active:
            self.activate()

    @property
    def is_counting(self):
        if self.finished() and self._is_counting:
            self._is_counting = False
        return self._is_counting

    def reset(self):
        """Reset the clock"""
        self.start_time = time()

    def activate(self, new_time=None):
        """Activates the clock"""
        if new_time:
            self.delay = new_time
        else:
            self.delay = self.base_delay
        self.start_time = time()
        self._is_counting = True

    def __bool__(self):
        return self.time_to_finish() < 0

    def finished(self):
        """Returns true if the timer is done"""
        return bool(self)

    def time_to_finish(self):
        return self.delay - (time() - self.start_time)


class Animation:
    """Collection class to make animations easier"""
    _key = object()
    Frame = namedtuple('Frame', ('image', 'delay'))

    def __init__(self, dir_regex, fps, repeat, flip_x=False, flip_y=False, scale=1):
        """
        Generates an Animation object from a directory
        :param dir_regex:  directory path regex (string)
        :param fps: images per second (int)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        :return: Animation object (Animation)
        """

        self.images_list = [
            self.Frame(pg.transform.flip(pg.image.load(i), flip_x, flip_y).convert(), self.get_delay(i)) for i in glob(dir_regex)
        ]

        if scale != 1:
            self.images_list = [
                self.Frame(pg.transform.scale(i.image, (int(i.image.get_width() * scale),
                                                        int(i.image.get_height() * scale))).convert(), i.delay) for i in
                self.images_list]

        assert bool(self.images_list), "image list is empty"
        self.pointer = 0
        self.frames_per_second = fps
        self.timer = Timer(self.images_list[self.pointer].delay)
        self.repeat = repeat

    def get_image(self, update_pointer=True):
        """Next image in the animation list"""
        # 4 4 4 4 4 0
        if update_pointer and not self.finished():
            if self.timer.finished():
                self.update_pointer()
                self.timer.activate(self.images_list[self.pointer].delay)

        return self.images_list[self.pointer].image  # ??

    def update_pointer(self):
        """
        Updates the pointer. If it's too big stay on the last frame
        Returns weather or not the animation is over
        """
        self.pointer = 1 + self.pointer % len(self.images_list)
        if self.pointer >= len(self.images_list):  # ??
            if self.repeat:
                self.pointer = 0
            else:
                self.pointer -= 1
            return True
        return False

    def reset(self):
        """Takes the pointer back to the beginning"""
        self.pointer = 0
        self.timer.activate(self.images_list[self.pointer].delay)

    def finished(self):
        """Returns true if the animation is done and not set to repeat"""
        return (not self.repeat) and self.pointer == len(self.images_list) - 1 and self.timer.finished() # ??

    def __next__(self):
        return self.get_image()

    def get_next_size(self):
        """Returns the size of the next image"""
        return self.images_list[self.pointer].image.get_size()

    def __len__(self):
        return len(self.images_list)

    def set_pointer(self, new):
        self.pointer = new

    @staticmethod
    def get_delay(path):
        path = '.'.join(path.split('.')[:-1])
        path = path.split('-')[-1]
        path = path.replace('s', '')
        return float(path)
