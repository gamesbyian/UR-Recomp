/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.romtools;

import docking.action.builder.ActionBuilder;
import ghidra.app.context.ProgramLocationActionContext;
import ghidra.framework.plugintool.PluginTool;
import ghidra.program.database.mem.AddressSourceInfo;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Program;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.Msg;
import java.util.function.BooleanSupplier;
import java.util.OptionalLong;

/**
 * Popup action that labels the current address with its backing ROM file offset.
 */
public final class RomOffsetLabelAction {
  private static final String ACTION_NAME = "Create ROM Offset Label";
  private static final String POPUP_ROOT = "SNES ROM Tools";
  private final BooleanSupplier currentProgramIsSnesSupplier;

  /**
   * Registers the popup action in the listing context menu.
   *
   * @param tool active plugin tool used to install the action
   * @param owner action owner id used by Ghidra's action framework
   * @param currentProgramIsSnesSupplier supplies true when the active program is a SNES ROM
   */
  public RomOffsetLabelAction(
      PluginTool tool, String owner, BooleanSupplier currentProgramIsSnesSupplier) {
    this.currentProgramIsSnesSupplier = currentProgramIsSnesSupplier;

    new ActionBuilder(ACTION_NAME, owner)
      .withContext(ProgramLocationActionContext.class)
      .popupMenuPath(POPUP_ROOT, ACTION_NAME)
      .description("Create a label from the ROM file offset backing this address.")
      .popupWhen(this::isVisibleInPopup)
      .enabledWhen(this::isEnabled)
      .onAction(this::createRomOffsetLabel)
      .buildAndInstall(tool);
  }

  /**
   * Returns true when the action should appear in the popup menu.
   */
  private boolean isVisibleInPopup(ProgramLocationActionContext context) {
    if (context == null) {
      return false;
    }
    return currentProgramIsSnesSupplier.getAsBoolean();
  }

  /**
   * Returns true when the action can be executed for this context.
   */
  private boolean isEnabled(ProgramLocationActionContext context) {
    if (context == null) {
      return false;
    }
    return resolveRomFileOffset(context).isPresent();
  }

  /**
   * Creates the ROM offset label at the current listing address.
   */
  private void createRomOffsetLabel(ProgramLocationActionContext context) {
    Program program = context.getProgram();
    Address address = context.getAddress();

    if (program == null || address == null) {
      return;
    }

    OptionalLong fileOffsetOpt = resolveRomFileOffset(context);
    if (fileOffsetOpt.isEmpty()) {
      Msg.showWarn(
        RomOffsetLabelAction.class,
        null,
        "Create ROM Offset Label",
        "Selected address is not backed by ROM file bytes.");
      return;
    }

    long fileOffset = fileOffsetOpt.getAsLong();
    String labelName = String.format("ROM_%08X", fileOffset);

    int transactionId = program.startTransaction("Create SNES ROM offset label");
    boolean success = false;

    try {
      if (program.getSymbolTable().getGlobalSymbol(labelName, address) != null) {
        success = true;
        return;
      }

      program.getSymbolTable().createLabel(address, labelName, SourceType.USER_DEFINED);
      success = true;
    } catch (Exception exception) {
      Msg.showError(
        RomOffsetLabelAction.class,
        null,
        "Create ROM Offset Label",
        "Unable to create label '" + labelName + "'.",
        exception);
    } finally {
      program.endTransaction(transactionId, success);
    }
  }

  /**
   * Resolves the imported ROM file offset that backs the current address.
   */
  private OptionalLong resolveRomFileOffset(ProgramLocationActionContext context) {
    if (context == null) {
      return OptionalLong.empty();
    }

    Program program = context.getProgram();
    Address address = context.getAddress();

    if (program == null || address == null) {
      return OptionalLong.empty();
    }

    AddressSourceInfo sourceInfo = program.getMemory().getAddressSourceInfo(address);
    if (sourceInfo == null) {
      return OptionalLong.empty();
    }

    long fileOffset = sourceInfo.getFileOffset();
    if (fileOffset < 0) {
      return OptionalLong.empty();
    }

    return OptionalLong.of(fileOffset);
  }
}
