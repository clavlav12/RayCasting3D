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
        return cast_ray(self.__map, startX, startY, directionX, directionY)


@njit(nogil=True)
def cast_ray(array: np.array, startX, startY, directionX, directionY, texWidth):
    """
    Cast a ray from start_pos in the direction of the unit vector direction
    and returns it's length
    """

    height, width = array.shape

    stepX = abs(1 / directionX) if directionX != 0 else np.Inf
    stepY = abs(1 / directionY) if directionY != 0 else np.Inf

    # optimisation from:
    # step_size = structures.Vector2.Cartesian(
    #     hypot(1, direction.y / direction.x) if direction.x != 0 else float('inf'),
    #     hypot(1, direction.x / direction.y) if direction.y != 0 else float('inf')
    # )

    mapX = int(startX)
    mapY = int(startY)

    rayLengthX = 0
    rayLengthY = 0

    if directionX > 0:  # To the right
        rayLengthX += (1 - (startX - mapX)) * stepX
        stepDirX = 1
    else:  # To the left
        rayLengthX += (startX - mapX) * stepX
        stepDirX = -1

    if directionY > 0:  # To the right
        rayLengthY += (1 - (startY - mapY)) * stepY
        stepDirY = 1
    else:  # To the left
        rayLengthY += (startY - mapY) * stepY
        stepDirY = -1

    tile_found = False
    while not tile_found:
        if rayLengthX < rayLengthY:
            mapX += stepDirX
            rayLengthX += stepX
            side = False
        else:
            mapY += stepDirY
            rayLengthY += stepY
            side = True
        if 0 <= mapX < width and 0 <= mapY < height:
            if array[mapY, mapX] != 0:
                tile_found = True
        else:
            break

    if not side:  # stepX = step_dir.x -> rayDirX = direction.x
        wall_distance = (mapX - startX + (1 - stepDirX) / 2) / directionX
    else:
        wall_distance = (mapY - startY + (1 - stepDirY) / 2) / directionY

    # intersection = start_pos + direction * distance
    #

    if not side:
        wallX = startY + wall_distance * directionY
    else:
        wallX = startX + wall_distance * directionX
    wallX = abs((wallX - int(wallX)) - 1)

    texX = int(wallX * texWidth)
    if side == 0 and directionX > 0: texX = texWidth - texX - 1
    if side == 1 and directionY < 0: texX = texWidth - texX - 1

    return wall_distance, side, texX


@njit(nogil=True)
def cast_screen(W, resolution, array, posX, posY, dirX, cameraX, dirY, cameraY, H, tilt, height, texWidth,
                walls_ratio=1):
    """Casts really really fast, but it takes another iteration to draw the lines so it is not efficient"""
    inv_height = 2 - height
    for x in range(0, W, resolution):
        pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
        length, side, texX = cast_ray(array, posX, posY, dirX + cameraX * pixel_camera_pos,
                                      dirY + cameraY * pixel_camera_pos, texWidth)

        line_height = walls_ratio * H / length #if length != 0 \
           # else H  # Multiply by a greater than one value to make walls higher

        draw_start = - inv_height * line_height / 2 + H / 2 + tilt
        # if draw_start < 0:
        #     line_height += draw_start
        #     draw_start = 0

        c = max(1, int((255.0 - length * 27.2) * (1 - side * .25)))

        yield x, draw_start, line_height, c, texX


@njit(nogil=True)
def cast_screen_partly(start, end, W, resolution, array, posX, posY, dirX, cameraX, dirY, cameraY, H, tilt, height,
                       walls_ratio=.5):
    """Casts really really fast, but it takes another iteration to draw the lines so it is not efficient"""
    inv_height = 2 - height
    for x in range(start, end, resolution):
        pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
        length, side = cast_ray(array, posX, posY, dirX + cameraX * pixel_camera_pos,
                                dirY + cameraY * pixel_camera_pos)

        line_height = walls_ratio * H / length if length != 0 \
            else H  # Multiply by a greater than one value to make walls higher

        draw_start = - inv_height * line_height / 2 + H / 2 + tilt
        if draw_start < 0:
            line_height += draw_start
            draw_start = 0

        c = max(1, int((255.0 - length * 27.2) * (1 - side * .25)))
        yield x, draw_start, line_height, c


if __name__ == '__main__':
    fast = Map.from_file('map2.txt')

    import timeit

    l = '''
c = cast_screen(1920, 1, fast.map(), 3.10000002, 3.10000002, 0.9297758477079633,
                 -0.23906392650695832, 0.36812616454000946, 0.6038034954732037, 1080, -156.0, 1.0)
for i in c:
    pass
    '''
    print(1, timeit.timeit(l,
                           number=1000,
                           globals=globals(),
                           setup=l
                           ))
