from Player import Player
import pygame
from FasterMap import Map, cast_screen
import structures
import pg_structures
from threading import Thread


class Player3D(Player):

    def __init__(self, x: int = 0, y: int = 0):
        self.regular_speed = 50
        self.crouching_speed = self.regular_speed / 2
        self.running_speed = self.regular_speed * 2
        super(Player3D, self).__init__(x, y, self.regular_speed)
        # physics
        self.ground_height = 1
        self.vertical_velocity = 0
        self.jump_velocity = 4
        self.jumping = True
        self.coming_up = False
        self.g = 20
        self.standing_acc = 30
        self.standing_vel = 15

        sensitivity = .5

        self.sensitivity_x = 0.01 * sensitivity
        self.sensitivity_y = 8 * sensitivity

        self._vertical_angle = self.ground_height
        self._height = 1

        self.max_height = 2
        self.min_height = 0.3
        self.max_view_angle = pg_structures.DisplayMods.current_height

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if value > self.max_height:
            self._height = self.max_height
            if self.vertical_velocity > 0:
                self.vertical_velocity = 0
        elif value < self.min_height:
            self._height = self.min_height
        else:
            self._height = value

    @property
    def vertical_angle(self):
        return self._vertical_angle

    @vertical_angle.setter
    def vertical_angle(self, value):
        self._vertical_angle = min(max(-self.max_view_angle, value), self.max_view_angle)

    def update(self, dt, keys):
        diffX = pygame.mouse.get_pos()[0] - pg_structures.DisplayMods.current_width / 2
        self.looking_direction = self.looking_direction * structures.RotationMatrix(diffX * self.sensitivity_x, True)

        diffY = pygame.mouse.get_pos()[1] - pg_structures.DisplayMods.current_height / 2
        # self.vertical_angle -= diffY * self.sensitivity_y
        pygame.mouse.set_pos(pg_structures.DisplayMods.current_width / 2, pg_structures.DisplayMods.current_height / 2)

        self.ground_height = 1
        if self.speed == self.running_speed:
            self.speed = self.regular_speed
        super(Player3D, self).update(dt, keys)

    def move(self, dt):
        if self.height > self.ground_height and not self.jumping:  # Falling
            self.jumping = self.ground_height  # Truthy value and saves the height on time of fall

        if self.height < self.ground_height and (not self.coming_up):  # coming up
            self.coming_up = self.ground_height
            self.vertical_velocity += self.standing_vel

        if self.jumping:
            self.vertical_velocity -= self.g * dt

        if self.coming_up:
            self.vertical_velocity -= self.standing_acc * dt

        self.height += self.vertical_velocity * dt

        if self.jumping and self.height <= self.ground_height:
            # finished falling but can be called when coming up
            self.jumping = False
            if not self.ground_height > self.jumping:
                # did NOT came up middle jumping (to allow animation to run smooth)
                self.height = self.ground_height
                self.vertical_velocity = 0
            else:
                if self.vertical_velocity < 0:  # Reset coming up
                    self.coming_up = False
                    self.vertical_velocity = 0

        if self.height >= self.ground_height and self.coming_up:
            # came up
            if self.speed == self.crouching_speed:
                self.speed = self.regular_speed
            self.height = self.ground_height
            self.coming_up = False
            self.vertical_velocity = 0

        if self.coming_up and (not self.jumping) and self.vertical_velocity < 0:  # low framerate bug
            print("lowfr")
            self.height = self.ground_height
            self.vertical_velocity += self.standing_vel
            self.coming_up = False

        super(Player3D, self).move(dt)

    def setup_movement(self):
        self.key_to_function[pygame.K_w] = \
            lambda: self.set_moving_direction(*self.looking_direction)
        self.key_to_function[pygame.K_d] = \
            lambda: self.set_moving_direction(*(self.looking_direction * structures.RotationMatrix.ROT90))
        self.key_to_function[pygame.K_s] = \
            lambda: self.set_moving_direction(*(self.looking_direction * structures.RotationMatrix.ROT180))
        self.key_to_function[pygame.K_a] = \
            lambda: self.set_moving_direction(*(self.looking_direction * structures.RotationMatrix.ROT270))
        self.key_to_function[pygame.K_LCTRL] = \
            lambda: self.crouch()
        self.key_to_function[pygame.K_SPACE] = \
            lambda: self.jump()
        self.key_to_function[pygame.K_LSHIFT] = \
            lambda: self.run()

    def crouch(self):
        self.ground_height = .3
        self.speed = self.crouching_speed

    def jump(self):
        if not self.jumping:
            self.vertical_velocity = self.jump_velocity

    def run(self):
        if self.speed == self.regular_speed:
            self.speed = self.running_speed


class Render3D:
    def __init__(self, player, map_, screen):
        self.W, self.H = screen.get_size()
        self.player: Player3D = player
        self.map: Map = map_
        self.fov = 66
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)
        self.resolution = 3
        self.screen = screen
        self.texture = pygame.image.load('wood_wall.png').convert()
        # self.texture = pygame.transform.smoothscale(self.texture, (self.texture.get_width(), self.texture.get_height()))

        background = pygame.Surface((screen.get_width(), screen.get_height() * 3))
        background.fill(pygame.Color('black'))

        floor_colour = (50, 50, 50)
        ceiling_colour = (135, 206, 235)
        # floor_colour = (16 * 3, 8 * 3, 0)
        # floor_colour = (122 / 4, 18 / 4, 11 / 4)

        pygame.draw.rect(background, ceiling_colour, (0, 0, self.W, self.H * 1.5))
        pygame.draw.rect(background, floor_colour, (0, self.H * 1.5, self.W, self.H * 1.5))

        self.background = background.convert()

        self.background = pygame.image.load('bgr edited.png').convert()
        ratio = screen.get_width() / (self.background.get_width() / 3)
        # ratio = 6
        # ratio *=
        self.background = pygame.transform.smoothscale(self.background,
                                                       (int(self.background.get_width() * ratio * 180 / 66),
                                                        int(self.background.get_height() * ratio)))
        pygame.draw.rect(self.background, floor_colour, (0, self.background.get_height() / 2, self.background.get_width(),
                                                         self.background.get_height() / 2))
        # print(self.background.get_size(), ratio)
        # self.background = background.convert()

    def render_rays(self):
        dir_ = self.player.looking_direction.normalized()
        camera_plane = dir_.tangent() * self.camera_plane_length

        t = Thread(target=self.cast_and_draw, args=(dir_, camera_plane))
        t.start()
        t.join()

    def cast_and_draw(self, dir_, camera_plane):
        pos = self.map.to_local(self.player.position)
        W, H = self.W, self.H
        resolution = self.resolution
        map_ = self.map
        screen = self.screen
        texture = self.texture
        texHeight = texture.get_height()
        texWidth = texture.get_width()

        dirX = dir_.x
        dirY = dir_.y
        posX = pos[0]
        posY = pos[1]
        cameraX = camera_plane.x
        cameraY = camera_plane.y
        for x, drawStart, lineHeight, color, texX in \
                cast_screen(W, resolution, map_.map(), posX, posY, dirX, cameraX, dirY, cameraY, H,
                            self.player.vertical_angle, self.player.height, texWidth):
            # pygame.draw.rect(screen, (color, color, color), (x, start, resolution, height))

            drawEnd = drawStart + lineHeight

            yStart = max(0, drawStart)
            yStop = min(H, drawEnd)
            pixelsPerTexel = lineHeight / texHeight
            colStart = int((yStart - drawStart) / pixelsPerTexel + .5)
            colHeight = int((yStop - yStart) / pixelsPerTexel + .5)

            yStart = int(colStart * pixelsPerTexel + drawStart + .5)
            yHeight = int(colHeight * pixelsPerTexel + .5)

            column = texture.subsurface((texX, colStart, 1, colHeight)).copy()
            column.fill((color, color, color), special_flags=pygame.BLEND_MULT)
            column = pygame.transform.scale(column, (resolution, yHeight))
            screen.blit(column, (x, yStart))

    def render_background(self):
        self.screen.blit(self.background, (0, 0),
                         ((self.player.looking_direction.angle()) / 360 * (self.background.get_width()
                                                                           * 2 / 3),
                          self.H - self.player.vertical_angle, self.W, self.H))
        # self.screen.blit(self.background, (0, 0),
        #                  (self.player.looking_direction.angle() / 360 * self.background.get_width(), 0, self.W, self.H))
        # print(self.player.looking_direction.angle())
        # self.screen.blit(self.background, (0, 0))


def main():
    pygame.init()
    # screen = pg_structures.DisplayMods.Windowed((800, 800))
    screen = pg_structures.DisplayMods.FullScreenAccelerated()
    screen.set_alpha(None)
    pygame.mouse.set_visible(False)

    W, H = screen.get_size()
    clock = pygame.time.Clock()
    running = 1
    fps = 1000

    font = pygame.font.SysFont("Roboto", 40)
    color = pygame.Color('white')

    player = Player3D(100, 100)
    map_ = Map.from_file('map2.txt')
    renderer = Render3D(player, map_, screen)
    fps = 0
    frames = 0

    FPS = 1000
    average_frame = 1000 / FPS
    pygame.mouse.set_pos(pg_structures.DisplayMods.current_width / 2, pg_structures.DisplayMods.current_height / 2)

    while running:
        renderer.render_background()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                clock.tick()
                continue
            elif event.type == pygame.QUIT:
                running = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    player.with_ = False
                elif event.button == 5:
                    player.with_ = True

        keys = pygame.key.get_pressed()

        elapsed_real = clock.tick(FPS)
        elapsed = min(elapsed_real / 1000.0, 1 / 30)

        renderer.render_rays()

        player.update(elapsed, keys)

        fps_now = clock.get_fps()
        fps += fps_now
        frames += 1

        average_frame *= 0.9
        average_frame += 0.1 * elapsed_real

        fps_sur = font.render(str(round(1000 / average_frame)), False, color)
        screen.blit(fps_sur, (0, 0))
        tilt_sur = font.render(str(renderer.player.speed), False, pygame.Color('white'))
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
