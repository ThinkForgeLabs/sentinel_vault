import numpy as np

from app.modules.detection.motion import MotionDetector


def _make_frame(h=240, w=320, fill=60):
    return np.full((h, w, 3), fill, dtype=np.uint8)


def _make_frame_with_square(h=240, w=320, base_fill=60, square_fill=220, size=60):
    frame = _make_frame(h, w, base_fill)
    frame[40:40 + size, 40:40 + size] = square_fill
    return frame


def test_downscale_factor_detects_motion_and_scales_boxes_up():
    detector = MotionDetector(
        camera_id="cam-downscale",
        threshold=25,
        min_contour_area=200,
        downscale_factor=0.5,
    )

    # First frame just seeds the reference — no motion expected.
    assert detector.process_frame(_make_frame()) is None

    result = detector.process_frame(_make_frame_with_square())
    assert result is not None
    assert result.total_area > 0
    assert len(result.bounding_boxes) >= 1
    # Boxes should be reported in full-resolution coordinates (roughly
    # matching the 60x60 square drawn on the un-scaled frame), not the
    # smaller downscaled-frame coordinates.
    _, _, box_w, box_h = result.bounding_boxes[0]
    assert box_w >= 40
    assert box_h >= 40


def test_frame_skip_ignores_intermediate_frames():
    detector = MotionDetector(
        camera_id="cam-skip",
        threshold=25,
        min_contour_area=200,
        frame_skip=2,  # process every 3rd frame (skip 2 in between)
    )

    # Frame 1 (index 0): processed, seeds reference.
    assert detector.process_frame(_make_frame()) is None
    # Frames 2-3 (index 1-2): skipped entirely, even though they contain
    # motion — they must not affect the stored reference frame or trigger
    # a result.
    assert detector.process_frame(_make_frame_with_square()) is None
    assert detector.process_frame(_make_frame_with_square()) is None
    # Frame 4 (index 3): processed again; compares against the frame-1
    # reference (still the plain frame), so the square is now visible as
    # motion.
    result = detector.process_frame(_make_frame_with_square())
    assert result is not None


def test_defaults_preserve_original_behavior():
    detector = MotionDetector(camera_id="cam-default")
    assert detector.downscale_factor == 1.0
    assert detector.frame_skip == 0

    assert detector.process_frame(_make_frame()) is None
    result = detector.process_frame(_make_frame_with_square())
    assert result is not None
