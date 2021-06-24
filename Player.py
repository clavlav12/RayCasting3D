import structures
import pygame
import Map


class Player:
    def __init__(self, x=0, y=0):
        self.key_to_function = {}
        self.position = structures.Vector2.Cartesian(x, y)
        self.direction = structures.Vector2.Zero()
        self.setup_movement()

    def key_func(self, keys):
        self.direction.reset()
        for key, value in self.key_to_function.items():
            if keys[key]:
                value()

    def update(self, dt, keys):
        self.key_func(keys)
        self.move(dt)

    def move(self, dt):
        speed = 500
        shift = self.direction * speed * dt

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
            if tile != '0':
                return pygame.Rect(*rect)
            return None
        except IndexError:
            return None

    def set_direction(self, x=None, y=None):
        self.direction = self.direction.sign()
        self.direction.set_values(x, y)
        self.direction.normalize()

    def setup_movement(self):
        self.key_to_function[pygame.K_UP] = lambda: self.set_direction(y=-1)
        self.key_to_function[pygame.K_DOWN] = lambda: self.set_direction(y=1)
        self.key_to_function[pygame.K_LEFT] = lambda: self.set_direction(x=-1)
        self.key_to_function[pygame.K_RIGHT] = lambda: self.set_direction(x=1)

