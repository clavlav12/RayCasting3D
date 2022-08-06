import collections
import json

from Player import Player, Weapon
import pygame
import FasterMap
import structures
import pg_structures
import numpy as np
from threading import Thread
from Sprites3D import BillboardSprite, Sprites, PanoramicSprites
from numba.typed import Dict
from numba import types


class RenderSettings:
    Fov = 90
    Resolution = 3

    @classmethod
    def fov(cls):
        return cls.Fov

    @classmethod
    def resolution(cls):
        return cls.Resolution


class Player3D(Player):

    def __init__(self, x: int = 0, y: int = 0):
        self.regular_speed = 50
        self.crouching_speed = self.regular_speed / 2
        self.running_speed = self.regular_speed * 2
        super(Player3D, self).__init__(x, y, self.regular_speed)
        # physics
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

        self.vertical_position = 1

        self.max_height = 2
        self.min_height = 0.3
        self.with_ = False

    @property
    def height(self):
        return self.vertical_position

    @height.setter
    def height(self, value):
        if value > self.max_height:
            self.vertical_position = self.max_height
            if self.vertical_velocity > 0:
                self.vertical_velocity = 0
        elif value < self.min_height:
            self.vertical_position = self.min_height
        else:
            self.vertical_position = value

    def update_bef(self, dt, keys):
        diffX = pygame.mouse.get_pos()[0] - pg_structures.DisplayMods.current_width / 2
        self.looking_direction = self.looking_direction * structures.RotationMatrix(diffX / RenderSettings.fov() * 30,
                                                                                    False)
        # self.looking_direction = self.looking_direction * structures.RotationMatrix(90 * dt * self.sensitivity_x, True)
        diffY = pygame.mouse.get_pos()[1] - pg_structures.DisplayMods.current_height / 2
        self.tilt -= diffY * self.sensitivity_y

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
    BIG_TEXTURE = collections.namedtuple('BIG_TEXTURE', ('default', 'big_texture'))
    ceiling = None
    floor = None
    W = -1
    H = -1

    @classmethod
    def set_background(cls, ceiling_type, floor_type, ceiling_arg, floor_arg, W, H, ):
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
        if self.arg is not None:
            if isinstance(self.arg, tuple):  # big texture
                self.arg = self.BIG_TEXTURE(*self.arg)
            if isinstance(self.arg, self.BIG_TEXTURE):  # big texture
                self.arg = self.BIG_TEXTURE(*(pg_structures.Texture[texture] for texture in self.arg))
                self.arg = self.BIG_TEXTURE(*(pg_structures.IndexedTexture(texture, False) for texture in self.arg))

                srf = pygame.surfarray.make_surface(self.arg.big_texture.array)
                srf.set_palette(self.arg.big_texture.palette)
                pygame.image.save(srf, 'cityindexed.png')
            else:
                self.arg = pg_structures.Texture[r'Textures/Named/' + self.arg]
                self.arg = pg_structures.IndexedTexture(self.arg, False)
        else:  # otherwise create a list
            folder = pg_structures.Texture.textures_list()
            for file in folder:
                pg_structures.IndexedTexture(file, True)
            folder = pg_structures.Texture.textures_list()

            self.arg = np.asarray([texture.array for texture in folder])

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
            rect = screen.blit(self.background, (0, start + vertical_angle * self.is_floor),
                               (0, 0, self.W, self.H // 2 + sign * vertical_angle))
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
            if isinstance(self.arg, pg_structures.IndexedTexture):
                textures_map = np.ndarray(FasterMap.Map.instance.shape, np.int64)
                textures_map.fill(0)

                textures_array = np.asarray([self.arg.array])
            elif isinstance(self.arg, np.ndarray):
                if self.is_floor:
                    textures_map = FasterMap.Map.instance.floor_array
                else:
                    textures_map = FasterMap.Map.instance.ceiling_array
                textures_array = self.arg

            try:
                if isinstance(self.arg, (np.ndarray, pg_structures.IndexedTexture)):
                    background = self.get_floor_ceiling(map_, position, looking_direction, camera_plane_length, screen,
                                                        textures_map,
                                                        textures_array,
                                                        pg_structures.IndexedTexture.palette,
                                                        height,
                                                        vertical_angle,
                                                        self.is_floor
                                                        )
                elif isinstance(self.arg, self.BIG_TEXTURE):
                    background = self.get_floor_ceiling_big_texture(map_, position, looking_direction,
                                                                    camera_plane_length, screen,
                                                                    self.arg.big_texture.array,
                                                                    8,
                                                                    self.arg.default.array,
                                                                    pg_structures.IndexedTexture.palette,
                                                                    height,
                                                                    vertical_angle,
                                                                    self.is_floor
                                                                    )

            except Exception as e:
                raise e
            screen.blit(background, (0, start + vertical_angle * self.is_floor))

    @staticmethod
    def get_floor_ceiling(map_, position, looking_direction, camera_plane_length, screen, textures_map, textures_list,
                          palette, height, vertical_angle, is_floor):

        s = screen
        dir_ = looking_direction.normalized()
        camera_plane = dir_.tangent() * camera_plane_length
        pos = map_.to_local(position)

        buffer = FasterMap.cast_floor_ceiling(*dir_, *camera_plane, screen.get_width(), screen.get_height(), *pos,
                                              textures_list, textures_map,
                                              height,
                                              int(vertical_angle),
                                              is_floor
                                              )

        screen = pygame.surfarray.make_surface(buffer)
        screen.set_palette(palette)

        return screen

    @staticmethod
    def get_floor_ceiling_big_texture(map_, position, looking_direction, camera_plane_length, screen, big_texture,
                                      tile_size, default_texture, palette, height, vertical_angle, is_floor):

        dir_ = looking_direction.normalized()
        camera_plane = dir_.tangent() * camera_plane_length
        pos = map_.to_local(position)
        s = screen

        buffer = FasterMap.cast_floor_ceiling_big_texture(*dir_, *camera_plane, screen.get_width(), screen.get_height(),
                                                          *pos,
                                                          big_texture, tile_size, default_texture,
                                                          height,
                                                          int(vertical_angle),
                                                          is_floor
                                                          )

        screen = pygame.surfarray.make_surface(buffer)
        screen.set_palette(palette)
        # screen = pygame.transform.scale(screen, (s.get_width(), s.get_height()//2))

        return screen

    @classmethod
    def draw_background(cls, screen, fov, looking_direction, vertical_angle, map_, camera_plane_length, position,
                        height, threaded=None):
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

    class TempViewer(BillboardSprite.BillboardSprite):
        def __init__(self, origin: BillboardSprite.BillboardSprite, target: BillboardSprite.BillboardSprite,
                     set_viewer_method):
            self.target = target

            def spriteToFunc(sprite: BillboardSprite.BillboardSprite):
                return (lambda: sprite.position.x,
                        lambda: sprite.position.y,
                        lambda: sprite.looking_direction.angle(),
                        lambda: sprite.vertical_position)

            self.scroller = structures.Scroller(*spriteToFunc(target),
                                                *origin.position, origin.looking_direction.angle(), origin.vertical_position)
            super(Render3D.TempViewer, self).__init__(origin.position.copy(), (0, 0), )
            self.set_viewer_method = set_viewer_method

        def update(self, dt, keys):
            self.scroller.update()
            self.position.set_values(*self.scroller.current_position)
            if (self.target.position - self.position).magnitude_squared() < 5:
                self.set_viewer_method(self.target)

            self.looking_direction.set_values(*structures.Vector2.unit_vector(self.scroller.current_angle))
            self.vertical_position = self.scroller.current_height

    def __init__(self, player, map_, screen):
        self.z_buffer = None

        self.W, self.H = screen.get_size()
        self.player: Player3D = player
        self.map: FasterMap.Map = map_
        self.fov = 66
        self.fov = 60
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)
        self.resolution = 3

        pg_structures.Texture.initiate_handler(self.resolution)
        self.screen = screen

        ceiling_colour = (50, 50, 50)
        floor_colour = (80, 80, 80)

        # self.texture = pygame.image.load('Assets/Images/Textures/wood_wall.png').convert()

        bg = pygame.image.load('Assets/Images/Background/bgr edited.png').convert()
        ratio = screen.get_width() / (bg.get_width() / 3)

        bg = pygame.transform.smoothscale(bg,
                                          (int(bg.get_width() * ratio),
                                           int(bg.get_height() * ratio)))

        bg = bg.subsurface((0, 0, bg.get_width(), bg.get_height() // 2)).convert()
        # Background.set_background(
        #     structures.BackgroundType.textured,
        #     structures.BackgroundType.textured,
        #     r'greystone.png',
        #     None,
        #     *self.screen.get_size()
        # )

        Background.set_background(
            structures.BackgroundType.panoramic,
            structures.BackgroundType.textured,
            bg,
            (r'Textures\Named\wood.png', r'Textures/galletcity.png'),
            # None,
            *self.screen.get_size()
        )
        Render3D.instance = self

        texture = pygame.image.load(r'Assets\Images\Sprites\transparentBarrel.png  ').convert()
        # texture.set_colorkey(pygame.Color('black'))
        # self.bill = BillboardSprite.BillboardSprite(texture, (250, 250), self.resolution)
        # self.bill = BillboardSprite.BillboardSprite(texture, (250 + 50 * 3, 250 + 50 * 1), self.resolution)
        # pillar = BillboardSprite.LostSoul(r'Sprites\Lost Soul\idle', (250 + 50 * 4, 250 + 50 * 1),
        #                                   self.resolution)
        # self.bill = BillboardSprite.BillboardSprite(texture, (75, 75), self.resolution)
        pillar = BillboardSprite.BillboardSprite(texture, (100, 110), vertical_scale=2, horizontal_scale=2)
        # pillar = BillboardSprite.LostSoul(r'Sprites\Lost Soul\idle', (150, 75), self.resolution)
        self.bill = BillboardSprite.LostSoul(r'Sprites\Lost Soul\idle', (100, 1450), self.resolution, )
        textures: dict = pg_structures.Texture.textures_list()
        lst = json.load(open(r'Assets\MapsFiles\sprites_map.pickle', 'rb'))
        ts = FasterMap.Map.instance.tile_size
        for (x, y), id_ in lst:
            BillboardSprite.BillboardSprite(textures[int(id_)], (x * ts + ts // 2, y * ts + ts // 2), vertical_scale=2,
                                            horizontal_scale=1)
        self.LS = PanoramicSprites.PanoramicLostSoul(player.position + (100, 1), structures.Vector2(1, 0))

        self.viewer = None
        self.set_viewer(self.player)

    def set_viewer(self, viewer: BillboardSprite.BillboardSprite, smooth=True):
        if isinstance(self.viewer, Render3D.TempViewer):
            self.viewer.kill()
        if self.viewer is None or not smooth:
            self.viewer = viewer
        else:
            temp = Render3D.TempViewer(self.viewer, viewer, lambda viewer: self.set_viewer(viewer, smooth=False))
            self.viewer = temp

    def render_rays(self):
        dir_ = self.viewer.looking_direction.normalized()
        camera_plane = dir_.tangent() * self.camera_plane_length
        self.cast_and_draw(dir_, camera_plane)

    def cast_and_draw(self, dir_, camera_plane):
        pos = self.map.to_local(self.viewer.position)
        resolution = self.resolution
        # screen = pygame.Surface(self.screen.get_size())
        screen = self.screen
        screen.set_colorkey(pygame.Color('black'))

        # texture = self.texture
        textures: dict = pg_structures.Texture.textures_list()
        heights = np.asarray([texture.texture.get_height() for texture in textures if not isinstance(texture, dict)])
        widths = np.asarray([texture.texture.get_width() for texture in textures if not isinstance(texture, dict)])
        # heights[0] = 0
        # widths[0] = 0
        # for id_, tex in enumerate(textures):
        #     if isinstance(tex, dict):
        #         continue
        #     heights[int(id_)] = tex.texture.get_height()
        #     widths[int(id_)] = tex.texture.get_width()
        for x, colStart, colHeight, yStart, yHeight, color, texX, buffer, tile_id in \
                FasterMap.cast_screen(self.W, resolution, self.map.map(), pos[0], pos[1], dir_.x, camera_plane.x,
                                      dir_.y,
                                      camera_plane.y, self.H, self.viewer.tilt, self.viewer.vertical_position,
                                      widths, heights):
            if x < 0:
                break
            if tile_id == 0:
                continue
            texture = textures[tile_id].texture
            # if 3:
            # pygame.draw.rect(screen, (color, color, color), (x, yStart, resolution, yHeight))
            if colHeight > 0 and colStart < heights[tile_id]:
                # column = texture.sca
                column = texture.subsurface((texX, colStart, 1, colHeight)).copy()
                column.fill((color, color, color), special_flags=pygame.BLEND_MULT)
                column = pygame.transform.scale(column, (resolution, yHeight))
                screen.blit(column, (x, yStart))
        self.z_buffer = buffer

        BillboardSprite.BillboardSprite.draw_all(self.viewer, self.camera_plane_length, self.W, self.H, self.z_buffer,
                                                 self.resolution, screen)
        return screen

    def render_background(self):
        Background.draw_background(self.screen, self.fov, self.viewer.looking_direction, self.viewer.tilt,
                                   self.map, self.camera_plane_length, self.viewer.position,
                                   self.viewer.vertical_position)


global_val = 0


def main():
    global global_val
    pygame.init()
    screen = pg_structures.DisplayMods.Windowed((800 * 16 // 9, 800))
    # screen = pg_structures.DisplayMods.FullScreenAccelerated()
    # resScale = 2
    # screen = pygame.Surface((1920/resScale, 1080/resScale)).convert()
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
    BillboardSprite.BillboardSprite.initiate(RenderSettings)

    player = Player3D(100, 1500)
    map_ = FasterMap.Map.from_file(r'Assets\MapsFiles\map.txt')
    # map_ = FasterMap.Map.from_file(r'MapsManipulations/map.txt', None)
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
                    global_val += .01
                elif event.button == 5:
                    player.with_ = True
                    global_val -= .01
                elif event.button == 1:
                    pistol.shoot()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    global_val = True
                elif event.key == pygame.K_j:
                    global_val = False
                elif event.key == pygame.K_g:
                    renderer.set_viewer(structures.toggle(renderer.bill, renderer.player))

        keys = pygame.key.get_pressed()

        renderer.render_rays()

        # player._update(elapsed, keys)
        Sprites.BaseSprite.update_all(elapsed, keys)
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
        elapsed = elapsed_real / 1000  # min(elapsed_real / 1000.0, 1 / 30)

        # new = screen
        # new = pygame.transform.scale(screen, real_screen.get_size(), real_screen)
        # pygame.transform.scale(screen, Realscreen.get_size(), Realscreen)
        pygame.display.update()

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
