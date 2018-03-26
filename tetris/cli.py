import sys
import traceback
from .logging import setup_logger, Level
from .terminal import logger as term_logger
from .game import Game, ITetrimino, OTetrimino, STetrimino, Exit, \
    logger as game_logger



def run():
    rv = 1
    setup_logger(term_logger, level=Level.DEBUG, file='tetris.log', color=True)
    setup_logger(game_logger, level=Level.DEBUG, file='tetris.log', color=True)

    try:
        with Game() as game:
            game.add(ITetrimino(x=10, y=10))
            game.add(OTetrimino(x=20, y=20))
            game.add(STetrimino(x=10, y=14))
            game.run()

    except Exit as e:
        rv = e.code

    except Exception as e:
        print(e)
        traceback.print_exc()
        sys.exit(rv)
