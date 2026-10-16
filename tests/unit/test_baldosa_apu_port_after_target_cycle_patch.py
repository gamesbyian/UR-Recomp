"""RF-031 queue semantics: exact source, boundary C execution, no shipping stage."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import baldosa_apu_port_after_target_cycle_patch as rf031  # noqa: E402


class SourcePin(unittest.TestCase):
    def test_idempotent_and_tamper_rejecting(self):
        base = ("uint64_t target = apu->portTargetAnchor +\n"
                "void apu_cycle(Apu* apu)\n" + rf031.OLD)
        out = rf031.patch(base)
        self.assertEqual(rf031.patch(out), out)
        self.assertEqual(out.count(rf031.MARK), 1)
        with self.assertRaisesRegex(ValueError, "unknown pinned"):
            rf031.patch(base.replace("void apu_cycle", "void random_cycle"))
        with self.assertRaisesRegex(ValueError, "queue stage modified"):
            rf031.patch(out.replace(">= apu->portClock", "> apu->portClock"))

    def test_shipping_and_normal_qa_unchanged(self):
        windows = (ROOT / ".github/workflows/baldosa-windows-native-bridge.yml").read_text()
        self.assertNotIn("baldosa_apu_port_after_target_cycle_patch.py", windows)
        core = (ROOT / ".github/workflows/qa01-event-campaign.yml").read_text()
        self.assertNotIn("baldosa_apu_port_after_target_cycle_patch.py", core)


@unittest.skipUnless(shutil.which("cc") or shutil.which("gcc"), "requires C compiler")
class ClockBoundary(unittest.TestCase):
    def test_just_due_target_is_not_visible_to_receiver_early(self):
        # Extract the exact predicate from the treatment to test the code
        # itself, not an independent Python approximation.
        old_guard = rf031.OLD.splitlines()[0].strip()[3:]
        new_guard = rf031.NEW.splitlines()[-3].strip()[3:]
        self.assertEqual(old_guard, "(w->target_cycle > apu->portClock)")
        self.assertEqual(new_guard, "(w->target_cycle >= apu->portClock)")
        template = r"""
#include <stdio.h>
#include <stdint.h>
typedef struct { uint64_t target_cycle; } W;
typedef struct { uint64_t portClock; } A;
static int should_wait(W *w, A *apu) { return PREDICATE; }
int main(void) {
  W w={100}; A a={99}; int before=should_wait(&w,&a);
  a.portClock=100; int at=should_wait(&w,&a);
  a.portClock=101; int after=should_wait(&w,&a);
  printf("%d %d %d\n",before,at,after);
  return 0;
}
"""
        cc = shutil.which("cc") or shutil.which("gcc")
        for guard,expected in ((old_guard, "1 0 0"), (new_guard, "1 1 0")):
            with tempfile.TemporaryDirectory() as d:
                c = pathlib.Path(d) / "clock.c"
                exe = pathlib.Path(d) / "clock"
                c.write_text(template.replace("PREDICATE",guard[1:-1]))
                subprocess.run([cc, "-std=c99","-Wall","-Werror", str(c),"-o",str(exe)],
                               check=True,capture_output=True,text=True)
                result = subprocess.run([str(exe)],capture_output=True,text=True,check=True)
                self.assertEqual(result.stdout.strip(),expected)


if __name__ == "__main__":
    unittest.main()
