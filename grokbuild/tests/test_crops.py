from grokbuild.qa.crops import expand_box


def test_scale_1_keeps_the_face_box():
    assert expand_box((10.0, 10.0, 20.0, 20.0), 1.0, 100, 100) == (10.0, 10.0, 20.0, 20.0)


def test_scale_1_5_expands_around_the_center():
    assert expand_box((10.0, 10.0, 20.0, 20.0), 1.5, 100, 100) == (5.0, 5.0, 30.0, 30.0)


def test_scale_1_5_is_clipped_to_the_frame():
    cropped = expand_box((0.0, 0.0, 10.0, 10.0), 1.5, 100, 100)
    assert cropped == (0.0, 0.0, 12.5, 12.5)


def test_non_positive_box_is_rejected():
    assert expand_box((0.0, 0.0, 0.0, 10.0), 1.5, 100, 100) is None
    assert expand_box((0.0, 0.0, 10.0, 10.0), 0, 100, 100) is None
    assert expand_box((0.0, 0.0, 10.0, 10.0), 1.0, 0, 100) is None
