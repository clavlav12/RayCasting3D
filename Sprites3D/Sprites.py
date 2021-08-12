import pygame
from structures import Vector2
import typing
import FasterMap as Map

dx = 0.000001


class BaseSprite(pygame.sprite.Sprite):

    def __init__(self, position, velocity, rect_width, rect_height):
        super(BaseSprite, self).__init__()
        self.wall_collision = True
        self.position = Vector2(*position)
        self.velocity = Vector2(*velocity)

        self.rw = rect_width
        self.rh = rect_height

    def _update(self, dt, keys):
        self.update()
        self.move(keys)
        self.update_kinematics(dt)
        self.draw()

    def move(self, keys):
        pass

    def update_kinematics(self, dt):
        displacement = self.velocity * dt
        self.position.x += displacement.x
        self.x_collision(displacement)

        self.position.y += displacement.y
        self.y_collision(displacement)

    def draw(self):
        pass

    def x_collision(self, displacement):
        platform = self.platform_rect_check()
        if platform is not None:
            platform: pygame.Rect
            if displacement.x > 0:  # Moved right, move it back left
                self.position.x = platform.left - self.rw / 2 - dx
            else:  # Moved left, move it back right
                self.position.x = self.rw / 2 + platform.right + dx
        return platform

    def y_collision(self, displacement):
        platform = self.platform_rect_check()
        if platform is not None:
            platform: pygame.Rect
            if displacement.y > 0:  # Moved down, move it back up
                self.position.y = platform.top - self.rh / 2 - dx
            else:  # Moved up, move it back down
                self.position.y = self.rh / 2 + platform.bottom + dx
        return platform

    def platform_rect_check(self) -> pygame.Rect:
        hw = Vector2(self.rw / 2, 0)
        hh = Vector2(0, self.rh / 2)

        return self.platform_collision_check(self.position - hw + hh) or \
               self.platform_collision_check(self.position + hw + hh) or \
               self.platform_collision_check(self.position + hw - hh) or \
               self.platform_collision_check(self.position - hw - hh)

    @staticmethod
    def platform_collision_check(point: Vector2) -> typing.Optional[pygame.Rect]:
        try:
            tile, rect = Map.Map.instance.get_tile_global(*point)
            if tile != 0:
                return pygame.Rect(*rect)
            return None
        except IndexError:
            return None
