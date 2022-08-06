from dataclasses import dataclass, asdict, astuple
from typing import Union
from enum import Enum, auto
from threading import Thread
import math


class ValueThread(Thread):
    def __init__(self, target, args=(), kwargs=None):
        super(ValueThread, self).__init__()
        if kwargs is None:
            kwargs = {}
        self.target = target
        self.kwargs = kwargs
        self.args = args
        self.value = None

    def run(self):
        self.value = self.target(*self.args, **self.kwargs)


def sign(x):
    return -1 if x < 0 else 1 if x > 0 else 0


class SingletonError(Exception):
    def __init__(self, cls):
        super(SingletonError, self).__init__(
            f'an instance of singleton class {cls.__name__!r} already exists'
        )


class SingletonMeta(type):

    def __new__(mcs, name, bases, attr):
        sub_class = type.__new__(mcs, name, bases, attr)
        sub_class.instance = None
        return sub_class

    def __call__(cls, *args, **kwargs):
        if cls.instance is not None:
            raise SingletonError(cls)
        instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        cls.instance = instance
        return instance


class Singleton(metaclass=SingletonMeta):
    pass


class PrivateConstructorMeta(type):

    def __new__(mcs, name, bases, attr):
        sub_class = type.__new__(mcs, name, bases, attr)
        sub_class._key = object()
        return sub_class

    def __call__(cls, *args, key=None, **kwargs):
        if key is not cls._key:
            raise PermissionError(f"Access denied to private constructor of class {cls.__name__!r}")
        return super(PrivateConstructorMeta, cls).__call__(*args, **kwargs)


class PrivateConstructor(metaclass=PrivateConstructorMeta):
    pass


class VectorType(Enum):
    cartesian = 1
    polar = 2


class BackgroundType(Enum):
    panoramic = auto()
    solid = auto()
    image = auto()
    textured = auto()


class DegTrigo:

    @staticmethod
    def deg_to_rad(deg):
        return math.radians(deg)

    @staticmethod
    def rad_to_deg(rad):
        return math.radians(rad)

    @staticmethod
    def atan(value):
        return math.degrees(math.atan(value))

    @classmethod
    def atan1(cls, x, y):  # 0 to 360
        if (x > 0) and (y >= 0):
            return cls.atan(y / x)
        elif (x > 0) and (y < 0):
            return cls.atan(y / x) + 360
        elif x < 0:
            return cls.atan(y / x) + 180
        elif (x == 0) and (y > 0):
            return 90
        elif (x == 0) and (y < 0):
            return 270
        return 0

    @classmethod
    def atan2(cls, x, y):  # -180 to 180
        if x > 0:
            return cls.atan(y / x)
        elif (x < 0) and (y >= 0):
            return cls.atan(y / x) + 180
        elif (x < 0) and (y < 0):
            return cls.atan(y / x) - 180
        elif (x == 0) and (y > 0):
            return 90
        elif (x == 0) and (y < 0):
            return -90
        return 0

    @staticmethod
    def asin(value):
        return math.degrees(math.asin(value))

    @staticmethod
    def acos(value):
        return math.degrees(math.acos(value))

    @staticmethod
    def sin(value):
        return math.sin(math.radians(value))

    @staticmethod
    def cos(value):
        return math.cos(math.radians(value))

    @staticmethod
    def tan(value):
        return math.tan(math.radians(value))


class RotationMatrix:
    ROT_INIT = False
    ROT90 = None
    ROT180 = None
    ROT270 = None

    def __init__(self, angle, radians=False):
        if not radians:
            angle = math.radians(angle)
        self.m00 = math.cos(angle)
        self.m10 = -math.sin(angle)
        self.m01 = -self.m10
        self.m11 = self.m00

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.m00 * other.x + self.m10 * other.y, self.m01 * other.x + self.m11 * other.y)
        return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __str__(self):
        return f'[  {self.m00}  {self.m10}' \
               f'   {self.m01}  {self.m11}   ]'

    @classmethod
    def init(cls):
        if not RotationMatrix.ROT_INIT:
            RotationMatrix.ROT_INIT = True
            RotationMatrix.ROT90 = RotationMatrix(90)
            RotationMatrix.ROT180 = RotationMatrix(180)
            RotationMatrix.ROT270 = RotationMatrix(270)


RotationMatrix.init()


class Vector2:
    def __init__(self, x, y):  # parm = (r, theta) or (x, y)
        self.x = x
        self.y = y

    @classmethod
    def unit_vector(cls, angle):
        return Vector2(DegTrigo.cos(angle), DegTrigo.sin(angle))

    def angle(self):
        return math.degrees(math.atan2(self.y, self.x))  # + 180

    def mag(self):
        return math.hypot(self.x, self.y)

    def normalized(self):
        mag = math.hypot(self.x, self.y)
        return Vector2(self.x / mag, self.y / mag)

    def sign(self):
        return Vector2(sign(self.x), sign(self.y))

    def tangent(self):
        return Vector2(-self.y, self.x)

    def floor(self):
        return Vector2(int(self.x), int(self.y))

    def set_values(self, x=None, y=None):
        self.x = x or self.x
        self.y = y or self.y

    def __round__(self, n=None):
        return Vector2(round(self.x, n), round(self.y, n))

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __pos__(self):
        return Vector2(self.x, self.y)

    def __add__(self, other):  # + operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, self.__class__):
            return Vector2(self.x + other.x, self.y + other.y)
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot add a scalar to a vector")
        return NotImplemented

    def __iadd__(self, other):  # += operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, self.__class__):
            self.x += other.x
            self.y += other.y
            return self
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot add a scalar to a vector")
        return NotImplemented

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):  # - operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, self.__class__):
            return Vector2(self.x - other.x, self.y - other.y)
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot subtract a scalar from a vector")
        return NotImplemented

    def __isub__(self, other):  # -= operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, self.__class__):
            self.x -= other.x
            self.y -= other.y
            return self
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot subtract a scalar from a vector")
        return NotImplemented

    def __rsub__(self, other):
        return (-self) + other

    def __mul__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, (int, float)):
            return Vector2(self.x * other, self.y * other)
        elif isinstance(other, self.__class__):
            "Returns the dot product of the vectors"
            return self.x * other.x + self.y * other.y
        return NotImplemented

    def __imul__(self, other):
        if isinstance(other, (int, float)):
            self.r *= other
            return self
        return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, (int, float)):
            return Vector2(self.x / other, self.y / other)
        elif isinstance(other, self.__class__):
            "Returns the inverse of the dot product of the vectors"
            return self.x / other.x + self.y / other.y
        return NotImplemented

    def __itruediv__(self, other):
        if isinstance(other, (int, float)):
            self.x /= other
            self.y /= other
            return self
        return NotImplemented

    def __rtruediv__(self, other):
        return Vector2(other / self.x, other / self.y)

    def __floordiv__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, (int, float)):
            return Vector2(self.x // other, self.y // other)
        elif isinstance(other, self.__class__):
            "Returns the inverse of the dot product of the vectors"
            return self.x // other.x + self.y // other.y
        return NotImplemented

    def __ifloordiv__(self, other):
        if isinstance(other, int):
            self.x //= other
            self.y //= other
            return self
        return NotImplemented

    def __rfloordiv__(self, other):
        return Vector2(other // self.x, other // self.y)

    def __str__(self, typ=None):
        if typ is None:
            typ = VectorType.cartesian
        if typ == VectorType.polar:
            return f"r={self.r:.2f}, θ={self.theta:.2f}"
        elif typ == VectorType.cartesian:
            return f"[{self.x:.5f}, {self.y:.5f}]"
        else:
            return f"r={self.r:.2f}, θ={self.theta:.2f}" + ' : ' f"[{self.x:.2f}, {self.y:.2f}]"

    def __repr__(self):
        return str(self)

    def str_polar(self):
        return f"r={self.r:.2f}, θ={self.theta:.2f}"

    def __getitem__(self, item):
        if item in ('x', 0):
            return self.x
        elif item in ('y', 1):
            return self.y
        elif item == 'theta':
            return self.theta
        elif item == 'r':
            return self.r
        else:
            raise IndexError()

    def __setitem__(self, key, value):
        if not isinstance(value, (int, float)):
            raise AttributeError(f"Expected type 'int' or 'float', got '{type(value)}' instead")
        if key in ('x', 0):
            self.x = value
        elif key in ('y', 1):
            self.y = value
        elif key == 'theta':
            self.theta = value
        elif key == 'r':
            self.r = value
        else:
            raise IndexError()

    def __eq__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2(other[0], other[1])
        if isinstance(other, self.__class__):
            return (self.x == other.x) and (self.y == other.y)
        return NotImplemented

    def __bool__(self):
        return bool(self.x and self.y)

    def __mod__(self, other):
        if isinstance(other, (float, int)):
            return Vector2(self.x % other, self.y % other)

    def modf(self):
        x_float, x_num = math.modf(self.x)
        y_float, y_num = math.modf(self.y)
        return Vector2(x_float, y_float), \
               Vector2(x_num, y_num)

    def min(self, other):
        other = Vector2(*other)
        return Vector2.Cartesian(
            min(self.x, other.x),
            min(self.y, other.y)
        )

    def max(self, other):
        other = Vector2(*other)
        return Vector2(
            max(self.x, other.x),
            max(self.y, other.y)
        )

    def magnitude_squared(self):
        return self.x * self.x + self.y * self.y

    def to_pos(self):
        return tuple(self.floor())

    def copy(self):
        return self.__class__(self.x, self.y)


class Scroller:  # tested
    SCROLL_DELAY = 20  # the high it is the slower it takes to scroll to the player location

    @dataclass
    class camera:
        
        x: Union[float, callable]
        y: Union[float, callable]
        angle: Union[float, callable]
        height: Union[float, callable]

        @staticmethod
        def attr_value(value):
            if callable(value):
                return value()
            return value

        def get_current(self):
            c = Scroller.camera(
                self.attr_value(self.x),
                self.attr_value(self.y),
                self.attr_value(self.angle),
                self.attr_value(self.height)
            )
            return c

    minimum_steps = camera()

    @classmethod
    def build_callable_values(cls, x, y, angle, height):
        camera_attributes = [x, y, angle, height]
        for idx , value in enumerate(camera_attributes):
            if isinstance(value, int):
                camera_attributes[idx] = lambda: value
            elif callable(value):
                camera_attributes[idx] = value  # a function which returns the focus point
            else:
                raise AttributeError(f"Invalid value {list(cls.camera.__dataclass_fields__)[idx]}")
        return cls.camera(*camera_attributes)

    def __init__(self, x, y, angle, height, starting_x=None, starting_y=None,
                 starting_angle=None, starting_height=None, delay=SCROLL_DELAY, debug=False):

        self.target_camera = self.build_callable_values(x, y, angle, height)
        self.current_camera = self.camera(starting_x or self.target_camera.x(),
                                          starting_y or self.target_camera.y(),
                                          starting_angle or self.target_camera.angle(),
                                          starting_height or self.target_camera.height())
        self.last_change = self.camera(0, 0, 0, 0)  # not necessary, makes movement smoother
        # (to make it constant the function just need to be pure)
        self.delay = delay

    def __str__(self):
        return str(self.current_camera)

    @property
    def current_position(self):
        return self.current_camera.x, self.current_camera.y

    @property
    def current_angle(self):
        return self.current_camera.angle

    @property
    def current_height(self):
        return self.current_camera.height

    def __set_abs_values(self, new_camera):
        """Sets the position without a smooth transition"""
        self.current_camera = new_camera

    def set_to(self, x, y, angle, height, smooth_move=False):
        """Sets the position of the scroller to position. For a smooth transition, pass smooth_move=True."""
        self.target_camera = self.build_callable_values(x, y, angle, height)
        if not smooth_move:  # for a smooth transition just wait
            self.__set_abs_values(self.target_camera)

    def update(self):
        """Updates the scroller, called each frame"""

        current_target = self.target_camera.get_current()
        for current_attribute, current_attribute_value in asdict(self.current_camera).items():

            target_attribute = current_target.__getattribute__(current_attribute)
            delta = target_attribute - current_attribute_value

            delta = max(abs(delta), ) * sign(delta)
            # if abs(delta < 3) and \
            #         (abs(delta) < abs(self.last_change.__getattribute__(current_attribute))):  # makes movement
            #     # smoother, finishes at once instead of getting this 0.00000001
            #     delta += sign(int(delta)) * Scroller.SCROLL_DELAY

            next_step = delta / Scroller.SCROLL_DELAY + current_attribute_value

            if (next_step - target_attribute) * (target_attribute - current_attribute_value) > 0: # too big
                next_step = current_attribute_value
            self.current_camera.__setattr__(current_attribute, next_step)
            self.last_change.__setattr__(current_attribute, delta)


def toggle(a, b, dont_specify=[-1]):
    dont_specify[0] += 1
    if dont_specify[0] % 2 == 0:
        return a
    return b


if __name__ == '__main__':
    vec = Vector2.Cartesian(2, 3)
    angle = 10
    matrix = RotationMatrix(angle)
    print(vec.rotated(angle), vec * matrix)
