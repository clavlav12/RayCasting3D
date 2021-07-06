import structures
import pygame
import FasterMap as Map

dx = 0.000001


class Player:
    def __init__(self, x=0, y=0, speed=500):
        self.key_to_function = {}
        self.speed = speed
        self.distance_from_wall = 10
        self.position = structures.Vector2(x, y)
        self.moving_direction = structures.Vector2(0, 0)
        self.looking_direction = structures.Vector2(0.88838, 0.45911)
        self.setup_movement()

    def key_func(self, keys):
        self.moving_direction.x = 0
        self.moving_direction.y = 0
        for key, function in self.key_to_function.items():
            if keys[key]:
                function()

    def update(self, dt, keys):
        self.key_func(keys)
        self.move(dt)

    def move(self, dt):
        shift = self.moving_direction * self.speed * dt

        self.position.x += shift.x
        self.x_collision(shift)

        self.position.y += shift.y
        self.y_collision(shift)

    def x_collision(self, shift):
        platform = self.platform_rect_check()
        if platform is not None:
            platform: pygame.Rect
            if shift.x > 0:  # Moved right, move it back left
                self.position.x = platform.left - self.distance_from_wall / 2 - dx
            else:  # Moved left, move it back right
                self.position.x = self.distance_from_wall / 2 + platform.right + dx
        return platform

    def y_collision(self, shift):
        platform = self.platform_rect_check()
        if platform is not None:
            platform: pygame.Rect
            if shift.y > 0:  # Moved down, move it back up
                self.position.y = platform.top - self.distance_from_wall / 2 - dx
            else:  # Moved up, move it back down
                self.position.y = self.distance_from_wall / 2 + platform.bottom + dx
        return platform


    def platform_rect_check(self) -> pygame.Rect:
        hw = structures.Vector2(self.distance_from_wall / 2, 0)
        hh = structures.Vector2(0, self.distance_from_wall / 2)

        return self.platform_collision_check(self.position - hw + hh) or \
               self.platform_collision_check(self.position + hw + hh) or \
               self.platform_collision_check(self.position + hw - hh) or \
               self.platform_collision_check(self.position - hw - hh)

    @staticmethod
    def platform_collision_check(point: object) -> object:
        try:
            tile, rect = Map.Map.instance.get_tile_global(*point)
            if tile != 0:
                return pygame.Rect(*rect)
            return None
        except IndexError:
            return None

    def set_moving_direction(self, x=None, y=None):
        if self.moving_direction:
            self.moving_direction = self.moving_direction.normalized()
        self.moving_direction += structures.Vector2(x or 0, y or 0)
        self.moving_direction = self.moving_direction.normalized()

    def setup_movement(self):
        self.up_down_left_right_movements()

    def up_down_left_right_movements(self):
        self.key_to_function[pygame.K_UP] = lambda: self.set_moving_direction(y=-1)
        self.key_to_function[pygame.K_DOWN] = lambda: self.set_moving_direction(y=1)
        self.key_to_function[pygame.K_LEFT] = lambda: self.set_moving_direction(x=-1)
        self.key_to_function[pygame.K_RIGHT] = lambda: self.set_moving_direction(x=1)
