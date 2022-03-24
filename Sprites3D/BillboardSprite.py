import math
import pathlib

import pygame

import structures
import pg_structures
from structures import RotationMatrix
from .Sprites import BaseSprite
from numba import njit
from FasterMap import Map
import os
from itertools import chain
import sys


# class AnimationDescriptor:
# def __init__(self, texture):
#     if isinstance(texture)
# def __set_name__(self, owner, name):
#     self.name = name
#
# def __get__(self, instance, owner):
#     pass
#
# def __set__(self, instance, value):
#     if isinstance(value, pygame.Surface):
#         instance.__dict__[self.name] = value

class RenderSettings:
    Fov = 90
    Resolution = 3

    @classmethod
    def fov(cls):
        return cls.Fov

    @classmethod
    def resolution(cls):
        return cls.Resolution


@njit()
def cast_sprite(world_sprite_x, world_sprite_y, pos_x, pos_y, plane_x, plane_y, dir_x, dir_y, W, H, z_buffer,
                text_width, text_height, camera_height, tilt, vertical_position, vertical_scale, horizontal_scale):
    sprite_x = world_sprite_x - pos_x
    sprite_y = world_sprite_y - pos_y
    inv_det = 1 / (plane_x * dir_y - dir_x * plane_y)
    transform_x = inv_det * (dir_y * sprite_x - dir_x * sprite_y)
    transform_y = inv_det * (- plane_y * sprite_x + plane_x * sprite_y)

    sprite_screen_x = int((W // 2) * (1 + transform_x / transform_y))

    inv_height = 2 - camera_height
    draw_height = sprite_height = abs(int(H / transform_y / vertical_scale))
    height_pixel = H // transform_y
    v_move_screen = height_pixel - sprite_height + (vertical_position) // transform_y
    draw_start_y = - inv_height * height_pixel // 2 + H // 2 + v_move_screen + tilt
    # draw_start_y = - H // transform_y // 2 + H // 2

    sprite_width = abs(int(H / transform_y / horizontal_scale))

    draw_start_x = -sprite_width // 2 + sprite_screen_x
    if draw_start_x < 0:
        draw_start_x = 0

    draw_end_x = sprite_width // 2 + sprite_screen_x

    if draw_end_x > W:
        draw_end_x = W

    y_start = max(0, draw_start_y)
    y_stop = min(H, draw_height + draw_start_y)

    pixels_per_texel = draw_height / text_height

    col_start = int((y_start - draw_start_y) / pixels_per_texel + .5)
    col_height = int((y_stop - y_start) / pixels_per_texel + .5)

    if col_height < 0 or col_start + col_height > text_height:
        return

    y_texture_start = col_start * pixels_per_texel
    y_start = int(y_texture_start + draw_start_y + .5)
    y_height = int(col_height * pixels_per_texel + .5)

    # y_height *= vertical_scale
    # draw_start_x = draw_start_x - draw_start_x % resolution + resolution
    for stripe in range(draw_start_x, draw_end_x):
        if z_buffer[stripe] > transform_y > 0 and W > stripe > 0:
            tex_x = int(256 * (stripe - (-sprite_width / 2 + sprite_screen_x)) * text_width / sprite_width) / 256
            yield stripe, y_texture_start, y_start, y_height, tex_x, draw_height
            # x, y_texture_start, y_start, y_height, tex_x, draw_height in cast_sprite(


class BillboardSprite(BaseSprite):
    billboard_sprites = []

    # self.texture = AnimationDescriptor()

    def __init__(self, texture, position, vertical_position=0, vertical_scale=1, horizontal_scale=1, velocity=(0, 0),
                 fps=None, looking_direction=structures.Vector2(1, 0), resolution=RenderSettings.resolution(),
                 tilt=None, rect_size=(1, 1)):  # change 1,1 later!
        super(BillboardSprite, self).__init__(position, velocity, *rect_size)
        self.tilt = tilt
        self.billboard_sprites.append(self)

        self.resolution = resolution
        self.animation = self.get_animation(texture, fps=fps)

        self.vertical_position = vertical_position
        self.vertical_scale = vertical_scale
        self.horizontal_scale = horizontal_scale

        self.looking_direction = looking_direction
        self.texture_cache = {}

    def check_resolution(self, texture: pg_structures.Texture):
        if not self.resolution == texture.scaled_resolution:
            return texture.copy(texture)
        return texture

    def get_animation(self, texture, repeat=False, fps=None):
        if isinstance(texture, str):
            try:
                texture = pg_structures.Texture[texture]
                if isinstance(texture, pg_structures.Texture):  # single texture
                    texture = self.check_resolution(texture)
                    texture = pg_structures.Animation([texture], repeat, fps)

                elif isinstance(texture, dict):  # directory
                    texture = pg_structures.Animation(list(map(self.check_resolution,
                                                               filter(
                                                                   lambda item: isinstance(item, pg_structures.Texture),
                                                                   texture.values())
                                                               )
                                                           ), repeat, fps)

            except KeyError:  # not loaded
                if os.path.isfile(texture):
                    texture = pg_structures.Animation([
                        pg_structures.Texture(texture, self.resolution)], repeat, fps)
                else:  # directory
                    texture = pg_structures.Animation.by_directory(texture, repeat, fps=fps,
                                                                   texture_handler_resolution=self.resolution)
        if isinstance(texture, pygame.Surface):
            texture = pg_structures.Texture(texture, self.resolution)

        if isinstance(texture, pg_structures.Texture):
            return pg_structures.Animation([texture], repeat, fps)
        elif isinstance(texture, pg_structures.Animation):
            return texture

    @classmethod
    def draw_all(cls, viewer, camera_plane_length, W, H, z_buffer, resolution, screen):
        viewer: BillboardSprite
        cls.billboard_sprites.sort(key=lambda sprite: (sprite.position - viewer.position).magnitude_squared(),
                                   reverse=True)

        for sprite in cls.billboard_sprites:
            sprite.draw_3D(viewer, camera_plane_length, W, H, z_buffer, resolution, screen)

    def self_draw(self):
        pass

    def draw_3D(self, viewer, camera_plane_length, W, H, z_buffer, resolution, screen):
        viewer: BillboardSprite
        if viewer is self:
            return self.self_draw()

        viewer_position = Map.instance.to_local(viewer.position)
        texture = self.get_current_texture()
        image = texture.texture

        dir_ = viewer.looking_direction.normalized()
        camera_plane = dir_.tangent() * camera_plane_length

        pos = Map.instance.to_local(self.position)

        for x, y_texture_start, y_start, y_height, tex_x, draw_height in cast_sprite(
                pos[0], pos[1],
                viewer_position[0], viewer_position[1],
                camera_plane.x, camera_plane.y,
                dir_.x, dir_.y,
                W, H,
                z_buffer,
                image.get_width(), image.get_height(),
                viewer.vertical_position,
                viewer.tilt,
                self.vertical_position,
                self.vertical_scale,
                self.horizontal_scale,

        ):
            column = texture.get_stripe(tex_x, draw_height, y_texture_start, y_height)
            if column is not None:
                screen.blit(column, (x, y_start))

    def get_current_texture(self):
        return self.animation.get_image()


class LostSoul(BillboardSprite):
    def __init__(self, texture, position, resolution):
        super(LostSoul, self).__init__(texture, position, resolution, fps=2)
        self.animation.repeat = True
        self.amplitude = 50
        self.offset = -200
        self.frequency = .5

        # p = amplitude * sin(t * frequency) + offset
        # v = frequency * amplitude * sin(t * frequency) + offset
        # a = - frequency * frequency * amplitude * sin(t * frequency) + offset
        self.vertical_position = self.offset + self.amplitude  # p = amplitude * sin(t * frequency) + offset
        self.vertical_velocity = 0
        self.vertical_acceleration = 0  # F  = - k * dx, set k to 0 then F = - dx
        # so different from previous frame is = frequency * amplitude * cos(dt * frequency)

    def update_aft(self, dt, keys):
        dt = min(1 / 15, dt)
        # print(self.vertical_position, self.frequency * self.amplitude * math.cos(dt * self.frequency), math.cos(dt * self.frequency))
        self.vertical_velocity += -(self.vertical_position - self.offset) * self.frequency ** 2
        self.vertical_position += self.vertical_velocity * dt

    def get_animation(self, texture, repeat=False, fps=None):
        animation = super(LostSoul, self).get_animation(texture, repeat, fps)
        animation.modify_images(lambda x: x.set_colorkey((0, 255, 255)), False)
        return animation

    def get_current_texture(self):
        return super(LostSoul, self).get_current_texture()


def total_size(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                    }
    all_handlers.update(handlers)  # user handlers take precedence
    seen = set()  # track which object id's have already been seen
    default_size = sys.getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = sys.getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=sys.stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)
