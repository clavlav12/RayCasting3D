from typing import Tuple
import structures


class Map(structures.Singleton):
    TILE_SIZE = 50

    def __init__(self, arr, tile_size=TILE_SIZE):
        self.__map = arr
        self.__regular_map = [*zip(*self.__map)]
        self.tile_size = tile_size

        self.width = len(self.columns())
        self.height = len(self.rows())

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
        return self.__map[y][x]

    def get_tile_global(self, x, y):
        x, y = int(x // self.tile_size), int(y // self.tile_size)
        return self.get_tile(x, y), (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.__regular_map[item]
        elif isinstance(item, tuple):
            x, y = item
            return self.get_tile(x, y)
        elif isinstance(item, slice):
            return self.__regular_map[item]
        raise TypeError(f'wrong use of subscriptable item  Map ({item})')

    def rows(self):
        return self.__map

    def columns(self):
        return self.__regular_map

    def cast_ray(self, startX, startY, directionX, directionY) \
            -> Tuple[float, structures.Vector2, bool]:
        """
        Cast a ray from start_pos in the direction of the unit vector direction
        and returns it's length
        """

        stepX = abs(1 / directionX) if directionX != 0 else float('inf')
        stepY = abs(1 / directionY) if directionY != 0 else float('inf')


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
            if 0 <= mapX < self.width and 0 <= mapY < self.height:
                if self.__regular_map[mapX][mapY] != 0:
                    tile_found = True
            else:
                break

        if not side:  # stepX = step_dir.x -> rayDirX = direction.x
            wall_distance = (mapX - startX + (1 - stepDirX) / 2) / directionX
        else:
            wall_distance = (mapY - startY + (1 - stepDirY) / 2) / directionY

        # intersection = start_pos + direction * distance
        #
        return wall_distance, side

    def cast_ray2(self, start_pos: structures.Vector2, direction: structures.Vector2) \
            -> Tuple[float, structures.Vector2, bool]:
        """
        Cast a ray from start_pos in the direction of the unit vector direction
        and returns it's length
        """
        step_size = structures.Vector2(
            abs(1 / direction.x) if direction.x != 0 else float('inf'),
            abs(1 / direction.y) if direction.y != 0 else float('inf')
        )

        # optimisation from:
        # step_size = structures.Vector2.Cartesian(
        #     hypot(1, direction.y / direction.x) if direction.x != 0 else float('inf'),
        #     hypot(1, direction.x / direction.y) if direction.y != 0 else float('inf')
        # )

        step_dir = direction.sign()

        start_pos = structures.Vector2(*self.to_local(start_pos))

        relative_pos, map_pos = start_pos.modf()

        map_pos = map_pos.floor()

        ray_length = structures.Vector2(0, 0)

        if direction.x > 0:  # To the right
            ray_length.x += (1 - relative_pos.x) * step_size.x
        elif direction.x < 0:  # To the left
            ray_length.x += relative_pos.x * step_size.x

        if direction.y > 0:  # Down
            ray_length.y += (1 - relative_pos.y) * step_size.y
        elif direction.y < 0:  # Up
            ray_length.y += relative_pos.y * step_size.y

        tile_found = False
        distance = 0
        while not tile_found:
            if ray_length.x < ray_length.y:
                map_pos.x += step_dir.x
                distance = ray_length.x
                ray_length.x += step_size.x
                side = False
            else:
                map_pos.y += step_dir.y
                distance = ray_length.y
                ray_length.y += step_size.y
                side = True
            if 0 <= map_pos.x < self.width and 0 <= map_pos.y < self.height:
                if self[tuple(map_pos)] != '0':
                    tile_found = True
            else:
                break

        if not side:  # stepX = step_dir.x -> rayDirX = direction.x
            wall_distance = (map_pos.x - start_pos.x + (1 - step_dir.x) / 2) / direction.x
        else:
            wall_distance = (map_pos.y - start_pos.y + (1 - step_dir.y) / 2) / direction.y

        intersection = start_pos + direction * distance

        return wall_distance, side


if __name__ == '__main__':
    map_ = Map.from_file('map3.txt')
    print(map_.cast_ray(structures.Vector2.Cartesian(1, 1), structures.Vector2.Polar(1, 89)))
