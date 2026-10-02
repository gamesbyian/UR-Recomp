#!/usr/bin/env python3
"""Apply narrow modern-GCC compatibility fixes to Snes9x 1.51-rr Lua bridge."""

from pathlib import Path

path = Path("lua-engine.cpp")
text = path.read_text()

old_iter = "std::vector<Island>::const_iterator"
new_iter = "typename std::vector<Island>::const_iterator"
count = text.count(old_iter)
if count != 2:
    raise SystemExit(f"expected 2 dependent iterator sites, found {count}")
text = text.replace(old_iter, new_iter)

old_printf = """	va_list list;
	va_start(list, fmt);
	int len = vscprintf(fmt, list);
	char* str = new char[len+1];
	vsprintf(str, fmt, list);
	va_end(list);"""
new_printf = """	va_list list;
	va_start(list, fmt);
	va_list measure;
	__va_copy(measure, list);
	int len = vsnprintf(NULL, 0, fmt, measure);
	va_end(measure);
	char* str = new char[len+1];
	vsnprintf(str, len+1, fmt, list);
	va_end(list);"""
if old_printf not in text:
    raise SystemExit("printfToOutput compatibility site not found")
text = text.replace(old_printf, new_printf, 1)


old_ctor = """	TieredRegion()
	{
		Calculate(std::vector<unsigned int>());
	}"""
new_ctor = """	TieredRegion()
	{
		std::vector<unsigned int> empty;
		Calculate(empty);
	}"""
if old_ctor not in text:
    raise SystemExit("TieredRegion constructor compatibility site not found")
text = text.replace(old_ctor, new_ctor, 1)

path.write_text(text)

cpu = Path("cpuexec.cpp")
cpu_text = cpu.read_text()
old_trace = """		//S9xUnpackStatus();
		S9xTraceCPU();
		CallRegisteredLuaMemHook(Registers.PBPC, ICPU.S9xOpLengths[Op], Op, LUAMEMHOOK_EXEC);"""
new_trace = """		//S9xUnpackStatus();
#ifdef DEBUGGER
		S9xTraceCPU();
#endif
		CallRegisteredLuaMemHook(Registers.PBPC, ICPU.S9xOpLengths[Op], Op, LUAMEMHOOK_EXEC);"""
if old_trace not in cpu_text:
    raise SystemExit("non-debug trace compatibility site not found")
cpu.write_text(cpu_text.replace(old_trace, new_trace, 1))

print("patched historical Snes9x build seams for modern GCC without changing emulation semantics")
