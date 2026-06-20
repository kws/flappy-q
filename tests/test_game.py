from __future__ import annotations

import pytest

from flappy_q import FlappyGame, GameState


def test_same_seed_and_inputs_produce_same_states() -> None:
    inputs = [False, False, True, False, True, False, False, False]
    first = FlappyGame(seed=123)
    second = FlappyGame(seed=123)

    first_states = [first.tick(flap) for flap in inputs]
    second_states = [second.tick(flap) for flap in inputs]

    assert first_states == second_states


def test_different_seeds_produce_different_initial_maps() -> None:
    first = FlappyGame(seed=1)
    second = FlappyGame(seed=2)

    assert first.state != second.state


def test_tick_returns_state_only() -> None:
    game = FlappyGame(seed=7)

    state = game.tick(False)

    assert isinstance(state, GameState)


def test_flap_changes_velocity_upward() -> None:
    game = FlappyGame(seed=123)
    no_flap = game.tick(False)

    game.reset()
    flap = game.tick(True)

    assert no_flap.vy == pytest.approx(game.gravity)
    assert flap.vy < 0
    assert flap.vy < no_flap.vy


def test_no_flap_applies_gravity_and_scrolls_pipe() -> None:
    game = FlappyGame(seed=123)
    initial = game.state

    state = game.tick(False)

    assert state.vy == pytest.approx(game.gravity)
    assert state.dx == pytest.approx(initial.dx - game.scroll_speed)


def test_dx_tracks_trailing_edge_until_pipe_is_cleared() -> None:
    game = FlappyGame(
        seed=10,
        width=320,
        bird_x=80,
        gravity=0,
        scroll_speed=80,
        pipe_gap=300,
    )

    for _ in range(3):
        state = game.tick(False)

    assert game.alive
    assert game.score == 1
    assert state.dx == pytest.approx(-8)
    assert state.dx > -game.bird_radius


def test_reset_without_seed_replays_same_map() -> None:
    game = FlappyGame(seed=42)
    initial = game.state
    for _ in range(5):
        game.tick(False)

    reset_state = game.reset()

    assert reset_state == initial
    assert game.score == 0
    assert game.ticks == 0
    assert game.alive


def test_collision_ends_run() -> None:
    game = FlappyGame(seed=123)

    for _ in range(200):
        game.tick(False)
        if not game.alive:
            break

    assert not game.alive


def test_dead_game_does_not_advance_until_reset() -> None:
    game = FlappyGame(seed=123)
    while game.alive:
        game.tick(False)

    ticks = game.ticks
    state = game.state

    assert game.tick(True) == state
    assert game.ticks == ticks


def test_passing_pipe_increments_score() -> None:
    game = FlappyGame(
        seed=10,
        width=320,
        height=480,
        bird_x=80,
        gravity=0,
        scroll_speed=120,
        pipe_gap=300,
        pipe_spacing=120,
    )

    for _ in range(3):
        game.tick(False)

    assert game.alive
    assert game.score >= 1


def test_frames_and_obstacles_passed_are_readable_separately() -> None:
    game = FlappyGame(
        seed=10,
        width=320,
        height=480,
        bird_x=80,
        gravity=0,
        scroll_speed=120,
        pipe_gap=300,
        pipe_spacing=120,
    )

    for _ in range(3):
        game.tick(False)

    assert game.frames == 3
    assert game.ticks == game.frames
    assert game.obstacles_passed == 2
    assert game.score == game.obstacles_passed


class FakeCanvas:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def configure(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("configure", args, kwargs))

    def delete(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("delete", args, kwargs))

    def create_rectangle(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("create_rectangle", args, kwargs))

    def create_oval(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("create_oval", args, kwargs))

    def create_text(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("create_text", args, kwargs))


class FakeIpyCanvas:
    def __init__(self) -> None:
        self.width = 0
        self.height = 0
        self.fill_style = ""
        self.stroke_style = ""
        self.line_width = 1
        self.font = ""
        self.text_align = ""
        self.text_baseline = ""
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def save(self) -> None:
        self.calls.append(("save", (), {}))

    def restore(self) -> None:
        self.calls.append(("restore", (), {}))

    def clear(self) -> None:
        self.calls.append(("clear", (), {}))

    def fill_rect(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("fill_rect", args, kwargs))

    def stroke_rect(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("stroke_rect", args, kwargs))

    def fill_circle(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("fill_circle", args, kwargs))

    def stroke_circle(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("stroke_circle", args, kwargs))

    def fill_text(self, *args: object, **kwargs: object) -> None:
        self.calls.append(("fill_text", args, kwargs))

    def flush(self) -> None:
        self.calls.append(("flush", (), {}))


def test_render_draws_to_canvas_compatible_object() -> None:
    game = FlappyGame(seed=123)
    canvas = FakeCanvas()

    game.render(canvas)

    method_names = [name for name, _args, _kwargs in canvas.calls]
    assert "delete" in method_names
    assert "create_rectangle" in method_names
    assert "create_oval" in method_names
    assert "create_text" in method_names


def test_render_draws_to_ipycanvas_compatible_object() -> None:
    game = FlappyGame(seed=123)
    canvas = FakeIpyCanvas()

    game.render(canvas)

    method_names = [name for name, _args, _kwargs in canvas.calls]
    assert canvas.width == game.width
    assert canvas.height == game.height
    assert "clear" in method_names
    assert "fill_rect" in method_names
    assert "stroke_rect" in method_names
    assert "fill_circle" in method_names
    assert "stroke_circle" in method_names
    assert "fill_text" in method_names
    assert method_names[-1] == "flush"


def test_render_rejects_unsupported_canvas() -> None:
    game = FlappyGame(seed=123)

    with pytest.raises(TypeError, match="tkinter.Canvas or ipycanvas.Canvas"):
        game.render(object())
