import pytest
from pydantic import ValidationError
from app.models.schema import VideoAspect, VideoRewriteParams


def test_landscape_resolution():
    assert VideoAspect.landscape.to_resolution() == (1920, 1080)


def test_portrait_resolution():
    assert VideoAspect.portrait.to_resolution() == (1080, 1920)


def test_square_resolution():
    assert VideoAspect.square.to_resolution() == (1080, 1080)


def test_video_rewrite_params_defaults():
    params = VideoRewriteParams()
    assert params.video_count == 1
    assert params.subtitle_enabled is True
    assert params.voice_volume == 1.0


def test_invalid_aspect_raises_validation_error():
    with pytest.raises(ValidationError):
        VideoRewriteParams(video_aspect="invalid_ratio")
