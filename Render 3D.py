from Player import Player, Weapon
import pygame
import FasterMap
import structures
import pg_structures
import numpy as np
from threading import Thread
from Sprites3D import BillboardSprite

class Player3D(Player):

    def __init__(self, x: int = 0, y: int = 0):
        self.fov = 90
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

        self.sensitivity_x = .02 * sensitivity
        self.sensitivity_y = 8 * sensitivity

        self._vertical_angle = 0
        self._height = 1

        self.max_height = 2
        self.min_height = 0.3
        self.max_view_angle = pg_structures.DisplayMods.current_height

        self.with_ = False

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
        self.looking_direction = self.looking_direction * structures.RotationMatrix(diffX / self.fov * 30, False)
        # self.looking_direction = self.looking_direction * structures.RotationMatrix(90 * dt * self.sensitivity_x, True)
        diffY = pygame.mouse.get_pos()[1] - pg_structures.DisplayMods.current_height / 2
        self.vertical_angle -= diffY * self.sensitivity_y
        pygame.mouse.set_pos(pg_structures.DisplayMods.current_width / 2, pg_structures.DisplayMods.current_height / 2)

        self.ground_height = 1
        if self.speed == self.running_speed:
            self.speed = self.regular_speed

    def update_kinematics(self, dt):
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

        super(Player3D, self).update_kinematics(dt)

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


class Background:
    ceiling = None
    floor = None
    W = -1
    H = -1

    @classmethod
    def set_background(cls, ceiling_type, floor_type, ceiling_arg, floor_arg, W, H):
        """
        :param ceiling_type: Type of ceiling (structures.BackgroundType)
        :param floor_type:  Type of floor (structures.BackgroundType)
        :param ceiling_arg: Argument that is used to make ceiling (color for solid, panoramic image filename for
            panoramic, texture filename for textured and surface for image)
        :param floor_arg: Same as ceiling_arg for floor
        :param W: Width of screen
        :param H: Height of screen
        """
        cls.W = W
        cls.H = H
        cls.ceiling = cls(ceiling_type, ceiling_arg, False)
        cls.floor = cls(floor_type, floor_arg, True)

    def __init__(self, type_, arg, is_floor):
        self.type = type_
        self.arg = arg
        self.is_floor = is_floor

        self.background = pygame.Surface((self.W * 3, self.H * 1.5)).convert()

        {
            structures.BackgroundType.solid: self.solid_init,
            structures.BackgroundType.panoramic: self.panoramic_init,
            structures.BackgroundType.textured: self.textured_init,
            structures.BackgroundType.image: self.imaged_init
        }[self.type]()

    def solid_init(self):
        pygame.draw.rect(self.background, self.arg, (0, 0, self.W, self.H * 1.5))

    def panoramic_init(self):
        if isinstance(self.arg, str):
            self.panoramic_image = pygame.image.load('Assets/Images/Background/' + self.arg).convert()
            assert self.panoramic_image.get_size() == (self.W * 3, self.H * 1.5), 'Deal with it later'
        elif isinstance(self.arg, pygame.Surface):
            self.panoramic_image = self.arg

    def textured_init(self):
        self.arg = pg_structures.Textures(None, self.arg, to_index=True)

    def imaged_init(self):
        image = pygame.image.load('Assets/Images/Background/' + self.arg)
        assert image.get_height() < self.H * 1.5, 'Deal with it later'
        self.background.blit(image, (0, 0))

    @staticmethod
    def image_rect(image, vertical_angle):
        return 0, 0, image.get_width(), image.get_height() + vertical_angle

    def draw(self, screen, fov, looking_direction, vertical_angle, map_, camera_plane_length, position, height):
        start = 0
        sign = -1 if self.is_floor else 1

        if self.floor is self:
            start = self.H // 2
        if self.type in (structures.BackgroundType.image, structures.BackgroundType.solid):
            rect = screen.blit(self.background, (0, start + vertical_angle * self.is_floor), (0, 0, self.W, self.H // 2 + sign * vertical_angle))
            # pygame.draw.rect(screen, (255, 0, 0), rect, 1)
        elif self.type == structures.BackgroundType.panoramic:

            rect = pygame.Rect(
                (
                    (180 / fov) * (looking_direction.angle()) / 360 * (self.background.get_width()
                                                                       * 2 / 3) % (self.background.get_width() * 2 / 3),
                    self.H - vertical_angle, self.W, self.H // 2 + vertical_angle)
            )
            if not self.is_floor:
                rect.bottom = self.panoramic_image.get_height()
            screen.blit(self.panoramic_image, (0, start + vertical_angle * self.is_floor),
                        rect)

        elif self.type == structures.BackgroundType.textured:
            other = self.floor if self is not self.floor else self.ceiling
            if other.type == structures.BackgroundType.textured and height == 1 and vertical_angle == 0 and self.arg is other.arg:
                if self.is_floor:
                    return  # if both are textured only one casting is required
                else:  # cast both
                    background = self.get_floor_ceiling(map_, position, looking_direction, camera_plane_length, screen,
                                                        other.arg.array, self.arg.array, other.arg.palette, height, vertical_angle)
                    screen.blit(background, (0, 0))
            else:  # only cast self
                background = self.get_floor_ceiling(map_, position, looking_direction, camera_plane_length, screen,
                                                    self.arg.array if self.is_floor else None,
                                                    self.arg.array if not self.is_floor else None,
                                                    self.arg.palette,
                                                    height,
                                                    vertical_angle
                                                    )
                screen.blit(background, (0, start + vertical_angle * self.is_floor))

    @staticmethod
    def get_floor_ceiling(map_, position, looking_direction, camera_plane_length, screen, floor_texture,
                          ceiling_texture, palette, height, vertical_angle):

        dir_ = looking_direction.normalized()
        camera_plane = dir_.tangent() * camera_plane_length
        pos = map_.to_local(position)

        buffer = FasterMap.cast_floor_ceiling(*dir_, *camera_plane, screen.get_width(), screen.get_height(), *pos,
                                    floor_texture if floor_texture is not None else np.zeros((0, 0), np.int64),
                                    ceiling_texture if ceiling_texture is not None else np.zeros((0, 0), np.int64),
                                    floor_texture is not None,
                                    ceiling_texture is not None,
                                    height,
                                    int(vertical_angle),
                                    )

        screen = pygame.surfarray.make_surface(buffer)
        screen.set_palette(palette)

        return screen

    @classmethod
    def draw_background(cls, screen, fov, looking_direction, vertical_angle, map_, camera_plane_length, position, height, threaded=None):
        if threaded is None:  # automatically decide
            threaded = cls.floor.type == cls.ceiling.type == structures.BackgroundType.textured
        args = (screen, fov, looking_direction, vertical_angle, map_, camera_plane_length, position, height)
        if threaded:
            t1 = Thread(target=cls.floor.draw, args=args)
            t1.start()
            t2 = Thread(target=cls.ceiling.draw, args=args)
            t2.start()
            t1.join()
            t2.join()
        else:
            cls.floor.draw(*args)
            cls.ceiling.draw(*args)


class Render3D:
    instance = None

    def __init__(self, player, map_, screen):
        self.z_buffer = None

        self.W, self.H = screen.get_size()
        self.player: Player3D = player
        self.map: FasterMap.Map = map_
        self.fov = 66
        self.fov = 60
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)
        self.resolution = 3
        self.screen = screen

        ceiling_colour = (50, 50, 50)
        floor_colour = (80, 80, 80)

        self.texture = pygame.image.load('Assets/Images/Textures/wood_wall.png').convert()

        bg = pygame.image.load('Assets/Images/Background/bgr edited.png').convert()
        ratio = screen.get_width() / (bg.get_width() / 3)

        bg = pygame.transform.smoothscale(bg,
                                          (int(bg.get_width() * ratio),
                                           int(bg.get_height() * ratio)))

        bg = bg.subsurface((0, 0, bg.get_width(), bg.get_height() // 2)).convert()
        Background.set_background(
            structures.BackgroundType.panoramic,
            structures.BackgroundType.textured,
            bg,
            'wood2.png',
            *self.screen.get_size()
        )
        # Background.set_background(
        #     structures.BackgroundType.panoramic,
        #     structures.BackgroundType.textured,
        #     'background.png',
        #     'blood wall dark.png',
        #     *self.screen.get_size()
        # )
        Render3D.instance = self

        texture = pygame.image.load(r'Assets\Images\Sprites\barrel.png  ').convert()
        texture.set_colorkey(pygame.Color('black'))
        print(self.player.position)
        pillar = pygame.image.load(r'Assets\Images\Sprites\pillar.png').convert()
        pillar.set_colorkey(pygame.Color('black'))

        self.bill = BillboardSprite.BillboardSprite(texture, (250, 250))
        self.bill = BillboardSprite.BillboardSprite(texture, (250 + 50 * 3, 250 + 50 * 1))
        self.bill = BillboardSprite.BillboardSprite(texture, (250 + 50 * 4, 250 + 50 * 1))

    def render_rays(self):
        dir_ = self.player.looking_direction.normalized()
        camera_plane = dir_.tangent() * self.camera_plane_length
        self.cast_and_draw(dir_, camera_plane)

    def draw_floor(self, dir_, camera_plane):
        pos = self.map.to_local(self.player.position)
        buffer = FasterMap.cast_floor_ceiling(*dir_, *camera_plane, *self.screen.get_size(), *pos, self.floor_texture, self.ceiling_texture)
        screen = pygame.surfarray.make_surface(buffer)
    # screen = pygame.transform.scale(screen, seAlf.screen.get_size())
        screen.set_palette(self.floor_image.get_palette())
        screen.blit(self.shadow_mask, (0, 0), pygame.BLEND_MULT)
        # screen.set_alpha(None)
        self.screen.blit(screen, (0, self.screen.get_height() // 2), (0, self.screen.get_height() // 2, self.screen.get_width(), self.screen.get_height()))

    def cast_and_draw(self, dir_, camera_plane):
        pos = self.map.to_local(self.player.position)
        resolution = self.resolution
        # screen = pygame.Surface(self.screen.get_size())
        screen = self.screen
        screen.set_colorkey(pygame.Color('black'))

        texture = self.texture
        tex_height = self.texture.get_height()
        tex_width = self.texture.get_width()
        for x, colStart, colHeight, yStart, yHeight, color, texX, buffer in \
                FasterMap.cast_screen(self.W, resolution, self.map.map(), pos[0], pos[1], dir_.x, camera_plane.x, dir_.y,
                            camera_plane.y, self.H, self.player.vertical_angle, self.player.height,
                            self.texture.get_width(), tex_height):
            if x < 0:
                break
            # if 3:
            # pygame.draw.rect(screen, (color, color, color), (x, yStart, resolution, yHeight))
            if colHeight > 0 and colStart < tex_height:
                column = texture.subsurface((texX, colStart, 1, colHeight)).copy()
                column.fill((color, color, color), special_flags=pygame.BLEND_MULT)
                column = pygame.transform.scale(column, (resolution, yHeight))
                screen.blit(column, (x, yStart))
        self.z_buffer = buffer

        BillboardSprite.BillboardSprite.draw_all(pos, camera_plane, dir_, self.W, self.H, self.z_buffer,
                                                 self.resolution, screen, self.player.height, self.player.vertical_angle)

        return screen


    def render_background(self):
        Background.draw_background(self.screen, self.fov, self.player.looking_direction, self.player.vertical_angle,
                                   self.map, self.camera_plane_length, self.player.position, self.player.height)

global_val = False

def main():
    global global_val
    pygame.init()
    # screen = pg_structures.DisplayMods.Windowed((800, 800))
    screen = pg_structures.DisplayMods.FullScreenAccelerated()
    # resolution = 1
    # screen = pygame.Surface((real_screen.get_width() // resolution, real_screen.get_height() // resolution)).convert()
    # screen.set_alpha(None)
    pygame.mouse.set_visible(False)

    W, H = screen.get_size()
    clock = pygame.time.Clock()
    running = 1
    fps = 1000

    font = pygame.font.SysFont("Roboto", 40)
    color = pygame.Color('white')

    player = Player3D(100, 100)
    map_ = FasterMap.Map.from_file('Assets/Maps/map3.txt')
    renderer = Render3D(player, map_, screen)
    fps = 0
    frames = 0

    FPS = 1000
    elapsed = elapsed_real = 1 / FPS

    average_frame = 1000 / FPS
    pygame.mouse.set_pos(pg_structures.DisplayMods.current_width / 2, pg_structures.DisplayMods.current_height / 2)

    elaspeds = []

    pistol = Weapon('Assets/Weapons/Pistol', 8, -1, screen)

    while running:
        renderer.render_background()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    player.with_ = False
                    global_val += 1
                elif event.button == 5:
                    player.with_ = True
                    global_val -= 1
                elif event.button == 1:
                    pistol.shoot()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    global_val = True
                elif event.key == pygame.K_j:
                    global_val = False
        keys = pygame.key.get_pressed()

        renderer.render_rays()

        player._update(elapsed, keys)

        fps_now = clock.get_fps()
        fps += fps_now
        frames += 1

        elaspeds.append(elapsed)

        average_frame *= 0.9
        average_frame += 0.1 * elapsed_real

        fps_sur = font.render(str(round(1000 / average_frame)), False, color)
        screen.blit(fps_sur, (0, 0))
        tilt_sur = font.render("{}".format(global_val), False, pygame.Color('white'))
        screen.blit(tilt_sur, (0, 40))

        pistol.draw()

        elapsed_real = clock.tick(FPS)
        elapsed = elapsed_real / 1000 # min(elapsed_real / 1000.0, 1 / 30)

        # new = screen
        # new = pygame.transform.scale(screen, real_screen.get_size(), real_screen)
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
