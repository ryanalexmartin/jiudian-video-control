"""Adaptive default preset scenes at 1920x1080."""
from __future__ import annotations

from jiudian_server.compositing.models import Layer, Scene

_W, _H = 1920, 1080


def _fullscreen(input_id: int) -> Scene:
    return Scene(
        id=f"fullscreen_{input_id + 1}",
        name=f"\u5168\u87a2\u5e55 - \u8f38\u5165 {input_id + 1}",
        layers=[Layer(input_id=input_id, x=0, y=0, width=_W, height=_H)],
        is_default=True,
    )


def generate_default_scenes(input_ids: list[int]) -> list[Scene]:
    """Generate default scenes adapted to the available input IDs.

    Always produces a fullscreen preset per input.
    PiP and side-by-side if >= 2 inputs.
    Quad view if >= 4 inputs.
    """
    if not input_ids:
        input_ids = [0]

    scenes: list[Scene] = []

    # Fullscreen preset per input
    for iid in input_ids:
        scenes.append(_fullscreen(iid))

    sorted_ids = sorted(input_ids)

    # PiP - bottom right (first two inputs)
    if len(sorted_ids) >= 2:
        a, b = sorted_ids[0], sorted_ids[1]
        scenes.append(Scene(
            id="pip_br",
            name="\u5b50\u6bcd\u756b\u9762 - \u53f3\u4e0b",
            layers=[
                Layer(input_id=a, x=0, y=0, width=_W, height=_H, z_order=0),
                Layer(
                    input_id=b,
                    x=_W - 480 - 20,
                    y=_H - 270 - 20,
                    width=480,
                    height=270,
                    z_order=1,
                    border_width=2,
                    border_color="#00C8FF",
                ),
            ],
            is_default=True,
        ))

        # Side by side
        scenes.append(Scene(
            id="side_by_side",
            name="\u4e26\u6392\u756b\u9762",
            layers=[
                Layer(input_id=a, x=0, y=0, width=_W // 2, height=_H, z_order=0),
                Layer(input_id=b, x=_W // 2, y=0, width=_W // 2, height=_H, z_order=0),
            ],
            is_default=True,
        ))

    # Quad view (first four inputs)
    if len(sorted_ids) >= 4:
        q = sorted_ids[:4]
        scenes.append(Scene(
            id="quad",
            name="\u56db\u5206\u5272\u756b\u9762",
            layers=[
                Layer(input_id=q[0], x=0, y=0, width=_W // 2, height=_H // 2, z_order=0),
                Layer(input_id=q[1], x=_W // 2, y=0, width=_W // 2, height=_H // 2, z_order=0),
                Layer(input_id=q[2], x=0, y=_H // 2, width=_W // 2, height=_H // 2, z_order=0),
                Layer(input_id=q[3], x=_W // 2, y=_H // 2, width=_W // 2, height=_H // 2, z_order=0),
            ],
            is_default=True,
        ))

    return scenes


# Backwards-compatible constant for code that still references DEFAULT_SCENES
DEFAULT_SCENES: list[Scene] = generate_default_scenes([0, 1, 2, 3])
DEFAULT_SCENES_BY_ID: dict[str, Scene] = {s.id: s for s in DEFAULT_SCENES}
