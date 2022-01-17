import json
import pickle
from typing import List
import numpy as np
import random
from pygame import *
from pygame.locals import *


def subsample_hash(a: Surface):
    array: np.ndarray = surfarray.array2d(a)
    return array.tobytes()


def read_sprite_sheet(tile_size, sheet):
    sheet = image.load(sheet)
    lst = []

    for y in range(0, sheet.get_height(), tile_size):
        for x in range(0, sheet.get_width(), tile_size):
            lst.append(sheet.subsurface((x, y, tile_size, tile_size)).copy())

    return lst

ts = 8
tiles = read_sprite_sheet(ts, 'galletcity_tiles.png')
hashes = [subsample_hash(t) for t in tiles]
import TileSelection
from pickle import dump, load

try:
    walls_selected = load(open('walls_selected.pickle', 'rb'))
except FileNotFoundError:
    walls_selected = None

try:
    sprites_selected = load(open('sprites_selected.pickle', 'rb'))
except FileNotFoundError:
    sprites_selected = None

walls_selected, sprites_selected = TileSelection.tile_selection_window(tiles, walls_selected=walls_selected, sprites_selected=sprites_selected)
selected = walls_selected.union(sprites_selected)
selected_hashed = {subsample_hash(tiles[index]) for index in selected}
sprites_hashed = {subsample_hash(tiles[index]) for index in sprites_selected}

dump(walls_selected, open('walls_selected.pickle', 'wb'))
dump(sprites_selected, open('sprites_selected.pickle', 'wb'))

tile_map = image.load('galletcity_walls.png')

buffer = ''

sprites = [] # (position: tuple, texture_index: int)
for column in range(0, tile_map.get_height(), ts):
    for row in range(0, tile_map.get_width(), ts):
        tile = tile_map.subsurface((row, column, ts, ts)).copy()
        tile_hash = subsample_hash(tile)
        if tile_hash in selected_hashed:
            buffer += '0 '
            if tile_hash in sprites_hashed:
                sprites.append(((row // ts, column // ts), str(hashes.index(tile_hash))))
        else:
            buffer += str(hashes.index(tile_hash)) + ' '

    buffer += '\n'


with open('map.txt', 'w') as file:
    file.write(buffer)
with open('sprites_map.pickle', 'w') as file:
    json.dump(sprites, file)
