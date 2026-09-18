from games.snake.scene import SnakeScene

GAMES = (
    {
        "id": "snake",
        "title": "SNAKE",
        "subtitle": "EAT GROW DONT CRASH",
        "enabled": True,
        "factory": SnakeScene,
    },
    {
        "id": "soon",
        "title": "MORE SOON",
        "subtitle": "NEXT GAME TBD",
        "enabled": False,
        "factory": None,
    },
)
