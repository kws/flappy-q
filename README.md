# flappy-q

A tiny deterministic Flappy Bird-style environment for reinforcement-learning tutorials.

The core game advances one tick at a time. Each tick accepts one action, `flap` or
`no flap`, and returns the observable game state:

- `dy`: bird vertical offset from the next pipe opening center
- `vy`: bird vertical velocity
- `dx`: horizontal distance from the bird to the active pipe's trailing edge

## Install and run

```bash
uv sync
uv run flappy-q --seed 123
```

Controls in the standalone app:

- Space, Up, or W: flap
- R: reset

The module entry point is also available:

```bash
uv run python -m flappy_q --seed 123
```

## Core API

```python
from flappy_q import FlappyGame

game = FlappyGame(seed=123)

state = game.reset()
state = game.tick(flap=True)
state = game.tick(flap=False)

print(state.dy, state.vy, state.dx)
print(game.alive, game.frames, game.obstacles_passed)
```

Rendering supports either a `tkinter.Canvas`-compatible object or an
`ipycanvas.Canvas` in notebooks:

```python
game.render(canvas)
```

Notebook example:

```python
from IPython.display import display
from ipycanvas import Canvas

from flappy_q import FlappyGame

game = FlappyGame(seed=123)
canvas = Canvas(width=game.width, height=game.height)
display(canvas)

game.render(canvas)
```

The game is deterministic for a given seed and input sequence.

## Tests

```bash
uv run pytest
```
