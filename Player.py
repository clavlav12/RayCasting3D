import structures
import pygame
import FasterMap as Map
import pg_structures

from Sprites3D.Sprites import BaseSprite
from Sprites3D.BillboardSprite import BillboardSprite

dx = 0.000001


class Player(BillboardSprite):
    RECT_SIZE = 10

    def __init__(self, x=0, y=0, speed=500):
        self.distance_from_wall = 10
        super(Player, self).__init__(None, (x, y), velocity=(0, 0), rect_size=(self.RECT_SIZE, self.RECT_SIZE), tilt=0)
        self.key_to_function = {}
        self.speed = speed
        self.moving_direction = structures.Vector2(0, 0)
        self.looking_direction = structures.Vector2(0.88838, 0.45911)
        self.setup_movement()

    def move(self, keys, dt):
        self.moving_direction.x = 0
        self.moving_direction.y = 0
        for key, function in self.key_to_function.items():
            if keys[key]:
                function()

        self.velocity = self.speed * self.moving_direction

    def set_moving_direction(self, x=None, y=None):
        if self.moving_direction:
            self.moving_direction = self.moving_direction.normalized()
        self.moving_direction += structures.Vector2(x or 0, y or 0)
        if self.moving_direction:
            self.moving_direction = self.moving_direction.normalized()

    def setup_movement(self):
        self.up_down_left_right_movements()

    def up_down_left_right_movements(self):
        self.key_to_function[pygame.K_UP] = lambda: self.set_moving_direction(y=-1)
        self.key_to_function[pygame.K_DOWN] = lambda: self.set_moving_direction(y=1)
        self.key_to_function[pygame.K_LEFT] = lambda: self.set_moving_direction(x=-1)
        self.key_to_function[pygame.K_RIGHT] = lambda: self.set_moving_direction(x=1)


class Weapon:

    def __init__(self, animation_directory, fps, fire_rate, screen):
        self.animation = pg_structures.Animation.by_directory(animation_directory + '/*.gif', False, fps, scale=3)
        self.animation.set_pointer(-1)
        self.shooting = False

        self.wait_to_finish = fire_rate == -1

        if self.wait_to_finish:
            fire_rate = float('inf')
        self.fire_timer = pg_structures.Timer(1 / fire_rate)

        rect = self.animation.get_image(False).texture.get_rect()
        rect.center = screen.get_rect().center
        rect.bottom = screen.get_rect().bottom
        self.rect = rect
        self.screen = screen

    def shoot(self):
        if self.fire_timer.finished() and ((not self.wait_to_finish) or self.animation.finished()):
            self.shooting = True
            self.animation.reset()
            self.fire_timer.activate()
        else:
            self.shoot_next = True

    def draw(self):
        next_image = self.animation.get_image().texture
        if self.animation.finished():
            self.shooting = False

        self.screen.blit(next_image, self.rect)
