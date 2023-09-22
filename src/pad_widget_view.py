import numpy as np
import OpenGL.GL as GL
import PIL.Image as Image

from pad_model import PadModel, PanelModel, SensorModel, LEDModel


class TexturePainter:
    """Generic painter to map texture images to quads."""

    @staticmethod
    def load(path: str) -> tuple[bytes, int, int]:
        image = Image.open(path)
        conv_image = image.convert("RGBA")
        image_data = conv_image.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
        image.close()
        return (image_data, image.width, image.height)

    @staticmethod
    def set_data(image_data: bytes, width: int, height: int) -> int:
        texture_id = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR
        )
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, width, height, 0,
            GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, image_data
        )
        return texture_id

    @staticmethod
    def draw(id: int, x: int, y: int, size: int, alpha: float) -> None:
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, id)
        GL.glColor4f(1.0, 1.0, 1.0, alpha)
        GL.glBegin(GL.GL_QUADS)
        for cx, cy in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            GL.glTexCoord2f(cx, cy)
            GL.glVertex2f(x + size * cx, y + size * cy)
        GL.glEnd()
        GL.glDisable(GL.GL_TEXTURE_2D)


class RectPainter:
    """Painter for a rectangle with a colour gradient."""

    MID_GRAY = (100, 100, 100, 255)
    LIGHT_GRAY = (200, 200, 200, 255)
    LIGHT_RED = (150, 0, 0, 175)
    DARK_RED = (50, 0, 0, 175)
    LIGHT_GREEN = (0, 200, 0, 255)
    DARK_GREEN = (0, 100, 0, 255)
    LIGHT_BLUE = (0, 0, 200, 255)
    DARK_BLUE = (0, 0, 100, 255)

    @staticmethod
    def draw(
        x: int, y: int, w: int, h: int,
        start_col: tuple[int, int, int, int] | list[int],
        end_col: tuple[int, int, int, int] | list[int] | None = None
    ) -> None:
        GL.glBegin(GL.GL_QUADS)
        if len(start_col) == 3:
            GL.glColor3ub(*start_col)
        else:
            GL.glColor4ub(*start_col)
        GL.glVertex2f(x, y)
        GL.glVertex2f(x + w, y)
        if end_col is not None:
            if len(end_col) == 3:
                GL.glColor3ub(*end_col)
            elif len(end_col) == 4:
                GL.glColor4ub(*end_col)
        GL.glVertex2f(x + w, y + h)
        GL.glVertex2f(x, y + h)
        GL.glEnd()


class PanelPainter:
    """Painter for an arrow panels sensor and LED values."""

    SIZE = 280
    SEN_WIDTH = 15
    SEN_HEIGHT = 100
    SEN_SPACE = 5
    LED_GRID_SIZE = 180
    LED_SPACE = 2
    LED_SIZE = int(LED_GRID_SIZE / 12 - LED_SPACE)
    RECT_PAD = 5

    def __init__(self, panel: PanelModel):
        self._offset = (
            panel.coord[0] * self.SIZE,
            panel.coord[1] * self.SIZE
        )
        self._l_offset = (
            int(self._offset[0] + ((self.SIZE - self.LED_GRID_SIZE) / 2)),
            int(self._offset[1] + ((self.SIZE - self.LED_GRID_SIZE) / 2))
        )
        self._panel = panel
        self._threshold_rects = {}

    def draw(self) -> None:
        for sensor in self._panel.sensors:
            self.draw_sensor(sensor)
        for led in self._panel.leds:
            self.draw_led(led)

    def draw_led(self, led: LEDModel) -> None:
        x = self._l_offset[0] + (self.LED_SIZE + self.LED_SPACE) * led.coord[0]
        y = self._l_offset[1] + (self.LED_SIZE + self.LED_SPACE) * led.coord[1]
        RectPainter.draw(
            x, y, self.LED_SIZE, self.LED_SIZE, led.colour
        )

    def draw_sensor(self, sensor: SensorModel) -> None:
        if (sensor.coord[0] == 0):
            x = self._offset[0] + self.SEN_SPACE
        else:
            x = self._offset[0] + self.SIZE - self.SEN_WIDTH - self.SEN_SPACE
        if (sensor.coord[1] == 0):
            y = self._offset[1] + self.SIZE - self.SEN_HEIGHT - self.SEN_SPACE
        else:
            y = self._offset[1] + self.SEN_SPACE
        if sensor.active:
            s_col = RectPainter.LIGHT_GREEN
            e_col = RectPainter.DARK_GREEN
        else:
            s_col = RectPainter.LIGHT_BLUE
            e_col = RectPainter.DARK_BLUE
        RectPainter.draw(
            x, y, self.SEN_WIDTH, self.SEN_HEIGHT,
            RectPainter.LIGHT_GRAY, RectPainter.MID_GRAY
        )
        RectPainter.draw(
            x, y, self.SEN_WIDTH, sensor.delta_value, s_col, e_col
        )
        RectPainter.draw(
            x, y + sensor.off_threshold, self.SEN_WIDTH,
            sensor.threshold - sensor.off_threshold,
            RectPainter.LIGHT_RED, RectPainter.DARK_RED
        )
        self.store_rect(sensor, x, y)

    @property
    def threshold_rects(
        self
    ) -> dict[tuple[int, int], dict[tuple[int, int], list[int]]]:
        return self._threshold_rects

    def store_rect(self, sensor: SensorModel, x: int, y: int) -> None:
        pc = self._panel.coord
        sc = sensor.coord
        x1 = np.maximum(x - self.RECT_PAD, 0)
        y1 = np.maximum(
            y + sensor.threshold - sensor.hysteresis - self.RECT_PAD, 0
        )
        x2 = np.maximum(x + self.SEN_WIDTH + self.RECT_PAD, 0)
        y2 = np.maximum(y + sensor.threshold + self.RECT_PAD, 0)
        if pc not in self._threshold_rects:
            self._threshold_rects[pc] = {}
        self._threshold_rects[pc][sc] = [x1, y1, x2, y2]


class PadPainter:
    """Painter for a dance pad."""

    SIZE = PanelPainter.SIZE * 3

    def __init__(self, model: PadModel):
        gloss = TexturePainter.load("../assets/gloss-texture.jpg")
        self.gloss_id = TexturePainter.set_data(*gloss)
        metal = TexturePainter.load("../assets/brushed-metal-texture.jpg")
        self.metal_id = TexturePainter.set_data(*metal)
        self.model = model
        self.painters = [PanelPainter(panel) for panel in model.panels]

    def draw_base(self) -> None:
        size = PanelPainter.SIZE
        coords = [(x * size, y * size) for x, y in self.model.BLANK_COORDS]
        for x, y in coords:
            TexturePainter.draw(self.metal_id, x, y, size, 0.5)
        TexturePainter.draw(self.gloss_id, 0, 0, self.SIZE, 0.2)

    def draw_panel_data(self) -> None:
        for painter in self.painters:
            painter.draw()


class PadWidgetView:
    """View class encapsulating GL framework for dance pad painters."""

    SIZE = PadPainter.SIZE

    def init_painting(self, model: PadModel) -> None:
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glOrtho(0, self.SIZE, 0, self.SIZE, -1, 1)
        self.painter = PadPainter(model)

    def handle_resize_event(self, w: int, h: int) -> None:
        GL.glViewport(0, 0, w, h)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, w, 0, h, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        self.painter.draw_base()

    def draw_widget(self) -> None:
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.painter.draw_panel_data()
        self.painter.draw_base()

    @property
    def threshold_rects(
        self
    ) -> dict[tuple[int, int], dict[tuple[int, int], list[int]]]:
        rects = {}
        for panel_painter in self.painter.painters:
            rects.update(panel_painter.threshold_rects)
        return rects

    def mouse_in_threshold_rect(
        self, x: int, y: int
    ) -> tuple[tuple[int, int], tuple[int, int]] | None:
        for panel_coord, sensor_dict in self.threshold_rects.items():
            for sensor_coord, [x1, y1, x2, y2] in sensor_dict.items():
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return panel_coord, sensor_coord
        return None