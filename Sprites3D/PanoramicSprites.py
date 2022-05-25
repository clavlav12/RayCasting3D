import Sprites3D.BillboardSprite
from collections import namedtuple
from operator import sub
import structures
from FasterMap import Map


class closestDict(dict):
    def closest(self, item, operator=sub):
        """
        :param item: The item you want the closest key to
        :param operator: The operator used to compare items (returns an integer value that
            represents how close they are - closer to zero means closer)
        :return: value of they key that is closest to item
        """
        if not self:
            raise ValueError("No keys to compare to")
        current_key = None
        current_closeness = float('inf')

        for key in self:
            closeness = abs(operator(key, item))
            if closeness < current_closeness:
                current_key = key
                current_closeness = closeness
        return self[current_key]


class DirectionalSprite(Sprites3D.BillboardSprite.BillboardSprite):
    """
    Sprites that have a looking direction
    """

    def __init__(self, position, looking_direction, animations_dict, velocity=(0, 0)):
        super(DirectionalSprite, self).__init__(None, position, 3, velocity=velocity, looking_direction=structures.Vector2(*looking_direction))

        self.animations = closestDict((angle, self.get_animation(texture)) for angle, texture in animations_dict.items())
        #
        #    *sprite* ^
        #
        #             *viewer* ^
        #
        # 0 degrees - looking same direction
        # 90 degrees - rotated right
        # 180 degrees - facing directly

    def rotate(self, deg, radians=False):
        self.looking_direction *= structures.RotationMatrix(deg, radians)

    def set_looking_direction(self, new):
        self.looking_direction.set_values(new)

    def draw_3D(self, viewer, *args, **kwargs):
        self.animation = self.animations.closest(((self.position - Map.instance.to_global(viewer.position)).angle() - viewer.looking_direction.angle()) % 360)
        super(DirectionalSprite, self).draw_3D(viewer, *args, **kwargs)


class PanoramicLostSoul(DirectionalSprite):
    def __init__(self, position, looking_direction):
        super(PanoramicLostSoul, self).__init__(position, looking_direction,
                                                {
                                                    90+45*0: r'Sprites\3D_Attempt\0',
                                                    90+45*1: r'Sprites\3D_Attempt\315',
                                                    90+45*2: r'Sprites\3D_Attempt\270',
                                                    90+45*3: r'Sprites\3D_Attempt\225',
                                                    (90+45*4) % 360: r'Sprites\3D_Attempt\180',
                                                    (90+45*5) % 360: r'Sprites\3D_Attempt\135',
                                                    (90+45*6) % 360: r'Sprites\3D_Attempt\90',
                                                    (90+45*7) % 360: r'Sprites\3D_Attempt\45'
                                                }
                                                )
        for animation in self.animations.values():
            animation.modify_images(lambda image: image.set_colorkey((0, 255, 255)))

    # def update_bef(self, dt, keys):
    #     self.looking_direction *= structures.RotationMatrix()