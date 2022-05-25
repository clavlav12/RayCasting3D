import pygame as pg
import os

d = r'D:\GitHub Repositories\RayCasting3D\Assets\Images\Textures\Mapped2'
for file in os.listdir(d):
    fn = d + '/' + file
    old = pg.image.load(fn)
    empty = pg.Surface((old.get_width(), old.get_height() * 2), pg.SRCALPHA)
    empty.blit(old, (0, old.get_height()))
    pg.image.save(empty, fn)