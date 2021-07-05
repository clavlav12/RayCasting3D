import structures
import pygame
import FasterMap as Map


class Player:
    def __init__(self, x=0, y=0):
        self.key_to_function = {}
        self.speed = 500
        self.position = structures.Vector2(x, y)
        self.moving_direction = structures.Vector2(0, 0)
        self.looking_direction = structures.Vector2(0, 0)
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

        platform = self.platform_collision_check()
        if platform is not None:
            platform: pygame.Rect
            if shift.x > 0:  # Moved right, move it back left
                self.position.x = platform.left - 1
            else:  # Moved left, move it back right
                self.position.x = 1 + platform.right

        self.position.y += shift.y

        platform = self.platform_collision_check()
        if platform is not None:
            platform: pygame.Rect
            if shift.y > 0:  # Moved down, move it back up
                self.position.y = platform.top - 1
            else:  # Moved up, move it back down
                self.position.y = 1 + platform.bottom

    def platform_collision_check(self):
        try:
            tile, rect = Map.Map.instance.get_tile_global(*self.position)
            if tile != 0:
                return pygame.Rect(*rect)
            return None
        except IndexError:
            return None

    def set_direction(self, x=None, y=None):
        self.moving_direction.set_values(x, y)
        self.moving_direction = self.moving_direction.normalized()

    def setup_movement(self):
        self.up_down_left_right_movements()

    def up_down_left_right_movements(self):
        self.key_to_function[pygame.K_UP] = lambda: self.set_direction(y=-1)
        self.key_to_function[pygame.K_DOWN] = lambda: self.set_direction(y=1)
        self.key_to_function[pygame.K_LEFT] = lambda: self.set_direction(x=-1)
        self.key_to_function[pygame.K_RIGHT] = lambda: self.set_direction(x=1)

