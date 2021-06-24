import structures
from math import sqrt, hypot


class Map(structures.Singleton):
    TILE_SIZE = 50

    def __init__(self, arr, tile_size=TILE_SIZE):
        self._map = arr
        self._regular_map = [*zip(*self._map)]
        self.tile_size = tile_size
        
        self.width = len(self.columns())
        self.height = len(self.rows())

        self.slant = hypot(self.height, self.width)

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
                map_.append(list(line))
        return cls(map_)

    def __str__(self):
        return '\n'.join(' '.join(line) for line in self._map)

    def to_global(self, position):
        return position[0] * self.tile_size, position[1] * self.tile_size

    def to_local(self, position):
        return position[0] / self.tile_size, position[1] / self.tile_size

    def get_size(self):
        return len(self._map[0]), len(self._map)

    def get_tile(self, x, y):
        return self._map[y][x]

    def get_tile_global(self, x, y):
        x, y = int(x // self.tile_size), int(y // self.tile_size)
        return self._map[y][x], (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._regular_map[item]
        elif isinstance(item, tuple):
            x, y = item
            return self._regular_map[x][y]
        elif isinstance(item, slice):
            return self._regular_map[item]
        raise TypeError(f'wrong use of subscriptable item  Map ({item})')

    def rows(self):
        return self._map

    def columns(self):
        return self._regular_map

    def cast_ray(self, start_pos: structures.Vector2, direction: structures.Vector2) -> float:
        """
        Cast a ray from start_pos in the direction of the unit vector direction
        and returns it's length
        """
        slope = direction.y / direction.x
        step_size = structures.Vector2.Cartesian(
            hypot(1, slope), hypot(1, 1/slope)
        )

        step_dir = direction.sign()
        
        start_pos = structures.Vector2.Point(self.to_local(start_pos))

        relative_pos, map_pos = start_pos.modf()

        map_pos = map_pos.floor()

        ray_length = structures.Vector2.Zero()

        if step_dir.x > 0:  # To the right
            ray_length.x += (1-relative_pos.x) * step_size.x
        elif step_dir.x < 0:  # To the left
            ray_length.x += relative_pos.x * step_size.x

        if step_dir.y > 0:  # Down
            ray_length.y += (1-relative_pos.y) * step_size.y
        elif step_dir.y < 0:  # Up
            ray_length.y += relative_pos.y * step_size.y

        tile_found = False
        distance = 0
        while distance < self.slant and not tile_found:
            if ray_length.x < ray_length.y:
                map_pos.x += step_dir.x
                distance = ray_length.x
                ray_length.x += step_size.x
            else:
                map_pos.y += step_dir.y
                distance = ray_length.y
                ray_length.y += step_size.y
            if 0 <= map_pos.x < self.width and 0 <= map_pos.y < self.height:
                if self[tuple(map_pos)] != '0':
                    tile_found = True

        intersection = start_pos + direction * distance
        return distance * self.tile_size, intersection * self.tile_size


if __name__ == '__main__':
    map_ = Map.from_file('map3.txt')
    print(map_.cast_ray(structures.Vector2.Cartesian(1, 1), structures.Vector2.Polar(1, 89)))
    print(hypot(map_.tile_size, map_.tile_size))
