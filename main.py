from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
import random

# Размеры поля
COLS, ROWS = 10, 20
TILE_SIZE = 40

# Фигуры (координаты блоков)
SHAPES = {
    'I': [[1, 0], [1, 1], [1, 2], [1, 3]],
    'O': [[0, 0], [0, 1], [1, 0], [1, 1]],
    'T': [[1, 0], [0, 1], [1, 1], [2, 1]],
    'S': [[1, 0], [2, 0], [0, 1], [1, 1]],
    'Z': [[0, 0], [1, 0], [1, 1], [2, 1]],
    'J': [[0, 0], [0, 1], [1, 1], [2, 1]],
    'L': [[2, 0], [0, 1], [1, 1], [2, 1]],
}

COLORS = [(0,1,1), (1,1,0), (0.5,0,0.5), (0,1,0), (1,0,0), (0,0,1), (1,0.5,0)]

class TetrisGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.spawn_piece()
        Clock.schedule_interval(self.update, 0.5)

    def spawn_piece(self):
        name = random.choice(list(SHAPES.keys()))
        self.cur_piece = [list(p) for p in SHAPES[name]]
        self.cur_color = COLORS[list(SHAPES.keys()).index(name)]
        self.piece_pos = [COLS // 2 - 1, 0]
        
        if self.check_collision(self.piece_pos, self.cur_piece):
            self.__init__() # Рестарт при проигрыше

    def check_collision(self, pos, piece):
        for px, py in piece:
            x, y = pos[0] + px, pos[1] + py
            if x < 0 or x >= COLS or y >= ROWS or (y >= 0 and self.board[y][x]):
                return True
        return False

    def freeze_piece(self):
        for px, py in self.cur_piece:
            x, y = self.piece_pos[0] + px, self.piece_pos[1] + py
            if y >= 0:
                self.board[y][x] = self.cur_color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(v is None for v in row)]
        lines_cleared = ROWS - len(new_board)
        for _ in range(lines_cleared):
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board

    def rotate_piece(self):
        # Поворот матрицы на 90 градусов
        rotated = [[-p[1], p[0]] for p in self.cur_piece]
        if not self.check_collision(self.piece_pos, rotated):
            self.cur_piece = rotated

    def update(self, dt):
        new_pos = [self.piece_pos[0], self.piece_pos[1] + 1]
        if not self.check_collision(new_pos, self.cur_piece):
            self.piece_pos = new_pos
        else:
            self.freeze_piece()
        self.draw()

    def on_touch_down(self, touch):
        if touch.y < self.height / 3: # Нижняя часть экрана - поворот
            self.rotate_piece()
        elif touch.x < self.width / 2: # Лево
            new_pos = [self.piece_pos[0] - 1, self.piece_pos[1]]
            if not self.check_collision(new_pos, self.cur_piece): self.piece_pos = new_pos
        else: # Право
            new_pos = [self.piece_pos[0] + 1, self.piece_pos[1]]
            if not self.check_collision(new_pos, self.cur_piece): self.piece_pos = new_pos
        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # Рисуем застывшие блоки
            for y, row in enumerate(self.board):
                for x, color in enumerate(row):
                    if color:
                        Color(*color)
                        Rectangle(pos=(x*TILE_SIZE, self.height - (y+1)*TILE_SIZE), size=(TILE_SIZE-1, TILE_SIZE-1))
            
            # Рисуем текущую фигуру
            Color(*self.cur_color)
            for px, py in self.cur_piece:
                x, y = self.piece_pos[0] + px, self.piece_pos[1] + py
                Rectangle(pos=(x*TILE_SIZE, self.height - (y+1)*TILE_SIZE), size=(TILE_SIZE-1, TILE_SIZE-1))

class TetrisApp(App):
    def build(self):
        return TetrisGame()

if __name__ == '__main__':
    TetrisApp().run()
