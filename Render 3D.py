from Player import Player
from Map import Map
import structures


class Player3D(Player):
    pass


class Render3D:
    def __init__(self, player, map_):
        self.player: Player3D = player
        self.map: Map = map_
        self.fov = 90
        self.camera_plane_length = structures.DegTrigo.tan(self.fov / 2)

    def draw_screen(self, W, H):
        for x in range(W):
            camera_plane = self.player.direction.tangent() * self.camera_plane_length
            pixel_camera_pos = 2 * x / W - 1  # Turns the screen to coordinates from -1 to 1
            ray_direction = self.player.direction + camera_plane * pixel_camera_pos
            distance = self.map.cast_ray(self.player.position, ray_direction)
