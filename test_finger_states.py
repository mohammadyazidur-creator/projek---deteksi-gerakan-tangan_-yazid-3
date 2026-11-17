import unittest
from types import SimpleNamespace

from utils import get_finger_states


def landmarks_with_thumb(tip_x, tip_y, mirrored=False):
    points = [(0.5, 0.6)] * 21
    points[2] = (0.48, 0.64)
    points[3] = (0.42, 0.62)
    points[4] = (tip_x, tip_y)
    points[5] = (0.5, 0.6)
    points[17] = (0.2, 0.6)
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        points[pip] = (0.5, 0.55)
        points[tip] = (0.5, 0.35)
    if mirrored:
        points = [(1.0 - x, y) for x, y in points]
    return [SimpleNamespace(x=x, y=y, z=0.0) for x, y in points]


class FingerStateTests(unittest.TestCase):
    def test_open_thumb_is_detected_in_either_horizontal_direction(self):
        open_thumb = landmarks_with_thumb(0.32, 0.58)
        mirrored_thumb = landmarks_with_thumb(0.32, 0.58, mirrored=True)
        for landmarks in (open_thumb, mirrored_thumb):
            with self.subTest(landmarks=landmarks[4].x):
                self.assertEqual(get_finger_states(landmarks)[0], 1)

    def test_folded_thumb_is_not_counted_as_open(self):
        folded_thumb = landmarks_with_thumb(0.52, 0.62)

        self.assertEqual(get_finger_states(folded_thumb)[0], 0)


if __name__ == "__main__":
    unittest.main()
