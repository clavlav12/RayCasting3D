from Player import Player
import pygame
from FasterMap import Map, cast_screen
import structures
import pg_structures
from threading import Thread


class Player3D(Player):

    def __init__(self, x: int = 0, y: int = 0):
        super(Player3D, self).__init__(x, y, 50)

    def update(self, dt, keys):
        global tilt
        # diff = (structures.Vector2(*(pygame.mouse.get_pos())) -
        #                             structures.Vector2(*pg_structures.DisplayMods.current_resolution)/2).normalized()
        diffX = pygame.mouse.get_pos()[0] - pg_structures.DisplayMods.current_width / 2
        self.looking_direction = self.looking_direction * structures.RotationMatrix(diffX * 0.01, True)

        diffY = pygame.mouse.get_pos()[1] - pg_structures.DisplayMods.current_height / 2
        tilt -= diffY * 3
        head_move = 1080
        tilt = max(-head_move, min(head_move, tilt))

        pygame.mouse.set_pos(pg_structures.DisplayMods.current_width / 2, pg_structures.DisplayMods.current_height / 2)

        super(Player3D, self).update(dt, keys)

    def render_rays(self, map_, screen, screen_size):
        self.fov = 66
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)

        W, H = screen_size

        dir_ = self.looking_direction.normalized()
        resolution = 1
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
        for x, start, height, color in \
                cast_screen(W, resolution, map_.map(), posX, posY, dirX, cameraX, dirY, cameraY, H, tilt, h_):
            pygame.draw.rect(screen, (color, color, color), (x, start, resolution, height))

    def setup_movement(self):
        self.key_to_function[pygame.K_w] = \
            lambda: self.set_moving_direction(*self.looking_direction)
        self.key_to_function[pygame.K_d] = \
            lambda: self.set_moving_direction(*(self.looking_direction * structures.RotationMatrix.ROT90))
        self.key_to_function[pygame.K_s] = \
            lambda: self.set_moving_direction(*(self.looking_direction * structures.RotationMatrix.ROT180))
        self.key_to_function[pygame.K_a] = \
            lambda: self.set_moving_direction(*(self.looking_direction * structures.RotationMatrix.ROT270))


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
h_ = 1


def main():
    global tilt, h_
    pygame.init()
    # screen = pg_structures.DisplayMods.Windowed((500, 500))
    screen = pg_structures.DisplayMods.FullScreenAccelerated()
    screen.set_alpha(None)
    pygame.mouse.set_visible(False)

    W, H = screen.get_size()
    clock = pygame.time.Clock()
    running = 1
    fps = 1000
    player = Player3D(100, 100)

    font = pygame.font.SysFont("Roboto", 40)
    color = pygame.Color('white')

    background = pygame.Surface((screen.get_width(), screen.get_height() * 3))
    background.fill(pygame.Color('black'))
    background = background.convert()

    floor_colour = (50, 50, 50)
    ceiling_colour = (135, 206, 235)
    # ceiling_colour = (50, 50, 50)
    pygame.draw.rect(background, ceiling_colour, (0, 0, W, H * 1.5))
    pygame.draw.rect(background, floor_colour, (0, H * 1.5, W, H * 1.5))

    map_ = Map.from_file('map2.txt')

    fps = 0
    frames = 0

    FPS = 1000
    average_frame = 1000 / FPS
    pygame.mouse.set_pos(pg_structures.DisplayMods.current_width / 2, pg_structures.DisplayMods.current_height / 2)

    while running:
        h_ = min(2 - .3, max(h_, 0 + .3))
        screen.blit(background, (0, 0), (0, H - tilt, W, H))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                clock.tick()
                continue
            elif event.type == pygame.QUIT:
                running = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    h_ += .1
                elif event.button == 5:
                    h_ -= .1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL:
                    h_ += .7
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LCTRL:
                    h_ -= .7

        keys = pygame.key.get_pressed()

        elapsed_real = clock.tick(FPS)
        elapsed = min(elapsed_real / 1000.0, 1 / 30)

        player.render_rays(map_, screen, screen.get_size())

        player.update(elapsed, keys)

        fps_now = clock.get_fps()
        fps += fps_now
        frames += 1

        average_frame *= 0.9
        average_frame += 0.1 * elapsed_real

        fps_sur = font.render(str(round(1000 / average_frame)), False, color)
        screen.blit(fps_sur, (0, 0))
        tilt_sur = font.render(str(h_), False, pygame.Color('white'))
        screen.blit(tilt_sur, (0, 40))

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
