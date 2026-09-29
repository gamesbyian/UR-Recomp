/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes;

import ghidra.MiscellaneousPluginPackage;
import ghidra.app.plugin.PluginCategoryNames;
import ghidra.app.plugin.ProgramPlugin;
import ghidra.framework.plugintool.PluginInfo;
import ghidra.framework.plugintool.PluginTool;
import ghidra.framework.plugintool.util.PluginStatus;
import ghidra.program.model.listing.Program;
import ghidra_snes.options.SnesOptions;
import ghidra_snes.ui.about.AboutAction;
import ghidra_snes.ui.options.SnesOptionsAction;
import ghidra_snes.ui.romtools.RomOffsetLabelAction;

@PluginInfo(
  status = PluginStatus.RELEASED,
  packageName = MiscellaneousPluginPackage.NAME,
  category = PluginCategoryNames.COMMON,
  shortDescription = "SNES ROM loader helpers",
  description = "SNES ROM loader helpers and UI actions.")
public class SnesPlugin extends ProgramPlugin {
  private boolean currentProgramIsSnes;

  public SnesPlugin(PluginTool tool) {
    super(tool);

    currentProgramIsSnes = SnesOptions.isSnesProgram(getCurrentProgram());

    new AboutAction(tool, getName());
    new SnesOptionsAction(tool, getName(), this::getCurrentProgram);
    new RomOffsetLabelAction(tool, getName(), this::isCurrentProgramSnes);
  }

  @Override
  protected void programActivated(Program program) {
    currentProgramIsSnes = SnesOptions.isSnesProgram(program);
  }

  @Override
  protected void programDeactivated(Program program) {
    currentProgramIsSnes = false;
  }

  private boolean isCurrentProgramSnes() {
    return currentProgramIsSnes;
  }
}
