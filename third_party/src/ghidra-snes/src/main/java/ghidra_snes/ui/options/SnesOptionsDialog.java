/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.options;

import docking.DialogComponentProvider;
import ghidra.program.model.listing.Program;

public final class SnesOptionsDialog extends DialogComponentProvider {
  /**
   * Creates the modal SNES options dialog and mounts the main options component.
   *
   * @param currentProgram active program used by pages that display ROM metadata
   */
  public SnesOptionsDialog(Program currentProgram) {
    super("SNES Options", true);

    addWorkPanel(new SnesOptionsComponent(currentProgram));
    addDismissButton();
    setPreferredSize(980, 680);
  }
}
