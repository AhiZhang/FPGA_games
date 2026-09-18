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
        "id": "soon",
        "title": "MORE SOON",
        "subtitle": "NEXT GAME TBD",
        "enabled": False,
        "factory": None,
    },
)
