from enum import Enum
import math


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
    def __init__(self, angle):
        angle = math.radians(angle)
        self.m00 = math.cos(angle)
        self.m10 = -math.sin(angle)
        self.m01 = -self.m10
        self.m11 = self.m00

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2.Cartesian(self.m00 * other.x + self.m10 * other.y, self.m01 * other.x + self.m11 * other.y)
        return NotImplemented

    def __rmul__(self, other):
        return self * other

class Vector2(PrivateConstructor):
    def __init__(self, parm, vector_type):  # parm = (r, theta) or (x, y)
        if vector_type == VectorType.cartesian:
            self.x = parm[0]
            self.y = parm[1]
        elif vector_type == VectorType.polar:
            self.x = DegTrigo.cos(parm[1]) * parm[0]
            self.y = DegTrigo.sin(parm[1]) * parm[0]

    @property
    def r(self):
        return math.hypot(self.x, self.y)

    @r.setter
    def r(self, value):
        theta = self.theta
        self.x = DegTrigo.cos(theta) * value
        self.y = DegTrigo.sin(theta) * value

    @property
    def theta(self):
        return DegTrigo.atan1(self.x, self.y)

    @theta.setter
    def theta(self, value):
        r = self.r
        self.x = DegTrigo.cos(value) * r
        self.y = DegTrigo.sin(value) * r

    @property
    def values(self):
        return self.x, self.y

    @values.setter
    def values(self, value):
        self.x, self.y = value

    def magnitude(self):
        return abs(self.r)

    def square_magnitude(self):
        return self * self

    @classmethod
    def Cartesian(cls, x=0.0, y=0.0):
        return cls((x, y), VectorType.cartesian, key=cls._key)

    @classmethod
    def Point(cls, point):
        return cls((point[0], point[1]), VectorType.cartesian, key=cls._key)

    @classmethod
    def Polar(cls, r, theta):
        return cls((r, theta), VectorType.polar, key=cls._key)

    @classmethod
    def Zero(cls):
        return cls.Cartesian(0, 0)

    @classmethod
    def Copy(cls, vector):
        return cls.Cartesian(vector.x, vector.y)

    def copy(self):
        return Vector2.Copy(self)

    def reset(self):
        self.x = 0
        self.y = 0

    def rotate(self, angle):
        self.theta += angle

    def rotated(self, angle):
        new = self.copy()
        new.rotate(angle)
        return new

    def normalized(self):
        if not self:
            return Vector2.Zero()
        return Vector2.Cartesian(self.x / self.magnitude(), self.y / self.magnitude())

    def normalize(self):
        mag = self.magnitude()
        self.x /= mag
        self.y /= mag

    def sign(self):
        return Vector2.Cartesian(sign(self.x), sign(self.y))

    def normal(self):
        return Vector2.Cartesian(-self.y, self.x)

    def perpendicular(self):
        return self.normal()

    def tangent(self):
        return self.normal()

    def floor(self):
        if math.isnan(self.x):
            g = 5
        return Vector2.Cartesian(int(self.x), int(self.y))

    def set_values(self, x=None, y=None):
        self.x = x or self.x
        self.y = y or self.y

    def __round__(self, n=None):
        return Vector2.Cartesian(round(self.x, n), round(self.y, n))

    def __neg__(self):
        return Vector2.Cartesian(-self.x, -self.y)

    def __pos__(self):
        return Vector2.Cartesian(self.x, self.y)

    def __add__(self, other):  # + operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            return self.__class__.Cartesian(self.x + other.x, self.y + other.y)
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot add a scalar to a vector")
        return NotImplemented

    def __iadd__(self, other):  # += operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
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
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            return self.__class__.Cartesian(self.x - other.x, self.y - other.y)
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot subtract a scalar from a vector")
        return NotImplemented

    def __isub__(self, other):  # -= operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
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
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (int, float)):
            return Vector2.Cartesian(self.x * other, self.y * other)
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
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (int, float)):
            return self.Cartesian(self.x / other, self.y / other)
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
        return Vector2.Cartesian(other / self.x, other / self.y)

    def __floordiv__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (int, float)):
            self.Cartesian(self.x // other, self.y // other)
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
        return Vector2.Cartesian(other // self.x, other // self.y)

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
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            return (self.x == other.x) and (self.y == other.y)
        return NotImplemented

    def __bool__(self):
        return bool(round(self.r, 5))

    def __pow__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        """returns the cross product of the vector self and other"""
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(other * self.y, -other * self.x)
        elif isinstance(other, Vector2):
            return self.x * other.y - self.y * other.x

    def __rpow__(self, other):
        """returns the cross product of other and the vector self"""
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(-other * self.y, other * self.x)
        elif isinstance(other, Vector2):
            return other ** self

    def __mod__(self, other):
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(self.x % other, self.y % other)

    def __abs__(self):
        return self.magnitude()

    def modf(self):
        x_float, x_num = math.modf(self.x)
        y_float, y_num = math.modf(self.y)
        return Vector2.Cartesian(x_float, y_float), \
               Vector2.Cartesian(x_num, y_num)

    def min(self, other):
        other = Vector2.Point(other)
        return Vector2.Cartesian(
            min(self.x, other.x),
            min(self.y, other.y)
        )

    def max(self, other):
        other = Vector2.Point(other)
        return Vector2.Cartesian(
            max(self.x, other.x),
            max(self.y, other.y)
        )

    def to_pos(self):
        return tuple(self.floor())

    def modified(self, x=None, y=None):
        new = self.copy()
        new.set_values(x, y)
        return new


if __name__ == '__main__':
    vec = Vector2.Cartesian(2, 3)
    angle = 10
    matrix = RotationMatrix(angle)
    print(vec.rotated(angle),  vec * matrix)