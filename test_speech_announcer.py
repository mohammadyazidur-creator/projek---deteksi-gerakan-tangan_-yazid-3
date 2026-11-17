import unittest

from main import GestureAnnouncer


class FakeSpeaker:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


def detected_gesture(name, hand="Right"):
    return hand, {"name": name}, []


class GestureAnnouncerTests(unittest.TestCase):
    def setUp(self):
        self.speaker = FakeSpeaker()
        self.announcer = GestureAnnouncer(self.speaker)

    def test_speaks_thumb_and_closed_gestures_once_per_change(self):
        self.announcer.update([detected_gesture("Thumbs Up")])
        self.announcer.update([detected_gesture("Thumbs Up")])
        self.announcer.update([detected_gesture("Closed Fist")])

        self.assertEqual(self.speaker.spoken, ["jempol", "tutup"])

    def test_speaks_again_after_hand_leaves_and_returns(self):
        self.announcer.update([detected_gesture("Closed Fist")])
        self.announcer.update([])
        self.announcer.update([detected_gesture("Closed Fist")])

        self.assertEqual(self.speaker.spoken, ["tutup", "tutup"])


if __name__ == "__main__":
    unittest.main()
