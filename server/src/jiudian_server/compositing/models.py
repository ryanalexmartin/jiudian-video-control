"""Scene and Layer data models for compositing."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Layer(BaseModel):
    """A layer in a scene that maps an input source to a position on the output canvas."""

    input_id: int = Field(..., description="Input source index (0-3)")
    x: int = Field(0, description="X position on canvas")
    y: int = Field(0, description="Y position on canvas")
    width: int = Field(1920, description="Width on canvas")
    height: int = Field(1080, description="Height on canvas")
    z_order: int = Field(0, description="Z-order (higher = on top)")
    alpha: float = Field(1.0, ge=0.0, le=1.0, description="Opacity")
    border_width: int = Field(0, ge=0, description="Border width in pixels")
    border_color: str = Field("#00C8FF", description="Border color hex")
    visible: bool = Field(True, description="Whether this layer is visible")


class Scene(BaseModel):
    """A scene defines a layout of layers to be composited onto an output."""

    id: str = Field(..., description="Unique scene identifier")
    name: str = Field(..., description="Display name (Traditional Chinese)")
    layers: list[Layer] = Field(default_factory=list)
    background_color: str = Field("#0B0B1E", description="Background color hex")
    is_default: bool = Field(False, description="Whether this is a built-in preset")

    def get_sorted_layers(self) -> list[Layer]:
        """Return layers sorted by z_order for correct rendering."""
        return sorted(
            [l for l in self.layers if l.visible],
            key=lambda l: l.z_order,
        )
