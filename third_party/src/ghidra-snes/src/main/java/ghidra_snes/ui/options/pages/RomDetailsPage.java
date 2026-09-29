/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.options.pages;

import docking.widgets.MultiLineLabel;
import docking.widgets.label.GDLabel;
import ghidra.program.model.listing.Program;
import ghidra.util.layout.PairLayout;
import ghidra_snes.options.SnesOptions;
import java.awt.BorderLayout;
import java.awt.Font;
import javax.swing.BorderFactory;
import javax.swing.JPanel;

public final class RomDetailsPage extends JPanel {
  /**
   * Builds the ROM details page used by the options component.
   *
   * @param currentProgram active program whose metadata is displayed
   */
  public RomDetailsPage(Program currentProgram) {
    super(new BorderLayout());
    setBorder(BorderFactory.createEmptyBorder(24, 24, 24, 24));

    GDLabel titleLabel = new GDLabel("ROM Details");
    titleLabel.setFont(titleLabel.getFont().deriveFont(Font.BOLD, 18f));
    add(titleLabel, BorderLayout.NORTH);

    if (currentProgram == null) {
      add(buildEmptyState(), BorderLayout.CENTER);
      return;
    }

    add(buildDetails(currentProgram), BorderLayout.CENTER);
  }

  /**
   * Creates a small placeholder panel when no program is currently active.
   *
   * @return empty-state panel
   */
  private JPanel buildEmptyState() {
    MultiLineLabel emptyState = new MultiLineLabel("No open program.");
    emptyState.setAlignment(MultiLineLabel.LEFT);

    JPanel emptyPanel = new JPanel(new BorderLayout());
    emptyPanel.setBorder(BorderFactory.createEmptyBorder(16, 0, 0, 0));
    emptyPanel.add(emptyState, BorderLayout.NORTH);
    return emptyPanel;
  }

  /**
   * Creates the detailed metadata panel for the active ROM/program.
   *
   * @param currentProgram active program containing SNES metadata options
   * @return populated details panel
   */
  private JPanel buildDetails(Program currentProgram) {
    JPanel detailsPanel = new JPanel(new PairLayout(8, 16));
    detailsPanel.setBorder(BorderFactory.createCompoundBorder(
      BorderFactory.createTitledBorder("Current Program"),
      BorderFactory.createEmptyBorder(10, 10, 10, 10)));

    addInfoRow(detailsPanel, "Program", currentProgram.getName());
    addInfoRow(detailsPanel, "Executable path", normalized(currentProgram.getExecutablePath()));
    addInfoRow(detailsPanel, "Mapper", SnesOptions.getCartMapper(currentProgram));
    addInfoRow(detailsPanel, "ROM title", normalized(SnesOptions.getCartTitle(currentProgram)));
    addInfoRow(detailsPanel, "ROM size", formatBytes(SnesOptions.getRomSizeBytes(currentProgram)));
    addInfoRow(detailsPanel, "SRAM size", formatBytes(SnesOptions.getCartSramSize(currentProgram)));
    addInfoRow(detailsPanel, "SMC header", String.valueOf(SnesOptions.hasSmcHeader(currentProgram)));
    addInfoRow(detailsPanel, "ROM offset", formatHex(SnesOptions.getFileRomOffset(currentProgram)));
    addInfoRow(detailsPanel, "Header location", formatHex(SnesOptions.getRomHeader(currentProgram).location()));
    addInfoRow(detailsPanel, "Metadata source", SnesOptions.getMetadataSource(currentProgram));

    JPanel content = new JPanel(new BorderLayout());
    content.setBorder(BorderFactory.createEmptyBorder(16, 0, 0, 0));
    content.add(detailsPanel, BorderLayout.NORTH);
    return content;
  }

  /**
   * Adds a key/value row to the details table.
   *
   * @param detailsPanel panel receiving rows
   * @param key left-side label
   * @param value right-side value text
   */
  private void addInfoRow(JPanel detailsPanel, String key, String value) {
    GDLabel keyLabel = new GDLabel(key + ":");
    keyLabel.setFont(keyLabel.getFont().deriveFont(Font.BOLD));
    detailsPanel.add(keyLabel);
    detailsPanel.add(new GDLabel(value));
  }

  /**
   * Normalizes empty textual values for display.
   *
   * @param value raw text value
   * @return original value or "(not set)" for blank/null input
   */
  private static String normalized(String value) {
    if (value == null || value.isBlank()) {
      return "(not set)";
    }
    return value;
  }

  /**
   * Formats a long value as uppercase hexadecimal with 0x prefix.
   *
   * @param value value to format
   * @return hexadecimal string
   */
  private static String formatHex(long value) {
    return String.format("0x%X", value);
  }

  /**
   * Formats a size as decimal bytes and hexadecimal representation.
   *
   * @param value size in bytes
   * @return formatted size string
   */
  private static String formatBytes(long value) {
    return String.format("%d bytes (%s)", value, formatHex(value));
  }
}
