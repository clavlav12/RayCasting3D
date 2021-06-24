import Map
import pygame
import structures
import pg_structures
import Player


class MapDrawer:
    def __init__(self, screen):
        self.screen = screen
        self.map = Map.Map.from_file('map2.txt')

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
                if not tile == '0':
                    pass
                    pygame.draw.rect(bg, pygame.Color('black'), rect)
                rect.x += self.map.tile_size
            rect.y += self.map.tile_size

        return bg

    def draw(self):
        pass


class PointPlayer(Player.Player):
    def draw_ray(self, map_, screen):
        fov = 45
        res = 360
        dir_ = (structures.Vector2.Point(pygame.mouse.get_pos()) - self.position).normalized().rotated(-fov / 2)
        matrix = structures.RotationMatrix(1 / res * fov)
        for i in range(res):
            length, intersection = map_.cast_ray(self.position, dir_)
            # pg_structures.draw_line_dashed(screen, (255, 255, 0), self.position.to_pos(),
            #                                (self.position + dir_ * length).to_pos(), 3, 5)
            pygame.draw.line(screen, (255, 255, 0), self.position.to_pos(),
                             (self.position + dir_ * (length)).to_pos(), 3)
            dir_ *= matrix
            dir_.rotate(1 / res * fov)
        # pygame.draw.circle(screen, pygame.Color('blue'), tuple(intersection), 5, 1)

    def draw(self, screen, map_):
        pos = self.position.to_pos()
        pygame.draw.circle(screen, pygame.Color('red'), pos, 5)

        self.draw_ray(map_, screen)


def main():
    pygame.init()
    screen = pg_structures.DisplayMods.Windowed((500, 500))
    clock = pygame.time.Clock()
    running = 1
    fps = 1000
    map_drawer = MapDrawer(screen)
    background = map_drawer.get_background()
    player = PointPlayer(100, 100)

    font = pygame.font.SysFont("Roboto", 20)
    color = pygame.Color('white')

    while running:
        screen.blit(background, (0, 0))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                clock.tick()
                continue
            elif event.type == pygame.QUIT:
                running = 0

        keys = pygame.key.get_pressed()

        elapsed = min(clock.tick(fps) / 1000.0, 1 / 30)

        map_drawer.draw()
        player.update(elapsed, keys)

        player.draw(screen, map_drawer.map)

        fps_sur = font.render(str(round(clock.get_fps())), False, color)
        screen.blit(fps_sur, (0, 0))
        pygame.display.flip()


if __name__ == '__main__':
    main()
