from PyQt5.QtCore import QRectF, QPointF
import math
from multipledispatch import *

# Returns mantissa and exponent for <value> in normalized scientific notation


def normalized(value: float):
    if value == 0:
        return 0, 0

    exponent = math.floor(math.log10(abs(value)))
    mantissa = value / 10 ** exponent
    return mantissa, exponent


@dispatch(float, float, float, float, float, float)
def collision(l: float, r: float, b: float, t: float, x: float, y: float):
    return l <= x <= r and b <= y <= t


@dispatch(float, float, float, float, float, float, float, float)
def collision(l1, r1, b1, t1, l2, r2, b2, t2):
    return l1 < r2 and r1 > l2 and b1 < t2 and t1 > b2