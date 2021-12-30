from collections import namedtuple
from glob import glob
from time import time
import pygame as pg
import numpy as np
from win32api import GetSystemMetrics
from typing import Union
from PIL import Image
import pathlib
import os


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


class TextureMeta(type):
    def __init__(self, *args, **kwargs):
        self.textures = {}
        super(TextureMeta, self).__init__(*args, **kwargs)

    def __getitem__(self, path):
        p = pathlib.Path(path)
        split = p.parts
        dir_dict = self.textures
        for part in split[2:-1]:
            dir_dict = dir_dict[part]
        return dir_dict[p.stem]


class Texture(metaclass=TextureMeta):
    @classmethod
    def initiate_handler(cls, resolution):
        # create all textures from the assets folder recursively
        cls._initiate_handler('Assets/Images', cls.textures, resolution)

    @classmethod
    def _initiate_handler(cls, folder, folder_dictionary, scaled_resolution):
        # create all textures from the assets folder recursively
        for item in os.listdir(folder):
            full_path = os.path.join(folder, item)
            if os.path.isdir(full_path):
                folder_dictionary[item] = next = {}
                cls._initiate_handler(full_path, next, scaled_resolution)
            else:
                if item.endswith('.png') or item.endswith('.jpg'):
                    filename = os.path.splitext(item)[0]  # remove the extension
                    if filename in folder_dictionary:
                        raise ValueError(f'Two textures named "{filename}"')
                    folder_dictionary[filename] = cls(full_path, scaled_resolution)

    def __init__(self, full_path, scaled_resolution):
        self.name = full_path
        self.texture = pg.image.load(full_path).convert()

        self.scaled_resolution = scaled_resolution

        self.scaling_cache = {}  # height: scaled texture

    def change_resolution(self, new_resolution):
        self.scaled_resolution = new_resolution
        if self.scaling_cache is not None:
            self.scaling_cache.clear()

    def disable_scale_caching(self):
        self.scaling_cache = None

    def get_stripe(self, x, full_height, stripe_y_start, stripe_height):
        if (self.scaling_cache is None) or (full_height not in self.scaling_cache):
            scaled_texture = pg.transform.scale(self.texture, (self.scaled_resolution * self.texture.get_width(),
                                                               full_height))
            if self.scaling_cache is not None:
                self.scaling_cache[full_height] = scaled_texture
        else:
            scaled_texture = self.scaling_cache[full_height]
        # if col_height > 0 and col_start < tex_height:
        try:
            resolution = self.scaled_resolution
            start = round(x) * resolution
            if start + resolution > scaled_texture.get_width():
                resolution = self.scaled_resolution.get_width() - start
            return scaled_texture.subsurface((start, stripe_y_start, resolution, stripe_height))
        except Exception as e:
            pass
            # raise e


class IndexedTexture(Texture):
    def __init__(self, texture: Texture):
        super(IndexedTexture, self).__init__(texture.name, texture.scaled_resolution)
        self.array = None
        self.palette = None
        p = pathlib.Path(texture.name)
        split = p.parts
        dir_dict = Texture.textures
        for part in split[2:-1]:
            dir_dict = dir_dict[part]
        dir_dict[p.stem] = self
        try:
            self.palette = self.texture.get_palette()
            self.indexed_texture = self.texture
        except pg.error:
            im = Image.open(self.name)
            im = im.quantize(colors=256, method=2)

            im.save('temp.png')
            self.indexed_texture = pg.image.load('temp.png')
            self.palette = self.indexed_texture.get_palette()
            os.remove('temp.png')
        self.load_array()

    def load_array(self):
        self.array = pg.surfarray.array2d(
            self.indexed_texture)


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
    Frame = namedtuple('Frame', ('image', 'delay'))

    @classmethod
    def by_directory(cls, dir_regex, repeat, flip_x=False, flip_y=False, scale=1, fps=None, use_texture_handler=False):
        """
        Generates an Animation object from a directory
        :param use_texture_handler: Whether the surface should be obtained from the texture handler or
            from pygame.image.load
        :param dir_regex:  directory path regex (string)
        :param fps: images per second (int) if none number is derived from file name (see Assets/Weapons/pistol for example)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        :return: Animation object (Animation)
        """
        # if use_texture_handler:
        files_list = glob(dir_regex)
        average_delay = 1 / (fps or len(files_list))
        images_list = [
            cls.Frame(pg.transform.flip(pg.image.load(i), flip_x, flip_y).convert(), cls.get_delay(i) or average_delay)
            for i in files_list
        ]

        if scale != 1:
            images_list = [
                cls.Frame(pg.transform.scale(i.image, (int(i.image.get_width() * scale),
                                                       int(i.image.get_height() * scale))).convert(), i.delay) for i in
                images_list]

        return cls(images_list, repeat, fps)

    def __init__(self, images_list, repeat, fps=None):
        """
        Generates an Animation object from an images_list
        :param images_list:  list of pygame surfaces representing the individual frames of the animation
        :param fps: images per second (int)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        :return: Animation object (Animation)
        """
        if len(images_list) == 1:
            fps = 1
        if fps is not None and (all(isinstance(i, pg.Surface) for i in images_list)):
            delay = 1 / fps
            self.images_list = [self.Frame(image, delay) for image in images_list]
        elif all(isinstance(i, self.Frame) for i in images_list):
            self.images_list = images_list
        else:
            raise ValueError("Can't process image_list")
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
        return (not self.repeat) and self.pointer == len(self.images_list) - 1 and self.timer.finished()  # ??

    def __next__(self):
        return self.get_image()

    def get_next_size(self):
        """Returns the size of the next image"""
        return self.images_list[self.pointer].image.get_size()

    def __len__(self):
        return len(self.images_list)

    def set_pointer(self, new):
        self.pointer = new

    def modify_images(self, modifier, set_new=False):
        for index in range(len(self.images_list)):
            image = self.images_list[index].image
            new = modifier(image)
            if set_new:
                self.images_list[index] = self.Frame(new, self.images_list[index].delay)

    @staticmethod
    def get_delay(path):
        try:
            path = '.'.join(path.split('.')[:-1])
            path = path.split('-')[-1]
            path = path.replace('s', '')
            return float(path)
        except ValueError:
            return None
