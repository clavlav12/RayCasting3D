import pygame

import FasterMap as Map
import Player
import pg_structures
import structures


class MapDrawer:
    def __init__(self, screen):
        self.screen = screen
        self.map = Map.Map.from_file('../Assets/Maps/map2.txt')

    def get_background(self):
        bg = pygame.Surface(self.map.to_global(self.map.get_size())).convert()
        bg.fill(pygame.Color('grey'))
        y = 0

        for row in self.map.rows():
            pygame.draw.line(bg, pygame.Color('black'),
                             self.map.to_global((0, y)), self.map.to_global((len(row), y)))
            y += 1

        x = 0
        for column in self.map.columns():
            pygame.draw.line(bg, pygame.Color('black'),
                             self.map.to_global((x, 0)), self.map.to_global((x, len(column))))
            x += 1

        rect = pygame.Rect(0, 0, self.map.tile_size, self.map.tile_size)
        for row in self.map.rows():
            rect.x = 0
            for tile in row:
                if not tile == 0:
                    pass
                    pygame.draw.rect(bg, pygame.Color('black'), rect)
                rect.x += self.map.tile_size
            rect.y += self.map.tile_size

        return bg

    def draw(self):
        pass


def cast_sprite(world_sprite_x, world_sprite_y, pos_x, pos_y, plane_x, plane_y, dir_x, dir_y):
    # print(z_buffer)

    sprite_x = world_sprite_x - pos_x
    sprite_y = world_sprite_y - pos_y

    inv_det = 1 / (plane_x * dir_y - dir_x * plane_y)
    transform_x = inv_det * (dir_y * sprite_x - dir_x * sprite_y)
    transform_y = inv_det * (- plane_y * sprite_x + plane_x * sprite_y)

    return transform_x, transform_y


class PointPlayer(Player.Player):
    def __init__(self, *args, **kwargs):
        super(PointPlayer, self).__init__(*args, **kwargs)
        self.sprite = Sprite((150, 150))

        self.fov = 60
        self.cpl = structures.DegTrigo.tan(self.fov / 2)

    def draw_ray_shadow(self, map_, screen):
        map_: Map.Map
        res = 180
        fov = self.fov

        dir_ = (structures.Vector2(*pygame.mouse.get_pos()) - self.position)# * structures.RotationMatrix(-fov / 2)
        dir_ = dir_.normalized()

        #actual_dir = structures.Vector2(*pygame.mouse.get_pos()) - self.position
        plane = dir_.tangent() * self.cpl

        sprite_pos = map_.to_local(self.sprite.position)
        transform = cast_sprite(*sprite_pos, *map_.to_local(self.position), *plane, *dir_)

        transform = map_.to_global(transform)

        # matrix = structures.RotationMatrix(1 / res * fov)
        # for i in range(res):
        #     length, *_ = map_.cast_ray(*map_.to_local(self.position), *dir_)
        #     length = map_.to_global(length)
        #     pygame.draw.line(screen, (255, 255, 0), self.position.to_pos(),
        #                      (self.position + dir_ * (length)).to_pos(), 3)
        #     dir_ *= matrix

        pygame.draw.line(screen, pygame.Color('green'), self.position.to_pos(), (self.position + structures.Vector2(*transform) * structures.RotationMatrix(-dir_.angle())).to_pos(), 4)
        pygame.draw.line(screen, pygame.Color('blue'), self.position.to_pos(), (self.position + dir_*50).to_pos(), 4)
        pygame.draw.line(screen, pygame.Color('black'), self.position.to_pos(), (self.position + plane*50).to_pos(), 4)


        self.sprite.draw(screen)

    def draw(self, screen, map_):
        pos = self.position.to_pos()
        pygame.draw.circle(screen, pygame.Color('red'), pos, 5)

        self.draw_ray_shadow(map_, screen)

    def set_moving_direction(self, x=None, y=None):
        self.moving_direction = self.moving_direction.sign()
        super(PointPlayer, self).set_moving_direction(x, y)


class Sprite:
    def __init__(self, position):
        self.position = position

    def draw(self, screen):
        pygame.draw.circle(screen, pygame.Color('red'), self.position, 5)


def main():
    pygame.init()
    screen = pg_structures.DisplayMods.Windowed((500, 500))
    clock = pygame.time.Clock()
    running = 1
    fps = 1000
    map_drawer = MapDrawer(screen)
    background = map_drawer.get_background()
    player = PointPlayer(175, 175)

    font = pygame.font.SysFont("Roboto", 20)
    color = pygame.Color('white')

    while running:
        screen.blit(background, (0, 0))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = 0

        keys = pygame.key.get_pressed()

        elapsed = min(clock.tick(fps) / 1000.0, 1 / 30)

        map_drawer.draw()

        player._update(elapsed, keys, screen, map_drawer.map)

        fps_sur = font.render(str(round(clock.get_fps())), False, color)
        screen.blit(fps_sur, (0, 0))
        pygame.display.flip()

if __name__ == '__main__':
    main()
