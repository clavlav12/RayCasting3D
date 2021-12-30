from typing import Tuple
import structures
import numpy as np
from numba import njit


# arrauy


class Map(structures.Singleton):
    TILE_SIZE = 50

    def __init__(self, arr, tile_size=TILE_SIZE):
        self.__map = np.array(arr, np.int64)
        self.tile_size = tile_size

        self.width = len(self.columns())
        self.height = len(self.rows())

    def map(self):
        return self.__map

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as file:
            map_ = []
            line_size = None
            for line in file:
                line = line.strip().replace(' ', '')
                if (not len(line) == line_size) and (line_size is not None):
                    raise ValueError('Rows lengths are not uniform')
                line_size = len(line)
                l = list(line)
                l = [int(x) for x in l]
                map_.append(l)
        return cls(map_)

    def __str__(self):
        return '\n'.join(' '.join(line) for line in self.__map)

    def to_global(self, position):
        if isinstance(position, (int, float)):
            return position * self.tile_size
        return position[0] * self.tile_size, position[1] * self.tile_size

    def to_local(self, position):
        return position[0] / self.tile_size, position[1] / self.tile_size

    def get_size(self):
        return self.width, self.height

    def get_tile(self, x, y):
        return self.__map[y, x]

    def get_tile_global(self, x, y):
        x, y = int(x // self.tile_size), int(y // self.tile_size)
        return self.get_tile(x, y), (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.__map[:, item]
        elif isinstance(item, tuple):
            x, y = item
            return self.get_tile(x, y)
        raise TypeError(f'wrong use of subscriptable item  Map ({item})')

    def rows(self):
        return self.__map

    def columns(self):
        return self.__map.T

    def cast_ray(self, startX, startY, directionX, directionY):
        return cast_ray(self.__map, startX, startY, directionX, directionY, 1)


@njit(nogil=True, fastmath=True)
def cast_ray(array, start_x, start_y, direction_x, direction_y, widths):
    """
    Cast a ray from start_pos in the direction of the unit vector direction
    and returns it's length
    """
    height, width = array.shape

    step_x = abs(1 / direction_x) if direction_x != 0 else np.Inf
    step_y = abs(1 / direction_y) if direction_y != 0 else np.Inf

    # optimisation from:
    # step_size = structures.Vector2.Cartesian(
    #     hypot(1, direction.y / direction.x) if direction.x != 0 else float('inf'),
    #     hypot(1, direction.x / direction.y) if direction.y != 0 else float('inf')
    # )

    map_x = int(start_x)
    map_y = int(start_y)

    ray_length_x = 0
    ray_length_y = 0

    if direction_x > 0:  # To the right
        ray_length_x += (1 - (start_x - map_x)) * step_x
        step_dir_x = 1
    else:  # To the left
        ray_length_x += (start_x - map_x) * step_x
        step_dir_x = -1

    if direction_y > 0:  # To the right
        ray_length_y += (1 - (start_y - map_y)) * step_y
        step_dir_y = 1
    else:  # To the left
        ray_length_y += (start_y - map_y) * step_y
        step_dir_y = -1

    tile_found = 0
    while not tile_found:
        if ray_length_x < ray_length_y:
            map_x += step_dir_x
            ray_length_x += step_x
            side = True
        else:
            map_y += step_dir_y
            ray_length_y += step_y
            side = False
        if 0 <= map_x < width and 0 <= map_y < height:
            if array[map_y, map_x] != 0:
                tile_found = array[map_y, map_x]
        else:
            break

    if side:  # stepX = step_dir.x -> rayDirX = direction.x
        wall_distance = (map_x - start_x + (1 - step_dir_x) / 2) / direction_x
    else:
        wall_distance = (map_y - start_y + (1 - step_dir_y) / 2) / direction_y

    # intersection_x = start_x + direction_x * wall_distance
    # intersection_y = start_y + direction_y * wall_distance

    if side:
        wallX = start_y + wall_distance * direction_y
    else:
        wallX = start_x + wall_distance * direction_x
    # wallX2 = abs((wallX - int(wallX)) - 1) -> reverses the texture
    wallX -= int(wallX)

    tex_width = widths[tile_found]
    texX = int(wallX * tex_width)

    if side and direction_x > 0:
        texX = tex_width - texX - 1
    if (not side) and direction_y < 0:
        texX = tex_width - texX - 1

    return wall_distance, side, texX, tile_found


empty = np.empty(0, np.float64)


@njit(nogil=True)
def cast_screen(W, resolution, array, pos_x, pos_y, dir_x, camera_x, dir_y, camera_y, H, tilt, height, tex_widths,
                tex_heights, walls_ratio=1):
    """Casts really really fast, but it takes another iteration to draw the lines so it is not efficient"""
    z_buffer = np.zeros(W, np.float64)
    inv_height = 2 - height

    for x in range(0, W, resolution):
        pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
        length, side, texX, tile_id = cast_ray(array, pos_x, pos_y, dir_x + camera_x * pixel_camera_pos,
                                      dir_y + camera_y * pixel_camera_pos, tex_widths)

        line_height = int(walls_ratio * H // length)

        draw_start = - inv_height * line_height / 2 + H / 2 + tilt

        c = max(1, int((255.0 - length * 20) * (1 - side * 0.25)))  # length coefficient
        # measures how distance affect brightness. Side coefficient measures how sunlight affects the brightness (.25)
        # seems to be the right choice

        draw_end = draw_start + line_height

        tex_height = tex_heights[tile_id]
        y_start = max(-tex_height, draw_start)
        y_stop = min(H + tex_height, draw_end)
        pixels_per_texel = line_height / tex_height
        col_start = int((y_start - draw_start) / pixels_per_texel + .5)
        col_height = int((y_stop - y_start) / pixels_per_texel + .5)

        y_texture_start = col_start * pixels_per_texel
        y_start = int(y_texture_start + draw_start + .5)
        y_height = int(col_height * pixels_per_texel + .5)

        z_buffer[x] = length

        yield x, y_texture_start, y_start, y_height, line_height, c, texX, empty, tile_id

    yield -1, y_texture_start, y_start, y_height, line_height, c, texX, z_buffer, 0


@njit(nogil=True)
def cast_floor_ceiling(dir_x, dir_y, camera_x, camera_y, W, H, pos_x, pos_y, floor_texture, ceiling_texture,
                       floor, ceiling, h, vertical_angle):
    # H = H // 4
    # W = W // 4
    is_floor = not (0, 0) == floor_texture.shape
    is_ceiling = not (0, 0) == ceiling_texture.shape
    if is_floor and not is_ceiling:
        text_width, text_height = floor_texture.shape
    elif is_ceiling and not is_floor:
        text_width, text_height = ceiling_texture.shape
    elif floor_texture.shape == ceiling_texture.shape:
        text_width, text_height = ceiling_texture.shape
    else:
        raise ValueError('Texture sizes do not match')

    # negative vertical_angle means down!
    if is_floor and not is_ceiling:
        vertical_angle = - vertical_angle  # needs to draw more when looking down and less if looking down
    elif is_ceiling and not is_floor:
        h = 2 - h
    height = (floor + ceiling) * H // 2
    buffer = np.zeros((W, max(height + vertical_angle, 0)), np.int8)
    for y in range(H // 2 + 1, H + vertical_angle):
        # rayDir for leftmost ray (x = 0) and rightmost ray (x = w)
        ray_dir_x0 = dir_x - camera_x
        ray_dir_y0 = dir_y - camera_y
        ray_dir_x1 = dir_x + camera_x
        ray_dir_y1 = dir_y + camera_y

        # Current y position compared to the center of the screen (the horizon)
        p = y - H // 2

        # Vertical position of the camera.
        pos_z = H * h / 2

        # Horizontal distance from the camera to the floor for the current row.
        # 0.5 is the z position exactly in the middle between floor and ceiling.
        row_distance = pos_z / p

        # calculate the real world step vector we have to add for each x (parallel to camera plane)
        # adding step by step avoids multiplications with a weight in the inner loop
        floor_step_x = row_distance * (ray_dir_x1 - ray_dir_x0) / W
        floor_step_y = row_distance * (ray_dir_y1 - ray_dir_y0) / W

        # real world coordinates of the leftmost column. This will be updated as we step to the right.
        floor_x = pos_x + row_distance * ray_dir_x0
        floor_y = pos_y + row_distance * ray_dir_y0

        for x in range(W):
            cell_x = int(floor_x)
            cell_y = int(floor_y)

            tx = int(text_width * (floor_x - cell_x))
            ty = int(text_height * (floor_y - cell_y))

            floor_x += floor_step_x
            floor_y += floor_step_y

            # print('before:', format(color, '032b'))
            # color <<= 1
            # print('after:', format(color, '032b'))
            # color = (color >> 1) & 8355711
            # print(row_distance)
            if floor:
                color = floor_texture[tx, ty]
                buffer[x, y - height] = color
            if ceiling:
                color = ceiling_texture[tx, ty]
                buffer[x, height - y - 1] = color
    return buffer


if __name__ == '__main__':
    import pygame
    texture = pygame.image.load('Assets/Images/Textures/Blood Wall Dark.png')

    arr = pygame.surfarray.array2d(texture)
    buffer = cast_floor_ceiling(0.91632, 0.40044, -0.23119, 0.52904, 1920, 1080, 3.10000002, 3.10000002, arr)

    image = pygame.surfarray.make_surface(buffer)

    pygame.image.save(image, 'floor.png')
#     fast = Map.from_file('map2.txt')
#
#     import timeit
#
#     l = '''
# c = cast_screen(1920, 1, fast.map(), 3.10000002, 3.10000002, 0.9297758477079633,
#                  -0.23906392650695832, 0.36812616454000946, 0.6038034954732037, 1080, -156.0, 1.0)
# for i in c:
#     pass
#     '''
#     print(1, timeit.timeit(l,
#                            number=1000,
#                            globals=globals(),
#                            setup=l
#                            ))
