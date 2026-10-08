import pathlib
import unittest

from tools.build_audio_checkpoint_route import CHECKPOINTS, POST_CHECKPOINT_FRAMES, checkpoint_route

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tests" / "input" / "reach-first-race.script"


class NativeAudioCheckpointRouteTests(unittest.TestCase):
    def test_named_prefixes_come_from_existing_stock_route(self):
        source = SOURCE.read_text(encoding="utf-8")
        previous_length = 0
        for checkpoint in CHECKPOINTS:
            with self.subTest(checkpoint=checkpoint):
                script = checkpoint_route(source, checkpoint)
                self.assertTrue(script.endswith(
                    f"dump {checkpoint}\n"
                    f"wait {POST_CHECKPOINT_FRAMES}\n"
                    f"dump {checkpoint}-audio-post\nquit\n"
                ))
                self.assertEqual(script.count("\nquit\n"), 1)
                self.assertGreater(len(script), previous_length)
                # After the selected checkpoint only bounded passive input,
                # an observed tail-frame marker, then a clean quit may follow.
                previous_length = len(script)
                before, final = script.rsplit(f"dump {checkpoint}\n", 1)
                self.assertEqual(
                    final,
                    f"wait {POST_CHECKPOINT_FRAMES}\n"
                    f"dump {checkpoint}-audio-post\nquit\n",
                )
                self.assertFalse(any(x.startswith("poke ") for x in script.splitlines()))
                self.assertTrue(any(x.startswith("until ") for x in before.splitlines()))

        menu = checkpoint_route(source, "main-menu-ready")
        now = checkpoint_route(source, "now-playing-ready")
        race = checkpoint_route(source, "race-entered")
        self.assertNotIn("press a 2", menu)
        self.assertIn("press a 2", now)
        self.assertIn("until 0313 == 01", race)
        self.assertNotIn("until 0313 == 01", now)

    def test_unknown_checkpoint_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            checkpoint_route("dump some-state", "some-state")

    def test_ambiguous_or_missing_dump_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            checkpoint_route("wait 10\ndump race-entered\ndump race-entered\n", "race-entered")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            checkpoint_route("wait 10\nquit\n", "race-entered")

    def test_premature_quit_rejected(self):
        with self.assertRaisesRegex(ValueError, "quits before"):
            checkpoint_route("quit\ndump main-menu-ready\n", "main-menu-ready")


if __name__ == "__main__":
    unittest.main()
