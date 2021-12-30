import math

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

    u_div = horizontal_scale
    v_div = vertical_scale

    draw_height = sprite_height = abs(int(H / transform_y / v_div))
    height_pixel = H // transform_y
    v_move_screen = height_pixel // 2 - sprite_height // 2 + vertical_position // transform_y
    draw_start_y = - inv_height * sprite_height // 2 + H // 2 + v_move_screen + tilt

    sprite_width = abs(int(H / transform_y / u_div))

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

    # draw_start_x = draw_start_x - draw_start_x % resolution + resolution
    for stripe in range(draw_start_x, draw_end_x):
        if z_buffer[stripe] > transform_y > 0 and W > stripe > 0:
            tex_x = int(256 * (stripe - (-sprite_width / 2 + sprite_screen_x)) * text_width / sprite_width) / 256
            yield stripe, y_texture_start, y_start, y_height, tex_x, draw_height
                   #x, y_texture_start, y_start, y_height, tex_x, draw_height in cast_sprite(


class BillboardSprite(BaseSprite):
    billboard_sprites = []
    # self.texture = AnimationDescriptor()

    def __init__(self, texture, position, vertical_position=0, vertical_scale=1, horizontal_scale=1):
        super(BillboardSprite, self).__init__(position, (0, 0), 1, 1)  # change 1,1 later!
        self.billboard_sprites.append(self)

        self.set_animation(texture)

        self.vertical_position = vertical_position
        self.vertical_scale = vertical_scale
        self.horizontal_scale = horizontal_scale

        self.texture_cache = {}

    def set_animation(self, texture, repeat=False, fps=None):
        if isinstance(texture, str):
            if os.path.isfile(texture):
                texture = pg_structures.Animation([pygame.image.load(texture)], repeat, fps)
            else:  # directory
                texture = pg_structures.Animation.by_directory(texture, repeat, fps=fps, )
        if isinstance(texture, pygame.Surface):
            self.animation = pg_structures.Animation([texture], repeat, fps)
        elif isinstance(texture, pg_structures.Animation):
            self.animation = texture

    @classmethod
    def draw_all(cls, viewer_position, camera_plane, dir_, W, H, z_buffer, resolution, screen, height, tilt, global_val):
        converted_viewer_position = Map.instance.to_global(viewer_position)
        cls.billboard_sprites.sort(key=lambda sprite: (sprite.position - converted_viewer_position).magnitude_squared(), reverse=True)

        for sprite in cls.billboard_sprites:
            sprite.draw_3D(viewer_position, camera_plane, dir_, W, H, z_buffer, resolution, screen, height, tilt, global_val)

    def draw_3D(self, viewer_position, camera_plane, dir_, W, H, z_buffer, resolution, screen, height, tilt, global_val):
        texture = self.get_current_texture()
        try:
            texture_cache = self.texture_cache[texture]
        except KeyError:
            texture_cache = self.texture_cache[texture] = {}

        tex_height = texture.get_height()
        pos = Map.instance.to_local(self.position)
        scaled_texture = None
        for x, y_texture_start, y_start, y_height, tex_x, draw_height in cast_sprite(
                pos[0], pos[1],
                viewer_position[0], viewer_position[1],
                camera_plane.x, camera_plane.y,
                dir_.x, dir_.y,
                W, H,
                z_buffer,
                texture.get_width(), texture.get_height(),
                height,
                tilt,
                self.vertical_position,
                self.vertical_scale,
                self.horizontal_scale,

        ):
            # if global_val > 0:
            #     y_height *= 1.2
            # y_height - actual height drawn to screen
            # draw_height - supposing "height"
            # 4275 1069 4275
            # print(pixels_per_texel)
            # print(int(pixels_per_texel * texture.get_height()), y_height, draw_height, y_height == draw_height)
            if scaled_texture is None:
                scaled_texture = self.texture_cache.get(draw_height, None)
                if scaled_texture is None:
                    scaled_texture = pygame.transform.scale(texture, (resolution * texture.get_width(),
                                                                      draw_height))
                    texture_cache[draw_height] = scaled_texture
                #
            # if col_height > 0 and col_start < tex_height:
            try:
                cr = resolution
                start = round(tex_x) * resolution
                if start + resolution > scaled_texture.get_width():
                    cr = scaled_texture.get_width() - start
                column = scaled_texture.subsurface((start, y_texture_start, cr, y_height))
            except Exception as e:

                # continue
                raise e

            if global_val > 0:
                # column = pygame.transform.scale(column, (resolution, y_height), )
                screen.blit(column, (x, y_start))

    def get_current_texture(self):
        return self.animation.get_image()


class LostSoul(BillboardSprite):
    def __init__(self, texture, position):
        super(LostSoul, self).__init__(texture, position)
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

    def update(self, dt, keys):
        dt = min(1/15, dt)
        #print(self.vertical_position, self.frequency * self.amplitude * math.cos(dt * self.frequency), math.cos(dt * self.frequency))
        self.vertical_velocity += -(self.vertical_position - self.offset) * self.frequency ** 2
        self.vertical_position += self.vertical_velocity * dt

    def set_animation(self, texture):
        super(LostSoul, self).set_animation(texture, fps=5)
        self.animation.modify_images(lambda x: x.set_colorkey((0, 255, 255)))

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
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = sys.getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
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