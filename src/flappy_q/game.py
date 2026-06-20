"""Core deterministic Flappy Bird-style game simulation."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True, slots=True)
class GameState:
    """The observation exposed to tutorial agents."""

    dy: float
    vy: float
    dx: float


@dataclass(slots=True)
class _Pipe:
    x: float
    gap_y: float
    scored: bool = False


class FlappyGame:
    """A deterministic tick-driven Flappy Bird-style game.

    Coordinates use a top-left origin. Positive `dy` means the bird is below the
    center of the next pipe opening; negative `dy` means it is above.
    """

    def __init__(
        self,
        seed: int | None = None,
        *,
        width: int = 640,
        height: int = 480,
        bird_x: float = 120.0,
        bird_radius: float = 14.0,
        gravity: float = 0.45,
        flap_impulse: float = -7.5,
        scroll_speed: float = 3.0,
        pipe_width: float = 72.0,
        pipe_gap: float = 140.0,
        pipe_spacing: float = 240.0,
    ) -> None:
        self.width = width
        self.height = height
        self.bird_x = bird_x
        self.bird_radius = bird_radius
        self.gravity = gravity
        self.flap_impulse = flap_impulse
        self.scroll_speed = scroll_speed
        self.pipe_width = pipe_width
        self.pipe_gap = pipe_gap
        self.pipe_spacing = pipe_spacing

        self._validate_config()

        self.seed = seed
        self._rng = Random(seed)
        self._pipes: list[_Pipe] = []
        self._bird_y = 0.0
        self._bird_vy = 0.0
        self._alive = True
        self._score = 0
        self._ticks = 0
        self.reset(seed=seed)

    @property
    def state(self) -> GameState:
        return self._read_state()

    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def score(self) -> int:
        return self._score

    @property
    def obstacles_passed(self) -> int:
        """Number of pipe obstacles passed in the current run."""
        return self._score

    @property
    def ticks(self) -> int:
        return self._ticks

    @property
    def frames(self) -> int:
        """Number of live simulation frames elapsed in the current run."""
        return self._ticks

    def reset(self, seed: int | None = None) -> GameState:
        """Restart the game.

        Passing a seed replaces the current seed. Calling reset without a seed
        reuses the existing seed, so the same game object can replay the same map.
        """

        if seed is not None:
            self.seed = seed
        self._rng = Random(self.seed)
        self._bird_y = self.height / 2
        self._bird_vy = 0.0
        self._alive = True
        self._score = 0
        self._ticks = 0

        self._pipes = []
        x = self.width - 80.0
        while x < self.width + (self.pipe_spacing * 3):
            self._pipes.append(_Pipe(x=x, gap_y=self._random_gap_y()))
            x += self.pipe_spacing

        return self.state

    def tick(self, flap: bool) -> GameState:
        """Advance the simulation by exactly one tick."""

        if not self._alive:
            return self.state

        self._ticks += 1
        if flap:
            self._bird_vy = self.flap_impulse

        self._bird_vy += self.gravity
        self._bird_y += self._bird_vy

        for pipe in self._pipes:
            pipe.x -= self.scroll_speed

        self._update_score()
        self._drop_old_pipes()
        self._extend_pipes()
        self._alive = not self._has_collision()

        return self.state

    def render(self, canvas: object) -> None:
        """Render the current scene to a tkinter.Canvas or ipycanvas.Canvas."""

        if self._is_tk_canvas(canvas):
            self._render_tk(canvas)
            return

        if self._is_ipycanvas(canvas):
            self._render_ipycanvas(canvas)
            return

        raise TypeError(
            "canvas must be compatible with tkinter.Canvas or ipycanvas.Canvas"
        )

    def _render_tk(self, canvas: object) -> None:
        if hasattr(canvas, "configure"):
            canvas.configure(width=self.width, height=self.height)

        canvas.delete("all")
        canvas.create_rectangle(0, 0, self.width, self.height, fill="#8bd3ff", width=0)
        canvas.create_rectangle(
            0,
            self.height - 42,
            self.width,
            self.height,
            fill="#72b657",
            width=0,
        )

        gap_half = self.pipe_gap / 2
        for pipe in self._pipes:
            x1 = pipe.x
            x2 = pipe.x + self.pipe_width
            if x2 < 0 or x1 > self.width:
                continue

            top_gap = pipe.gap_y - gap_half
            bottom_gap = pipe.gap_y + gap_half
            canvas.create_rectangle(x1, 0, x2, top_gap, fill="#3a9d44", outline="#237a31")
            canvas.create_rectangle(
                x1,
                bottom_gap,
                x2,
                self.height,
                fill="#3a9d44",
                outline="#237a31",
            )

        r = self.bird_radius
        canvas.create_oval(
            self.bird_x - r,
            self._bird_y - r,
            self.bird_x + r,
            self._bird_y + r,
            fill="#ffd447" if self._alive else "#c8c8c8",
            outline="#3f2d1c",
            width=2,
        )

        canvas.create_text(
            16,
            16,
            text=f"Score {self._score}",
            anchor="nw",
            fill="#17324d",
            font=("Helvetica", 16, "bold"),
        )
        if not self._alive:
            canvas.create_text(
                self.width / 2,
                self.height / 2,
                text="Game over - press R",
                fill="#17324d",
                font=("Helvetica", 24, "bold"),
            )

    def _render_ipycanvas(self, canvas: object) -> None:
        self._configure_ipycanvas(canvas)
        save = getattr(canvas, "save", None)
        restore = getattr(canvas, "restore", None)
        flush = getattr(canvas, "flush", None)
        should_restore = callable(save) and callable(restore)

        if should_restore:
            save()

        try:
            canvas.clear()

            self._ipy_fill_rect(canvas, 0, 0, self.width, self.height, "#8bd3ff")
            self._ipy_fill_rect(
                canvas, 0, self.height - 42, self.width, 42, "#72b657"
            )

            gap_half = self.pipe_gap / 2
            for pipe in self._pipes:
                x = pipe.x
                if x + self.pipe_width < 0 or x > self.width:
                    continue

                top_gap = pipe.gap_y - gap_half
                bottom_gap = pipe.gap_y + gap_half
                self._ipy_rect(
                    canvas,
                    x,
                    0,
                    self.pipe_width,
                    top_gap,
                    fill="#3a9d44",
                    outline="#237a31",
                )
                self._ipy_rect(
                    canvas,
                    x,
                    bottom_gap,
                    self.pipe_width,
                    self.height - bottom_gap,
                    fill="#3a9d44",
                    outline="#237a31",
                )

            self._ipy_circle(
                canvas,
                self.bird_x,
                self._bird_y,
                self.bird_radius,
                fill="#ffd447" if self._alive else "#c8c8c8",
                outline="#3f2d1c",
                width=2,
            )

            self._ipy_text(
                canvas,
                f"Score {self._score}",
                16,
                16,
                fill="#17324d",
                font="bold 16px Helvetica",
                align="left",
                baseline="top",
            )
            if not self._alive:
                self._ipy_text(
                    canvas,
                    "Game over - press R",
                    self.width / 2,
                    self.height / 2,
                    fill="#17324d",
                    font="bold 24px Helvetica",
                    align="center",
                    baseline="middle",
                )
        finally:
            if should_restore:
                restore()

        if callable(flush):
            flush()

    @staticmethod
    def _is_tk_canvas(canvas: object) -> bool:
        return all(
            callable(getattr(canvas, name, None))
            for name in ("delete", "create_rectangle", "create_oval", "create_text")
        )

    @staticmethod
    def _is_ipycanvas(canvas: object) -> bool:
        return all(
            callable(getattr(canvas, name, None))
            for name in (
                "clear",
                "fill_rect",
                "stroke_rect",
                "fill_circle",
                "stroke_circle",
                "fill_text",
            )
        )

    def _configure_ipycanvas(self, canvas: object) -> None:
        if hasattr(canvas, "width"):
            canvas.width = self.width
        if hasattr(canvas, "height"):
            canvas.height = self.height

    @staticmethod
    def _ipy_fill_rect(
        canvas: object, x: float, y: float, width: float, height: float, fill: str
    ) -> None:
        canvas.fill_style = fill
        canvas.fill_rect(x, y, width, height)

    @classmethod
    def _ipy_rect(
        cls,
        canvas: object,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill: str,
        outline: str,
    ) -> None:
        cls._ipy_fill_rect(canvas, x, y, width, height, fill)
        canvas.stroke_style = outline
        canvas.stroke_rect(x, y, width, height)

    @staticmethod
    def _ipy_circle(
        canvas: object,
        x: float,
        y: float,
        radius: float,
        *,
        fill: str,
        outline: str,
        width: float,
    ) -> None:
        canvas.fill_style = fill
        canvas.fill_circle(x, y, radius)
        canvas.stroke_style = outline
        canvas.line_width = width
        canvas.stroke_circle(x, y, radius)

    @staticmethod
    def _ipy_text(
        canvas: object,
        text: str,
        x: float,
        y: float,
        *,
        fill: str,
        font: str,
        align: str,
        baseline: str,
    ) -> None:
        canvas.fill_style = fill
        canvas.font = font
        canvas.text_align = align
        canvas.text_baseline = baseline
        canvas.fill_text(text, x, y)

    def _validate_config(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if not 0 < self.bird_x < self.width:
            raise ValueError("bird_x must be inside the world")
        if self.bird_radius <= 0:
            raise ValueError("bird_radius must be positive")
        if self.scroll_speed <= 0:
            raise ValueError("scroll_speed must be positive")
        if self.pipe_width <= 0 or self.pipe_gap <= 0 or self.pipe_spacing <= 0:
            raise ValueError("pipe dimensions must be positive")

        top_margin, bottom_margin = self._gap_bounds()
        if top_margin >= bottom_margin:
            raise ValueError("pipe_gap is too large for the configured height")

    def _gap_bounds(self) -> tuple[float, float]:
        margin = (self.pipe_gap / 2) + self.bird_radius + 8
        return margin, self.height - margin

    def _random_gap_y(self) -> float:
        top_margin, bottom_margin = self._gap_bounds()
        return self._rng.uniform(top_margin, bottom_margin)

    def _read_state(self) -> GameState:
        pipe = self._next_pipe()
        return GameState(
            dy=self._bird_y - pipe.gap_y,
            vy=self._bird_vy,
            dx=pipe.x - self.bird_x,
        )

    def _next_pipe(self) -> _Pipe:
        for pipe in self._pipes:
            if pipe.x + self.pipe_width >= self.bird_x - self.bird_radius:
                return pipe
        return self._pipes[0]

    def _update_score(self) -> None:
        for pipe in self._pipes:
            if not pipe.scored and pipe.x + self.pipe_width < self.bird_x:
                pipe.scored = True
                self._score += 1

    def _drop_old_pipes(self) -> None:
        while len(self._pipes) > 1 and self._pipes[0].x + self.pipe_width < 0:
            self._pipes.pop(0)

    def _extend_pipes(self) -> None:
        while self._pipes[-1].x < self.width + (self.pipe_spacing * 2):
            next_x = self._pipes[-1].x + self.pipe_spacing
            self._pipes.append(_Pipe(x=next_x, gap_y=self._random_gap_y()))

    def _has_collision(self) -> bool:
        if self._bird_y - self.bird_radius <= 0:
            return True
        if self._bird_y + self.bird_radius >= self.height:
            return True

        gap_half = self.pipe_gap / 2
        for pipe in self._pipes:
            horizontally_overlaps = (
                self.bird_x + self.bird_radius > pipe.x
                and self.bird_x - self.bird_radius < pipe.x + self.pipe_width
            )
            if not horizontally_overlaps:
                continue

            top_gap = pipe.gap_y - gap_half
            bottom_gap = pipe.gap_y + gap_half
            outside_gap = (
                self._bird_y - self.bird_radius < top_gap
                or self._bird_y + self.bird_radius > bottom_gap
            )
            if outside_gap:
                return True

        return False
