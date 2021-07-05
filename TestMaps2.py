from math import sin, cos, radians, hypot
import Map
import FasterMap

fast = FasterMap.Map.from_file('map2.txt')
map_ = Map.Map.from_file('map2.txt')
# a = radians(45)

# def rotate(angle, x, y):
#     r = hypot(x, y)
#     return r * cos(angle), r * sin(r)
# 1.6301367260523387 4.479863273947661 0.9390349378601008 -0.34382173502859975 506.0563250398058

dirX = 0.9390349378601008
dirY = -0.34382173502859975
posX = 1.6301367260523387
posY = 4.479863273947661

cameraX = -0.6427964233227306
cameraY = -0.09242824387647106

# dirX, dirY = rotate(a, dirX, dirY)
# cameraX, cameraY = rotate(a, cameraX, cameraY)

W = 1000


def cast():
    x = 243
    if x:
        pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
        length1, side1 = fast.cast_ray(posX, posY, dirX + cameraX * pixel_camera_pos,
                                       dirY + cameraY * pixel_camera_pos)

        print(length1, length2)

cast()
# 3.0 3.0 [1.00000, -0.00007] 4508473165.751536

# 3.0 3.0 [1.00000, 0.00010] -2719053883.910109

# 3.0 3.0 [-0.99999, 0.00438] 150.00167892937822

# print(map_.cast_ray(3.0, 3.0, -0.99999,  0.00438))
