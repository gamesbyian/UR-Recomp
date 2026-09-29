/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.options.pages;

import docking.widgets.MultiLineLabel;
import docking.widgets.button.GButton;
import docking.widgets.label.GDLabel;
import ghidra.program.model.listing.Program;
import ghidra.util.Msg;
import ghidra.util.layout.VerticalLayout;
import ghidra_snes.ghidra.MemoryMap;
import ghidra_snes.ghidra.MemoryMapUtils;
import ghidra_snes.ui.components.SystemBankRangeSlider;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.util.ArrayList;
import java.util.List;
import javax.swing.BorderFactory;
import javax.swing.JComponent;
import javax.swing.JPanel;

public final class SystemBanksPage extends JPanel {
  private static final int BANK_MIN = 0x00;
  private static final int BANK_MAX = 0xbf;
  private static final int FORBIDDEN_MIN = 0x40;
  private static final int FORBIDDEN_MAX = 0x7f;

  private static final String PAGE_TITLE = "Generate System Bank Mirrors in Memory Map";

  private final Program currentProgram;

  private final SystemBankRangeSlider rangeSlider =
    new SystemBankRangeSlider(BANK_MIN, BANK_MAX, FORBIDDEN_MIN, FORBIDDEN_MAX, BANK_MIN, BANK_MAX);
  private final GDLabel startBankValueLabel = new GDLabel();
  private final GDLabel endBankValueLabel = new GDLabel();
  private final MultiLineLabel previewLabel = new MultiLineLabel();
  private final MultiLineLabel resultLabel = new MultiLineLabel();
  private final JPanel infoSection = new JPanel(new BorderLayout());
  private final GButton generateButton = new GButton("Generate missing mirrors");

  /**
   * Builds the System Banks page and wires range selection/generation actions.
   *
   * @param currentProgram active program that will receive mirror block creation
   */
  public SystemBanksPage(Program currentProgram) {
    super(new BorderLayout());
    this.currentProgram = currentProgram;

    setBorder(BorderFactory.createEmptyBorder(20, 24, 20, 24));

    JPanel content = new JPanel(new VerticalLayout(12));
    content.add(buildHeaderSection());
    content.add(buildBankRangeSection());
    content.add(buildPreviewSection());
    content.add(buildActionSection());
    content.add(buildInfoSection());

    add(content, BorderLayout.NORTH);

    bindListeners();
    refreshRangeAndPreview();

    if (currentProgram == null) {
      setInteractiveEnabled(false);
    }
  }

  /**
   * Builds the title and explanatory notice shown above controls.
   */
  private JComponent buildHeaderSection() {
    JPanel section = new JPanel(new VerticalLayout(6));

    GDLabel title = new GDLabel(PAGE_TITLE);
    title.setFont(title.getFont().deriveFont(Font.BOLD, 20f));

    MultiLineLabel notice = new MultiLineLabel(
      "Create mirrored views for SNES system ROM banks.\n"
        + "Banks $40-$7F are never generated (hardware range).");
    notice.setAlignment(MultiLineLabel.LEFT);

    section.add(title);
    section.add(notice);
    return section;
  }

  /**
   * Builds the bank-range block with value labels and two-thumb slider.
   */
  private JComponent buildBankRangeSection() {
    JPanel section = new JPanel(new VerticalLayout(4));
    section.setBorder(BorderFactory.createCompoundBorder(
      BorderFactory.createTitledBorder("Bank range"),
      BorderFactory.createEmptyBorder(8, 10, 4, 10)));

    JPanel valuesPanel = new JPanel(new BorderLayout(24, 0));
    valuesPanel.add(buildBankValueRow("Start bank:", startBankValueLabel), BorderLayout.WEST);
    valuesPanel.add(buildBankValueRow("End bank:", endBankValueLabel), BorderLayout.EAST);

    section.add(valuesPanel);
    section.add(rangeSlider);
    return section;
  }

  /**
   * Builds the preview block reflecting the effective bank ranges.
   */
  private JComponent buildPreviewSection() {
    JPanel section = new JPanel(new BorderLayout());
    section.setBorder(BorderFactory.createCompoundBorder(
      BorderFactory.createTitledBorder("Preview"),
      BorderFactory.createEmptyBorder(10, 10, 10, 10)));

    previewLabel.setAlignment(MultiLineLabel.LEFT);
    section.add(previewLabel, BorderLayout.CENTER);
    return section;
  }

  /**
   * Builds the action row with Help (disabled) and Generate button.
   */
  private JComponent buildActionSection() {
    JPanel section = new JPanel(new BorderLayout());

    GButton helpButton = new GButton("Help");
    helpButton.setEnabled(false);
    helpButton.setToolTipText("Coming later");

    generateButton.addActionListener(event -> generateMissingMirrors());

    section.add(helpButton, BorderLayout.WEST);
    section.add(generateButton, BorderLayout.EAST);
    return section;
  }

  /**
   * Builds the post-generation info block shown after the first run.
   */
  private JComponent buildInfoSection() {
    infoSection.setBorder(BorderFactory.createCompoundBorder(
      BorderFactory.createTitledBorder("Info"),
      BorderFactory.createEmptyBorder(10, 10, 10, 10)));
    resultLabel.setAlignment(MultiLineLabel.LEFT);
    infoSection.add(resultLabel, BorderLayout.CENTER);
    infoSection.setVisible(false);
    return infoSection;
  }

  /**
   * Wires page events.
   */
  private void bindListeners() {
    rangeSlider.addChangeListener(event -> refreshRangeAndPreview());
  }

  /**
   * Refreshes displayed range labels and preview text from slider state.
   */
  private void refreshRangeAndPreview() {
    startBankValueLabel.setText(formatBank(rangeSlider.getStartBank()));
    endBankValueLabel.setText(formatBank(rangeSlider.getEndBank()));
    updatePreview();
  }

  /**
   * Updates preview text with effective mirrored ranges and exclusions.
   */
  private void updatePreview() {
    List<Integer> selectedBanks = collectBanksForGeneration(rangeSlider.getStartBank(), rangeSlider.getEndBank());
    String previewText;

    if (selectedBanks.isEmpty()) {
      previewText = "No eligible mirror banks selected.";
    } else {
      previewText = "This will create Memory Map mappings for: " + describeRanges(selectedBanks) + ".";
    }

    previewText += "\nBanks $40-$7F are always skipped.";
    previewLabel.setLabel(previewText);
  }

  /**
   * Collects selected banks that are valid mirror targets.
   */
  private List<Integer> collectBanksForGeneration(int startBank, int endBank) {
    List<Integer> banks = new ArrayList<>();

    for (int bank = startBank; bank <= endBank; bank++) {
      if (!MemoryMapUtils.isSystemBank(bank)) {
        continue;
      }
      banks.add(bank);
    }

    return banks;
  }

  /**
   * Converts individual bank values into human-readable contiguous ranges.
   */
  private String describeRanges(List<Integer> banks) {
    if (banks.isEmpty()) {
      return "(none)";
    }

    List<String> ranges = new ArrayList<>();
    int rangeStart = banks.get(0);
    int previous = rangeStart;

    for (int index = 1; index < banks.size(); index++) {
      int bank = banks.get(index);
      if (bank == previous + 1) {
        previous = bank;
        continue;
      }

      ranges.add(formatRange(rangeStart, previous));
      rangeStart = bank;
      previous = bank;
    }

    ranges.add(formatRange(rangeStart, previous));
    return String.join(" and ", ranges);
  }

  /**
   * Runs mirror generation for the current range and shows completion feedback.
   */
  private void generateMissingMirrors() {
    if (currentProgram == null) {
      setResult("No active program.", ResultTone.WARNING);
      return;
    }

    List<Integer> banks =
      collectBanksForGeneration(rangeSlider.getStartBank(), rangeSlider.getEndBank());
    if (banks.isEmpty()) {
      setResult("No eligible banks in the selected range.", ResultTone.WARNING);
      return;
    }

    int createdMappings = 0;
    int banksWithCreatedMappings = 0;
    boolean success = false;
    int transactionId = currentProgram.startTransaction("Generate SNES system bank mirrors");

    try {
      for (int bank : banks) {
        int createdForBank = MemoryMap.createBlockSystemRegionMirrors(currentProgram, bank);
        createdMappings += createdForBank;
        if (createdForBank > 0) {
          banksWithCreatedMappings++;
        }
      }
      success = true;
    } catch (Exception exception) {
      setResult("Mirror generation failed. Check log for details.", ResultTone.ERROR);
      Msg.error(SystemBanksPage.class, "Unable to generate system bank mirrors.", exception);
      return;
    } finally {
      currentProgram.endTransaction(transactionId, success);
    }

    if (createdMappings > 0) {
      setResult(
        "Created " + createdMappings + " memory mapping" + pluralSuffix(createdMappings)
          + " across " + banksWithCreatedMappings + " bank" + pluralSuffix(banksWithCreatedMappings)
          + ".",
        ResultTone.SUCCESS);
      return;
    }

    setResult("No mirrors created (everything already present or out of range).", ResultTone.INFO);
  }

  /**
   * Enables/disables all interactive controls for this page.
   */
  private void setInteractiveEnabled(boolean enabled) {
    rangeSlider.setEnabled(enabled);
    generateButton.setEnabled(enabled);
  }

  /**
   * Updates the result message and tone in the info block.
   */
  private void setResult(String text, ResultTone tone) {
    if (!infoSection.isVisible()) {
      infoSection.setVisible(true);
      revalidate();
      repaint();
    }
    resultLabel.setLabel(text);
    Color toneColor = tone.color();
    if (tone == ResultTone.INFO) {
      toneColor = previewLabel.getForeground();
    }
    resultLabel.setForeground(toneColor);
  }

  /**
   * Builds one bank display row (label + value).
   */
  private JComponent buildBankValueRow(String label, GDLabel valueLabel) {
    JPanel row = new JPanel(new BorderLayout(8, 0));
    row.add(new GDLabel(label), BorderLayout.WEST);
    row.add(valueLabel, BorderLayout.CENTER);
    return row;
  }

  /**
   * Formats a bank number as two-digit uppercase hexadecimal.
   */
  private static String formatBank(int bank) {
    return String.format("$%02X", bank);
  }

  /**
   * Formats a contiguous bank range.
   */
  private static String formatRange(int start, int end) {
    if (start == end) {
      return formatBank(start);
    }
    return formatBank(start) + "-" + formatBank(end);
  }

  /**
   * Returns plural suffix for basic English labels based on count.
   */
  private static String pluralSuffix(int count) {
    return count == 1 ? "" : "s";
  }

  private enum ResultTone {
    INFO(new Color(65, 65, 65)),
    SUCCESS(new Color(30, 120, 40)),
    WARNING(new Color(170, 115, 10)),
    ERROR(new Color(170, 40, 40));

    private final Color color;

    ResultTone(Color color) {
      this.color = color;
    }

    Color color() {
      return color;
    }
  }
}
