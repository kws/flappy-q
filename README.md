# flappy-q

A tiny deterministic Flappy Bird-style environment for reinforcement-learning tutorials.

The core game advances one tick at a time. Each tick accepts one action, `flap` or
`no flap`, and returns the observable game state:

- `dy`: bird vertical offset from the next pipe opening center
- `vy`: bird vertical velocity
- `dx`: horizontal distance from the bird's trailing edge to the active pipe's trailing edge
- `bird_y`: absolute bird vertical position for edge detection

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

print(state.dy, state.vy, state.dx, state.bird_y)
print(game.alive, game.frames, game.obstacles_passed)
```

Rendering supports either a `tkinter.Canvas`-compatible object or an
`ipycanvas.Canvas` in notebooks. `FlappyGame.render()` draws only the game
world, so reinforcement-learning loops can choose their own metrics overlay:

```python
game.render(canvas)
```

Jupyter example:

```python
!pip install ipycanvas

from IPython.display import display
from ipycanvas import Canvas, hold_canvas

from flappy_q import FlappyGame

game = FlappyGame(seed=123)
canvas = Canvas(width=game.width, height=game.height)
display(canvas)

episode = 0
q_table = {}

with hold_canvas(canvas):
    canvas.clear()
    game.render(canvas)
    canvas.fill_style = "#17324d"
    canvas.font = "16px sans-serif"
    canvas.fill_text(f"Episode: {episode}", 10, 20)
    canvas.fill_text(f"Score: {game.obstacles_passed}", 10, 40)
    canvas.fill_text(f"Q-Table Size: {len(q_table)}", 10, 60)
```

Colab example:

```python
!pip install ipycanvas
!pip install git+https://github.com/kws/flappy-q.git

from google.colab import output
output.enable_custom_widget_manager()

from IPython.display import display
from ipycanvas import Canvas, hold_canvas

from flappy_q import FlappyGame

game = FlappyGame(seed=123)
canvas = Canvas(width=game.width, height=game.height)
display(canvas)

episode = 0
q_table = {}

with hold_canvas(canvas):
    canvas.clear()
    game.render(canvas)
    canvas.fill_style = "#17324d"
    canvas.font = "16px sans-serif"
    canvas.fill_text(f"Episode: {episode}", 10, 20)
    canvas.fill_text(f"Score: {game.obstacles_passed}", 10, 40)
    canvas.fill_text(f"Q-Table Size: {len(q_table)}", 10, 60)
```

The game is deterministic for a given seed and input sequence.

## Tests

```bash
uv run pytest
```
