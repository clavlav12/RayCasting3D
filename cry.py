import pygame


# def int_to_rgb(x):
#     return (x << 4) >> 4, (x << 2) >> 8, (x) >> 8


# print([int_to_rgb(i) for i in range(256)])
# sur.set_palette([int_to_rgb(i) for i in range(256)])

sur = pygame.image.load('Assets/Images/Textures/wood.png')

# (0, 0 , 0)

load = pygame.image.load('new_wood.png')
ceiling_texture = pygame.surfarray.array2d(
    sur
)

# mapped = pygame.surfarray.map_array(sur, ceiling_texture)
r = (ceiling_texture[0, 0]) << 8) // 256
final = pygame.surfarray.make_surface(ceiling_texture / 256 )
# print(len(final.get_palette()))
pygame.image.save(final, 'floor.png')

