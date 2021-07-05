from Player import Player
import pygame
from FasterMap import Map, cast_screen
import structures
import pg_structures
from threading import Thread


class Player3D(Player):
    def render_rays(self, map_, screen, screen_size):
        self.fov = 66
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)

        W, H = screen_size

        dir_ = (structures.Vector2(*(pygame.mouse.get_pos()) - self.position)).normalized()
        resolution = 3
        camera_plane = dir_.tangent() * self.camera_plane_length

        t = Thread(target=self.cast_and_draw, args=(W, resolution, dir_, camera_plane, map_, screen, H))
        t.start()
        t.join()

    def cast_and_draw(self, W, resolution, dir_, camera_plane, map_: Map, screen, H):
        pos = map_.to_local(self.position)

        dirX = dir_.x
        dirY = dir_.y
        posX = pos[0]
        posY = pos[1]
        cameraX = camera_plane.x
        cameraY = camera_plane.y
        for x in range(0, W, resolution):
            pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
            length, side = map_.cast_ray(posX, posY, dirX + cameraX * pixel_camera_pos,
                                         dirY + cameraY * pixel_camera_pos)
            self.draw_ray(screen, x, length, H, side, resolution)

    @staticmethod
    def draw_ray(screen, x, ray_length, height, side, resolution):
        line_height = height / ray_length if ray_length != 0 \
            else height  # Multiply by a greater than one value to make walls higher

        half_height = height / 2
        half_line = line_height / 2

        draw_start = max(-half_line + half_height, 0) + tilt
        draw_end = min(half_line + half_height, height) + tilt

        # print(side, ray_length)
        c = min(int(max(1, (255.0 - ray_length * 27.2) * (1 - side * .25))), 255)
        try:
            if resolution == 1:
                pygame.draw.line(screen, (0, 0, c), (x, draw_start), (x, draw_end))
            else:
                pygame.draw.rect(screen, (0, 0, c), (x, draw_start, resolution, draw_end - draw_start))
        except Exception as e:
            print((0, 0, c), ray_length)
            raise e


class Render3D:
    def __init__(self, player, map_):
        self.player: Player3D = player
        self.map: Map = map_
        self.fov = 90
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)

    def draw_screen(self, W, H):
        for x in range(W):
            camera_plane = self.player.moving_direction.tangent() * self.camera_plane_length
            pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
            ray_direction = self.player.moving_direction + camera_plane * pixel_camera_pos
            distance = self.map.cast_ray(self.player.position, ray_direction)


tilt = 10


def main():
    global tilt
    pygame.init()
    # screen = pg_structures.DisplayMods.Windowed((500, 500))
    screen = pg_structures.DisplayMods.FullScreenAccelerated()
    screen.set_alpha(None)
    W, H = screen.get_size()
    clock = pygame.time.Clock()
    running = 1
    fps = 1000
    player = Player3D(100, 100)

    font = pygame.font.SysFont("Roboto", 20)
    color = pygame.Color('white')
    background = pygame.Surface(screen.get_size())
    background.fill(pygame.Color('black'))

    floor_colour = (50, 50, 50)
    ceiling_colour = (135, 206, 235)

    map_ = Map.from_file('map2.txt')
    t = None

    fps = 0
    frames = 0

    FPS = 1000
    average_frame = 1000 / FPS

    while running:
        new_bg = background.copy()
        pygame.draw.rect(new_bg, ceiling_colour, (0, 0, W, H // 2 + tilt))
        pygame.draw.rect(new_bg, floor_colour, (0, 0, W, H // 2 + tilt))

        screen.blit(new_bg, (0, 0))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                clock.tick()
                continue
            elif event.type == pygame.QUIT:
                running = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    tilt += 10
                elif event.button == 5:
                    tilt -= 10

        keys = pygame.key.get_pressed()

        elapsed_real = clock.tick(FPS)
        elapsed = min(elapsed_real / 1000.0, 1 / 30)

        if tilt > 0:
            player.render_rays(map_, screen, screen.get_size())
        else:
            player.render_rays2(map_, screen, screen.get_size())

        player.update(elapsed, keys)

        fps_now = clock.get_fps()
        fps += fps_now
        frames += 1

        average_frame *= 0.9
        average_frame += 0.1 * elapsed_real

        fps_sur = font.render(str(round(1000 / average_frame)), False, color)
        screen.blit(fps_sur, (30, 0))
        tilt_sur = font.render(str(tilt), False, pygame.Color('white'))
        screen.blit(tilt_sur, (0, 0))

        if t is not None:
            t.join()
        pygame.display.flip()
    print(fps / frames)


if __name__ == '__main__':
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()
    main()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename='profiling.prof')
