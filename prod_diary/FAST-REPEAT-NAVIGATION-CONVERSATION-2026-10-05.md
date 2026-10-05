# Fast repeat and navigation conversation transcript

Captured: 2026-10-05

Source: project conversation **Implement navigation shortcuts**.

The user requested a Windows x64-only pass on high-value repeat/navigation shortcuts, explicitly reusing existing Restart, Quick Practice, stock-menu routing and completed-run machinery rather than creating another course picker or restart path.

PR #489, **Add fast rematch, Practice repeat and Recent Course shortcuts**, implemented one-action Rematch/Repeat Practice and a Recent Course shortcut with fail-closed routing. Native acceptance verified unchanged course identity, SRAM/progression safety and non-progressing Practice behavior. Authentic mode remained inert.

A speculative Next Event shortcut was deliberately not forced in before its routing semantics were proven.
