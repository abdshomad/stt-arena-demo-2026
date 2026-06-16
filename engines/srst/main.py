"""srst — N/A: the claimed model has no public implementation or API.

Reports available=false so the UI grays it out with an N/A badge. If the user
later supplies a real backend (API key + endpoint), wire it like the engines in
the API group (see assumptions/002-engine-to-real-model-mapping.md).
"""
from engine_common import create_unavailable_app

app = create_unavailable_app(
    engine_id="srst",
    reason="SRST does not correspond to any public model or API",
)
