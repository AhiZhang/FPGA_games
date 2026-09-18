from games.breakout.scene import BreakoutScene
from games.flappy.scene import FlappyScene
from games.game2048.scene import Game2048Scene
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
    {
        "id": "flappy",
        "title": "FLAPPY",
        "subtitle": "FLAP THROUGH PIPES",
        "enabled": True,
        "factory": FlappyScene,
    },
    {
        "id": "g2048",
        "title": "2048",
        "subtitle": "SLIDE AND MERGE",
        "enabled": True,
        "factory": Game2048Scene,
    },
)
