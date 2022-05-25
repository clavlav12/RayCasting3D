import sys

import pygame
from pygame.locals import *

from typing import List
from math import sqrt


def tile_selection_window(tiles_list: List[pygame.Surface], walls_selected=None, sprites_selected=None):
    if walls_selected is None:
        walls_selected = set()
    if sprites_selected is None:
        sprites_selected = set()
    tile_size = tiles_list[0].get_width()

    length = len(tiles_list)

    greatest_divisor = -1
    for i in range(1, int(sqrt(length))):
        if length % i == 0:
            greatest_divisor = max(greatest_divisor, i)

    dimensions = (greatest_divisor, length // greatest_divisor)
    pygame.init()

    fps = 60
    fpsClock = pygame.time.Clock()

    width, height = (d * tile_size for d in dimensions)
    scale = 3
    actual_screen = pygame.display.set_mode((width * scale, height * scale))
    screen = pygame.Surface((width, height))
    screen.convert()

    walls_selected_mark = pygame.Surface((tile_size, tile_size)).convert()
    walls_selected_mark.fill((200, 130, 130))
    sprites_selected_mark = pygame.Surface((tile_size, tile_size)).convert()
    sprites_selected_mark.fill((130, 130, 255))
    # pygame.draw.rect(selected_mark, (0, 0, 0), (0, 0, tile_size, tile_size), 1)

    # Game loop.
    running = 1
    while running:
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == QUIT:
                running = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                tile = int(pos[0] / scale // tile_size + pos[1] / scale // tile_size * dimensions[0])
                if event.button == 1:  # left click
                    if tile in walls_selected:
                        walls_selected.remove(tile)
                    else:
                        walls_selected.add(tile)

                elif event.button == 3:  # right click
                    if tile in sprites_selected:
                        sprites_selected.remove(tile)
                    else:
                        sprites_selected.add(tile)

        for x in range(0, dimensions[0]):
            for y in range(0, dimensions[1]):
                screen.blit(tiles_list[x + y * dimensions[0]], (x * tile_size, y * tile_size))

        for index in walls_selected:
            screen.blit(walls_selected_mark, (index % dimensions[0] * tile_size, index // dimensions[0] * tile_size), special_flags=pygame.BLEND_MULT)
        for index in sprites_selected:
            screen.blit(sprites_selected_mark, (index % dimensions[0] * tile_size, index // dimensions[0] * tile_size), special_flags=pygame.BLEND_MULT)
        pygame.transform.scale(screen, (actual_screen.get_size()), actual_screen)
        pygame.display.flip()
        fpsClock.tick(fps)

    pygame.quit()
    return walls_selected, sprites_selected
