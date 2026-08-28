"""
Builds Cursor-on-Target (CoT) XML events from Sentinel Vault detections,
for publishing to a TAK Server / ATAK / WinTAK / FreeTAKServer mesh over
the MQTT bridge.

Adapted from ThinkForgeLabs/ODDS (odds-v3) app/services/cot_builder.py.
Per product scope, this port drops monocular range/bearing estimation and
target designation entirely — there is no drone tracker here. Each camera
instead reports its own static, user-entered latitude/longitude (if set)
as the detection's plotted point, with the CoT convention for "no
position-error estimate available" (9999999.0) on ce/le, since the point
represents the camera's surveyed location rather than a computed target fix.

CoT is the standard XML situational-awareness format used across the TAK
ecosystem. A minimal event looks like:

    <event version="2.0" uid="..." type="a-u-G" time="..." start="..."
           stale="..." how="m-g">
        <point lat="34.5" lon="-117.2" hae="0.0" ce="9999999.0" le="9999999.0"/>
        <detail>
            <contact callsign="Camera Name - person"/>
            <remarks>...</remarks>
        </detail>
    </event>
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import quoteattr


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def build_detection_cot(
    *,
    camera_id: str,
    camera_name: str,
    latitude: float,
    longitude: float,
    hae_m: float = 0.0,
    class_name: str,
    confidence: float,
    cot_type: str = "a-u-G",
    stale_seconds: float = 60.0,
    ce_meters: float = 9999999.0,
    le_meters: float = 9999999.0,
    location_label: str = "",
) -> str:
    """Render a single CoT <event> XML string for a detection alert."""
    now = datetime.now(timezone.utc)
    stale = now + timedelta(seconds=max(stale_seconds, 1.0))

    uid = f"SV-{camera_id}-{uuid.uuid4().hex[:8]}"
    callsign = f"{camera_name or 'Sentinel Vault Camera'} — {class_name}"

    remarks_text = (
        f"Detected '{class_name}' (confidence {confidence:.0%}) by Sentinel Vault "
        f"camera '{camera_name}'"
        + (f" at {location_label}" if location_label else "")
        + ". Position reflects the camera's surveyed location, not a computed "
        "target fix."
    )

    sv_attrs = (
        f'camera_id={quoteattr(str(camera_id))} class_name={quoteattr(str(class_name))} '
        f'confidence={quoteattr(f"{confidence:.4f}")}'
    )

    detail_children = [
        f'<contact callsign={quoteattr(callsign)}/>',
        f'<remarks>{_escape_text(remarks_text)}</remarks>',
        # Non-standard but harmless custom tag; unknown detail children are
        # ignored by TAK clients that don't recognize them.
        f'<sentinelvault {sv_attrs}/>',
    ]

    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<event version="2.0" uid={quoteattr(uid)} type={quoteattr(cot_type)} '
        f'time={quoteattr(_iso(now))} start={quoteattr(_iso(now))} '
        f'stale={quoteattr(_iso(stale))} how="m-g">'
        f'<point lat="{latitude:.7f}" lon="{longitude:.7f}" hae="{hae_m:.1f}" '
        f'ce="{ce_meters}" le="{le_meters}"/>'
        f'<detail>{"".join(detail_children)}</detail>'
        "</event>"
    )
    return xml


def _escape_text(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
