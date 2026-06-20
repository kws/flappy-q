"""Standalone Tkinter wrapper for manual play testing."""

from __future__ import annotations

import argparse
import tkinter as tk
from collections.abc import Sequence

from .game import FlappyGame


class FlappyApp:
    """Small Tkinter app that turns keyboard events into tick inputs."""

    def __init__(self, *, seed: int | None = None, fps: int = 60) -> None:
        self.game = FlappyGame(seed=seed)
        self.fps = fps
        self._flap_requested = False

        self.root = tk.Tk()
        self.root.title("flappy-q")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=self.game.width,
            height=self.game.height,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.root.bind("<space>", self._request_flap)
        self.root.bind("<Up>", self._request_flap)
        self.root.bind("<KeyPress-w>", self._request_flap)
        self.root.bind("<KeyPress-W>", self._request_flap)
        self.root.bind("<KeyPress-r>", self._reset)
        self.root.bind("<KeyPress-R>", self._reset)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

    def run(self) -> None:
        self.game.render(self.canvas)
        self.root.after(self._frame_delay_ms, self._tick)
        self.root.mainloop()

    @property
    def _frame_delay_ms(self) -> int:
        return max(1, round(1000 / self.fps))

    def _request_flap(self, _event: tk.Event[tk.Misc]) -> None:
        self._flap_requested = True

    def _reset(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.game.reset()
        self._flap_requested = False
        self.game.render(self.canvas)

    def _tick(self) -> None:
        if self.game.alive:
            self.game.tick(self._flap_requested)
        self._flap_requested = False
        self.game.render(self.canvas)
        self.root.after(self._frame_delay_ms, self._tick)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the flappy-q Tkinter app.")
    parser.add_argument("--seed", type=int, default=None, help="deterministic map seed")
    parser.add_argument("--fps", type=int, default=60, help="ticks per second")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.fps <= 0:
        raise SystemExit("--fps must be greater than zero")

    app = FlappyApp(seed=args.seed, fps=args.fps)
    app.run()
    return 0
