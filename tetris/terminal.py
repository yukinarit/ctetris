import abc
import copy
import enum
import random
import os
from typing import List, Tuple, Dict, Callable
from termbox import (DEFAULT, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN,  # type: ignore
        WHITE, KEY_ESC, KEY_ARROW_UP, KEY_ARROW_DOWN, KEY_ARROW_LEFT,
        KEY_ARROW_RIGHT, Termbox)
from .logger import create_logger
from .exceptions import Exit


basedir = os.path.abspath(os.path.dirname(__file__))

DEFAULT_SQUARE = 0x0020

DEFAULT_COLOR = DEFAULT

CELLX = 2

CELLY = 1

logger = create_logger(__name__)


class Color(enum.IntEnum):
    """
    Color enum representing terminal colors.
    """
    Default = DEFAULT
    Black = BLACK
    Red = RED
    Green = GREEN
    Yellow = YELLOW
    Blue = BLUE
    Magenta = MAGENTA
    Cyan = CYAN
    White = WHITE
    Random = 0x09

    @classmethod
    def random_color(cls):
        return random.randint(cls.Default, cls.Random - 1)


class Shape(enum.Enum):
    """
    Shape enum.
    """
    Square = ord(' ')
    Bullet = ord('•')
    Star = ord('*')
    Default = Square


class Vector2:
    """
    Vector 2D class.
    """
    def __init__(self, x: int=None, y: int=None) -> None:
        self.x: int = x
        self.y: int = y

    def __add__(self, other) -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other) -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __repr__(self) -> str:
        return '<Vector2(x={},y={})>'.format(
            self.x, self.y)

    def __str__(self) -> str:
        return '(x={},y={})'.format(
            self.x, self.y)


class Dir(enum.Enum):
    Left = Vector2(-2, 0)
    Right = Vector2(2, 0)
    Up = Vector2(0, -1)
    Down = Vector2(0, 1)


class Rect:
    """
    Rectangle.
    """
    def __init__(self, x1: int=0, y1: int=0, x2: int=0, y2: int=0) -> None:
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2

    @property
    def lb(self) -> Vector2:
        """
        Left bottom
        """
        return Vector2(self.x1, self.y1)

    @property
    def lt(self) -> Vector2:
        """
        Left top
        """
        return Vector2(self.x1, self.y2)

    @property
    def rb(self) -> Vector2:
        """
        Right bottom
        """
        return Vector2(self.x2, self.y1)

    @property
    def rt(self) -> Vector2:
        """
        Right top
        """
        return Vector2(self.x2, self.y2)

    def get_pos(self) -> Vector2:
        return self.get_center()

    def get_center(self) -> Vector2:
        return Vector2(self.x1 + (self.x2 - self.x1),
                       self.y1 + (self.y2 - self.y1))

    def get_width(self) -> int:
        return abs(self.x2 - self.x1) + 1

    def get_height(self) -> int:
        return abs(self.y2 - self.y1) + 1

    def __repr__(self) -> str:
        return '[Rect] lb={},lt={},rt={},rb={},w={},h={}'.format(
            str(self.lb), str(self.lt), str(self.rt),
            str(self.rb), self.get_width(), self.get_height())


class Cell:
    """
    Cell object.
    """
    def __init__(self, x: int=None, y: int=None, fg: Color=None,
                 bg: Color=None, c: Shape=None) -> None:
        self.c: Shape = c or Shape.Default.value
        self.x: int = x
        self.y: int = y
        self.fg: Color = fg or Color.Default
        self.bg: Color = bg or Color.Default


class Size(enum.IntEnum):
    w1xh1 = 1
    w2xh1 = 1
    w3xh3 = 3
    w5xh5 = 5
    w7xh7 = 7
    w9xh9 = 9
    w11xh11 = 11
    w13xh13 = 13
    w15xh15 = 15
    w17xh17 = 17
    w19xh19 = 19
    MinSize = w1xh1
    MaxSize = w19xh19


def render_objects(tm: 'Terminal', objects: List['Renderable']):
    """
    Render objects in terminal.
    """
    if not tm:
        raise RuntimeError('Null terminal')
    if not tm.tb:
        raise RuntimeError('Null termbox')

    for o in objects:
        if not o:
            continue
        o.render(tm)


def render_cells(tm: 'Terminal', cells: List[Cell]):
    """
    Render cells in terminal.
    """
    if not tm.tb:
        raise RuntimeError('Null termbox')
    for cell in cells:
        tm.tb.change_cell(cell.x, cell.y, cell.c, cell.fg, cell.bg)


class Renderable:
    """
    Renderable object base.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, x: int=None, y: int=None) -> None:
        self.pos: Vector2 = Vector2(x, y)
        self.prev_pos: Vector2 = None
        self.fg: Color = None
        self.bg: Color = None
        self.prev_direction: Dir = None
        self.direction: Dir = None

    def render(self, tm: 'Terminal'=None, dx: int=0, dy: int=0,
               check_intersect: bool=True):
        """
        Render object.
        """
        pos = self.get_pos()
        if not pos:
            logger.debug('Null pos.')
            return
        fg, bg = self.get_color()
        rect = self.get_rect()
        left = rect.x1
        right = rect.x2
        bottom = rect.y1
        top = rect.y2

        """
        if self.direction:
            trajectory = self.make_trajectory(rect=rect)
            #logger.debug('dir:{}, trajectory:{}'.format(
                          self.direction, str(trajectory)))
        else:
            trajectory = rect
        if check_intersect and tm.map.intersectd_with(rect=trajectory):
            self.pos = self.prev_pos or self.pos
            self.render(tm, dx, dy, check_intersect=False)
        """

        cells = []
        for y in range(bottom, top+1):
            for x in range(left, right+1):
                cell = Cell(x=x-dx, y=y-dy, fg=fg, bg=bg, c=self.get_shape())
                cells.append(cell)
        if tm.debug:
            x = right + 1
            y = bottom + 1
            coord = "xy({},{}),w={},y={},rect={}".format(
                x, y, self.get_width(), self.get_height(), rect)
            for c in coord:
                cell = Cell(x=x-dx, y=y-dy, fg=fg, c=Shape(ord(c)))
                cells.append(cell)
                x += 1

        render_cells(tm, cells)

    def move(self, direction: Dir=None, pos: Vector2=None):
        self.prev_direction = self.direction
        if direction:
            self.direction = direction
            self.prev_pos = copy.deepcopy(self.pos)
            self.pos += direction.value
            logger.debug('{} {} {} {}'.format(direction, direction.name,
                         direction.value, self.pos))
        if pos:
            self.prev_pos = copy.deepcopy(self.pos)
            self.pos = pos

    def get_pos(self) -> Vector2:
        return self.pos

    def get_rect(self) -> Rect:
        pos = self.get_pos()
        size = self.get_size()
        diameter = Vector2(x=int((size - 1) / 2), y=int((size - 1) / 2))

        left = pos.x - diameter.x
        right = pos.x + diameter.x
        bottom = pos.y - diameter.y
        top = pos.y + diameter.y
        return Rect(x1=left, y1=bottom, x2=right, y2=top)

    def make_trajectory(self, rect=None):
        rect = rect or self.get_rect()
        if self.direction == Dir.Left:
            trajectory = Rect(
                x1=rect.x1,
                y1=rect.y1,
                x2=rect.x2-Dir.Left.value.x,
                y2=rect.y2,
            )
        elif self.direction == Dir.Right:
            trajectory = Rect(
                x1=rect.x1-Dir.Right.value.x,
                y1=rect.y1,
                x2=rect.x2,
                y2=rect.y2,
            )
        elif self.direction == Dir.Up:
            trajectory = Rect(
                x1=rect.x1,
                y1=rect.y1-Dir.Up.value.y,
                x2=rect.x2,
                y2=rect.y2,
            )
        elif self.direction == Dir.Down:
            trajectory = Rect(
                x1=rect.x1,
                y1=rect.y1,
                x2=rect.x2,
                y2=rect.y2-Dir.Down.value.y,
            )
        else:
            trajectory = rect
        return trajectory

    @abc.abstractmethod
    def get_size(self) -> Size:
        return Size.w1xh1

    @abc.abstractmethod
    def get_width(self) -> int:
        pass

    @abc.abstractmethod
    def get_height(self) -> int:
        pass

    def set_color(self, fg: Color, bg: Color):
        """
        Set foreground, background color.
        """
        self.fg = fg
        self.bg = bg
        if self.fg == Color.Random:
            self.fg = Color.random_color()
        if self.bg == Color.Random:
            self.bg = Color.random_color()

    def get_color(self) -> Tuple[Color, Color]:
        """
        Get foreground, background color.
        """
        return self.fg, self.bg

    @abc.abstractmethod
    def get_shape(self) -> Shape:
        """
        Get shape. Needs to be overridden.
        """
        return None


class MouseKey(enum.Enum):
    ESC = KEY_ESC
    Left = KEY_ARROW_LEFT
    Right = KEY_ARROW_RIGHT
    Up = KEY_ARROW_UP
    Down = KEY_ARROW_DOWN
    a = 'a'
    b = 'b'
    c = 'c'
    d = 'd'
    e = 'e'
    f = 'f'
    g = 'g'
    h = 'h'
    i = 'i'
    j = 'j'
    k = 'k'
    l = 'l'
    m = 'm'
    n = 'n'
    o = 'o'
    p = 'p'
    q = 'q'
    r = 'r'
    s = 's'
    t = 't'
    u = 'u'
    v = 'v'
    w = 'w'
    x = 'x'
    y = 'y'
    z = 'z'


class Terminal:
    """
    Terminal class.
    """
    TermboxCls = Termbox

    def __init__(self, debug=False) -> None:
        self.tb = self.TermboxCls()
        logger.debug("init {}".format(self.tb))
        self.debug = debug
        self._keydown_handlers: Dict[int, Callable] = {}
        self._on_shutdown = None

    def __enter__(self):
        logger.debug("entering {}".format(self.tb))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("exiting {}".format(self.tb))
        self.close()

    def __del__(self):
        logger.debug("deleting {}".format(self.tb))

    def close(self):
        if self.tb:
            self.tb.close()
            self.tb = None

    def set_keydown_handler(self, keys, cb):
        if isinstance(keys, list):
            for key in keys:
                self._keydown_handlers.update({key.value: cb})
        else:
            key = keys
            self._keydown_handlers.update({key.value: cb})

    def get_keydown_handler(self, keyvalue):
        return self._keydown_handlers.get(keyvalue)

    @property
    def on_shutdown(self):
        return self._on_shutdown

    @on_shutdown.setter
    def on_shutdown(self, f):
        self._on_shutdown = f

    @property
    def width(self):
        return self.tb.width()

    @property
    def height(self):
        return self.tb.height()

    @property
    def boundary(self) -> Rect:
        return Rect(x1=0, y1=0, x2=self.width, y2=self.height)

    def center(self):
        x = int(self.width / 2)
        y = int(self.height / 2)
        return Vector2(x, y)

    def clear(self):
        """
        Clear the console
        """
        self.tb.clear()

    def update(self, now, *objects):
        """
        Render any renderable object on the console.
        """
        self.clear()
        self.peek_key_event()
        render_objects(self, objects)
        self.tb.present()

    def peek_key_event(self):
        try:
            if not self.tb:
                raise RuntimeError('Null termbox')

            type_, uch, key, mod, w, h, x, y = self.tb.peek_event()
            logger.debug('type:{type},uch={uch},key={key},mod={mod},'
                         'w={w},h={h},x={x},y={y}'.
                         format(type=type_, uch=uch, key=key, mod=mod,
                                w=w, h=h, x=x, y=y))
            if key is not None:
                cb = self.get_keydown_handler(key)
                if cb:
                    cb(key)
                if key == KEY_ESC:
                    self.close()
                    if self.on_shutdown:
                        self.on_shutdown()
                    raise Exit()
            if uch:
                cb = self.get_keydown_handler(uch)
                if cb:
                    cb(key)

        except TypeError as e:
            pass

        except Exception as e:
            print(e)
            raise
