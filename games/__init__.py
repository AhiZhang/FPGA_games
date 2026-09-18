from games.breakout.scene import BreakoutScene
from games.snake.scene import SnakeScene
from games.tetris.scene import TetrisScene

GAMES = (
    {
        "id": "snake",
        "title": "SNAKE",
        "subtitle": "EAT GROW DONT CRASH",
        "enabled": True,
        "factory": SnakeScene,
    },
    {
        "id": "tetris",
        "title": "TETRIS",
        "subtitle": "STACK AND CLEAR",
        "enabled": True,
        "factory": TetrisScene,
    },
    {
        "id": "breakout",
        "title": "BREAKOUT",
        "subtitle": "HIT ALL THE BRICKS",
        "enabled": True,
        "factory": BreakoutScene,
    },
)
