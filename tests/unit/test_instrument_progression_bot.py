import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/instrument_progression_bot.py"


def test_instrument_progression_bot(tmp_path):
    src = tmp_path / "bot.lua"
    out = tmp_path / "instrumented.lua"
    src.write_text(
        """targetMedal = 21 -- 17 for bronze, 19 for silver, 21 for gold
needNewPlayer = false
	
function Run()
    while(true) do
        if true then
            emu.frameadvance()
        else
            emu.frameadvance()
        end
    end
end

--snes9x.speedmode("nothrottle")
Run()
""",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(TOOL), str(src), str(out)],
        cwd=ROOT,
        check=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "targetMedal = 17 -- progression acceptance: bronze" in text
    assert text.count("URProgressionMonitor()") == 2
    assert 'snes9x.speedmode("nothrottle")' in text
    assert '--snes9x.speedmode("nothrottle")' not in text
