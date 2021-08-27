import math

import pygame

import structures
from structures import RotationMatrix
from .Sprites import BaseSprite
from numba import njit
from FasterMap import Map


@njit()
def cast_sprite(world_sprite_x, world_sprite_y, pos_x, pos_y, plane_x, plane_y, dir_x, dir_y, W, H, z_buffer,
                text_width, text_height, camera_height, tilt):

    sprite_x = world_sprite_x - pos_x
    sprite_y = world_sprite_y - pos_y
    inv_det = 1 / (plane_x * dir_y - dir_x * plane_y)
    transform_x = inv_det * (dir_y * sprite_x - dir_x * sprite_y)
    transform_y = inv_det * (- plane_y * sprite_x + plane_x * sprite_y)

    sprite_screen_x = int((W // 2) * (1 + transform_x / transform_y))

    inv_height = 2 - camera_height

    u_div = 1
    v_div = 1

    draw_height = sprite_height = abs(int(H / transform_y / v_div))

    height_pixel = H // transform_y
    v_move_screen = height_pixel // 2 - sprite_height // 2
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

    y_start = int(col_start * pixels_per_texel + draw_start_y + .5)
    y_height = int(col_height * pixels_per_texel + .5)

    # draw_start_x = draw_start_x - draw_start_x % resolution + resolution
    for stripe in range(draw_start_x, draw_end_x):
        if z_buffer[stripe] > transform_y > 0 and W > stripe > 0:
            tex_x = int(256 * (stripe - (-sprite_width / 2 + sprite_screen_x)) * text_width / sprite_width) / 256
            yield stripe, col_start, col_height, y_start, y_height, tex_x


class BillboardSprite(BaseSprite):
    sprites = []

    def __init__(self, texture, position):
        super(BillboardSprite, self).__init__(position, (0, 0), 1, 1)  # change 1,1 later!
        self.sprites.append(self)
        self.texture = texture

    @classmethod
    def draw_all(cls, viewer_position, camera_plane, dir_, W, H, z_buffer, resolution, screen, height, tilt):
        cls.sprites.sort(key=lambda sprite: (sprite.position - viewer_position).magnitude_squared())

        for sprite in cls.sprites:
            sprite.draw_3D(viewer_position, camera_plane, dir_, W, H, z_buffer, resolution, screen, height, tilt)

    def draw_3D(self, viewer_position, camera_plane, dir_, W, H, z_buffer, resolution, screen, height, tilt):
        tex_height = self.texture.get_height()
        texture = self.texture
        pos = Map.instance.to_local(self.position)
        for x, col_start, col_height, y_start, y_height, tex_x in cast_sprite(
                pos[0], pos[1],
                viewer_position[0], viewer_position[1],
                camera_plane.x, camera_plane.y,
                dir_.x, dir_.y,
                W, H,
                z_buffer,
                self.texture.get_width(), self.texture.get_height(),
                height,
                tilt
        ):
            # if col_height > 0 and col_start < tex_height:
            column = texture.subsurface((tex_x, col_start, 1, col_height)).copy()
            column = pygame.transform.scale(column, (resolution, y_height))
            screen.blit(column, (x, y_start))
