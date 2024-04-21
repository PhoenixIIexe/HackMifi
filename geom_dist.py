from typing import Tuple

from math import radians, sin, cos, sqrt, atan2


EPS = 1e-8


def eq(x, y):
    return abs(x - y) < EPS


def lt(x, y):
    return x + EPS < y


def lteq(x, y):
    return lt(x, y) or eq(x, y)


def qt(x, y):
    return x - EPS > y


def qteq(x, y):
    return qt(x, y) or eq(x, y)


class Point:
    def __init__(self, *args) -> None:
        if len(args) == 1:
            if isinstance(args[0], tuple):
                self.x = args[0][0]
                self.y = args[0][1]
        elif len(args) == 2:
            x, y = args
            if isinstance(x, int) and isinstance(y, int):
                self.x = x
                self.y = y
            if isinstance(x, Point) and isinstance(y, Point):
                self.x = y.x - x.x
                self.y = y.y - x.y

    def len2(self):
        return self.x**2 + self.y**2

    def len(self):
        return sqrt(self.len2())

    def dist(self, other):
        return sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def __mul__(self, other):
        return self.x * other.y - self.y * other.x

    def __xor__(self, other):
        return self.x * other.x + self.y * other.y


def point2vector(c: Tuple[float, float], d: Tuple[float, float], a: Tuple[float, float]) -> float:
    c = Point(c)
    d = Point(d)
    a = Point(a)
    res = min(a.dist(c), a.dist(d))

    cd = Point(c, d)
    ca = Point(c, a)
    dc = Point(d, c)
    da = Point(d, a)
    if qteq((cd ^ ca), 0) and qteq((dc ^ da), 0):
        res = abs(cd * ca) / cd.len()

    return res


def add_lat(lat: float, meters: float) -> float:
    meters_in_degrees = meters / 111000
    lat += meters_in_degrees
    return lat


def dist_points(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    lat1, lon1, *_ = point1
    lat2, lon2, *_ = point2

    R = 6371000

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) * sin(dlat / 2) + cos(lat1) * \
        cos(lat2) * sin(dlon / 2) * sin(dlon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance
