/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.options.pages;

import docking.widgets.MultiLineLabel;
import docking.widgets.button.GButton;
import docking.widgets.label.GDLabel;
import ghidra.program.model.listing.Program;
import ghidra.util.Msg;
import ghidra.util.layout.VerticalLayout;
import ghidra_snes.common.BankRange;
import ghidra_snes.common.BankWindow;
import ghidra_snes.common.RomMapType;
import ghidra_snes.common.cart.RomMirrorPolicy;
import ghidra_snes.ghidra.MemoryMap;
import ghidra_snes.options.SnesOptions;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.swing.BorderFactory;
import javax.swing.JComponent;
import javax.swing.JComboBox;
import javax.swing.JPanel;

/**
 * Interactive UI for creating ROM mirror views from canonical SNES ROM ranges.
 */
public final class RomMirrorsPage extends JPanel {
  private static final long LOROM_BANK_CHUNK_SIZE = 0x8000L;
  private static final int LOROM_PRIMARY_SOURCE_BANK_COUNT = 64;

  private final Program currentProgram;
  private final RomMapType romMapType;
  private final List<RomMirrorPolicy.Rule> availableRules;
  private final Map<BankRange, List<RomMirrorPolicy.Rule>> rulesBySource = new LinkedHashMap<>();

  private final JComboBox<SourceBlockChoice> sourceBlockCombo = new JComboBox<>();
  private final JComboBox<BankWindowChoice> sourceWindowCombo = new JComboBox<>();
  private final JComboBox<TargetBlockChoice> targetBlockCombo = new JComboBox<>();
  private final JComboBox<BankWindowChoice> targetWindowCombo = new JComboBox<>();

  private final MultiLineLabel sourceSummaryLabel = new MultiLineLabel();
  private final MultiLineLabel targetSummaryLabel = new MultiLineLabel();
  private final MultiLineLabel previewLabel = new MultiLineLabel();
  private final MultiLineLabel romInfoLabel = new MultiLineLabel();
  private final MultiLineLabel canonicalBlocksLabel = new MultiLineLabel();
  private final MultiLineLabel reservedZonesLabel = new MultiLineLabel();
  private final MultiLineLabel validationLabel = new MultiLineLabel();
  private final MultiLineLabel resultLabel = new MultiLineLabel();

  private final JPanel resultSection = new JPanel(new BorderLayout());
  private final GButton createMirrorButton = new GButton("Create Mirror");

  private boolean updatingSelection;

  /**
   * Builds the ROM mirrors page.
   *
   * @param currentProgram active program used to read metadata and create mirrors
   */
  public RomMirrorsPage(Program currentProgram) {
    super(new BorderLayout());
    this.currentProgram = currentProgram;
    this.romMapType = resolveRomMapType(currentProgram);
    this.availableRules = resolveRules(currentProgram, romMapType);

    indexRulesByCanonicalSource();
    setBorder(BorderFactory.createEmptyBorder(20, 24, 20, 24));

    JPanel content = new JPanel(new VerticalLayout(12));
    content.add(buildHeaderSection());
    content.add(buildSelectionAndInfoSection());
    content.add(buildPreviewSection());
    content.add(buildActionSection());
    content.add(buildResultSection());

    add(content, BorderLayout.NORTH);

    bindListeners();
    populateSourceBlocks();
    refreshComputedSections();
    initializeReadOnlyInfo();

    if (currentProgram == null || availableRules.isEmpty()) {
      setInteractiveEnabled(false);
    }
  }

  /**
   * Builds the page title and short explanatory notice.
   */
  private JComponent buildHeaderSection() {
    JPanel section = new JPanel(new VerticalLayout(6));

    GDLabel title = new GDLabel("Create ROM Mirror View");
    title.setFont(title.getFont().deriveFont(Font.BOLD, 20f));

    MultiLineLabel notice =
        new MultiLineLabel(
            "Map a target region to an existing canonical region. "
                + "This adds a CPU-visible alias; no data is duplicated.");
    notice.setAlignment(MultiLineLabel.LEFT);

    section.add(title);
    section.add(notice);
    return section;
  }

  /**
   * Builds source/target selectors and read-only side information.
   */
  private JComponent buildSelectionAndInfoSection() {
    JPanel section = new JPanel(new BorderLayout(12, 0));
    section.add(buildSelectorsSection(), BorderLayout.CENTER);
    return section;
  }

  /**
   * Builds the two selection cards (source and target).
   */
  private JComponent buildSelectorsSection() {
    JPanel section = new JPanel(new java.awt.GridLayout(1, 2, 12, 0));
    section.add(buildSourceCard());
    section.add(buildTargetCard());
    return section;
  }

  /**
   * Builds the source canonical block card.
   */
  private JComponent buildSourceCard() {
    JPanel section = new JPanel(new VerticalLayout(8));
    section.setBorder(
        BorderFactory.createCompoundBorder(
            BorderFactory.createTitledBorder("1. Source (canonical)"),
            BorderFactory.createEmptyBorder(10, 10, 10, 10)));

    sourceSummaryLabel.setAlignment(MultiLineLabel.LEFT);

    section.add(new GDLabel("Canonical block (banks)"));
    section.add(sourceBlockCombo);
    section.add(new GDLabel("Window (address range)"));
    section.add(sourceWindowCombo);
    section.add(sourceSummaryLabel);

    return section;
  }

  /**
   * Builds the target mirror block card.
   */
  private JComponent buildTargetCard() {
    JPanel section = new JPanel(new VerticalLayout(8));
    section.setBorder(
        BorderFactory.createCompoundBorder(
            BorderFactory.createTitledBorder("2. Target (new mirror)"),
            BorderFactory.createEmptyBorder(10, 10, 10, 10)));

    targetSummaryLabel.setAlignment(MultiLineLabel.LEFT);

    section.add(new GDLabel("Target block (banks)"));
    section.add(targetBlockCombo);
    section.add(new GDLabel("Window (address range)"));
    section.add(targetWindowCombo);
    section.add(targetSummaryLabel);

    return section;
  }

  /**
   * Builds the mapping preview block.
   */
  private JComponent buildPreviewSection() {
    JPanel section = new JPanel(new BorderLayout());
    section.setBorder(
        BorderFactory.createCompoundBorder(
            BorderFactory.createTitledBorder("Preview"),
            BorderFactory.createEmptyBorder(10, 10, 10, 10)));

    previewLabel.setAlignment(MultiLineLabel.LEFT);
    section.add(previewLabel, BorderLayout.CENTER);
    return section;
  }

  /**
   * Builds action buttons.
   */
  private JComponent buildActionSection() {
    JPanel section = new JPanel(new BorderLayout());

    GButton helpButton = new GButton("Help");
    helpButton.setEnabled(false);
    helpButton.setToolTipText("Coming later");

    createMirrorButton.addActionListener(event -> createMirrorView());

    section.add(helpButton, BorderLayout.WEST);
    section.add(createMirrorButton, BorderLayout.EAST);
    return section;
  }

  /**
   * Builds the post-action result area.
   */
  private JComponent buildResultSection() {
    resultSection.setBorder(
        BorderFactory.createCompoundBorder(
            BorderFactory.createTitledBorder("Result"),
            BorderFactory.createEmptyBorder(10, 10, 10, 10)));
    resultLabel.setAlignment(MultiLineLabel.LEFT);
    resultSection.add(resultLabel, BorderLayout.CENTER);
    resultSection.setVisible(false);
    return resultSection;
  }

  /**
   * Wires combo selection changes to refresh logic.
   */
  private void bindListeners() {
    sourceBlockCombo.addActionListener(
        event -> {
          if (updatingSelection) {
            return;
          }
          populateSourceWindows();
          populateTargetBlocks();
          populateTargetWindows();
          refreshComputedSections();
        });

    sourceWindowCombo.addActionListener(
        event -> {
          if (updatingSelection) {
            return;
          }
          populateTargetBlocks();
          populateTargetWindows();
          refreshComputedSections();
        });

    targetBlockCombo.addActionListener(
        event -> {
          if (updatingSelection) {
            return;
          }
          populateTargetWindows();
          refreshComputedSections();
        });

    targetWindowCombo.addActionListener(
        event -> {
          if (updatingSelection) {
            return;
          }
          refreshComputedSections();
        });
  }

  /**
   * Reads immutable informational content (ROM info and block lists).
   */
  private void initializeReadOnlyInfo() {
    romInfoLabel.setLabel(buildRomInformationText());
    canonicalBlocksLabel.setLabel(buildCanonicalBlocksText());
    reservedZonesLabel.setLabel(buildReservedZonesText());
  }

  /**
   * Indexes mirror rules by canonical source range.
   */
  private void indexRulesByCanonicalSource() {
    rulesBySource.clear();

    for (RomMirrorPolicy.Rule rule : availableRules) {
      rulesBySource.computeIfAbsent(rule.canonicalSource(), key -> new ArrayList<>()).add(rule);
    }
  }

  /**
   * Populates canonical source block choices.
   */
  private void populateSourceBlocks() {
    updatingSelection = true;
    try {
      sourceBlockCombo.removeAllItems();

      for (BankRange sourceRange : rulesBySource.keySet()) {
        sourceBlockCombo.addItem(new SourceBlockChoice(sourceRange));
      }

      if (sourceBlockCombo.getItemCount() > 0) {
        sourceBlockCombo.setSelectedIndex(0);
      }

      populateSourceWindows();
      populateTargetBlocks();
      populateTargetWindows();
    } finally {
      updatingSelection = false;
    }
  }

  /**
   * Populates source window choices for the selected canonical block.
   */
  private void populateSourceWindows() {
    updatingSelection = true;
    try {
      sourceWindowCombo.removeAllItems();

      SourceBlockChoice sourceChoice = selectedSourceBlockChoice();
      if (sourceChoice == null) {
        return;
      }

      List<RomMirrorPolicy.Rule> sourceRules = rulesBySource.get(sourceChoice.range());
      if (sourceRules == null) {
        return;
      }

      Set<BankWindow> orderedWindows = new LinkedHashSet<>();
      for (RomMirrorPolicy.Rule rule : sourceRules) {
        orderedWindows.add(rule.sourceWindow());
      }

      for (BankWindow window : orderedWindows) {
        sourceWindowCombo.addItem(new BankWindowChoice(window));
      }

      if (sourceWindowCombo.getItemCount() > 0) {
        sourceWindowCombo.setSelectedIndex(0);
      }
    } finally {
      updatingSelection = false;
    }
  }

  /**
   * Populates target bank block choices for the currently selected source rule.
   */
  private void populateTargetBlocks() {
    updatingSelection = true;
    try {
      targetBlockCombo.removeAllItems();

      RomMirrorPolicy.Rule rule = selectedRule();
      if (rule == null) {
        return;
      }

      Set<TargetBlockChoice> targetBlocks = new LinkedHashSet<>();
      for (BankRange targetRange : rule.allowedTargets()) {
        targetBlocks.add(new TargetBlockChoice(targetRange.startBank(), targetRange.endBank()));
      }

      for (TargetBlockChoice blockChoice : targetBlocks) {
        targetBlockCombo.addItem(blockChoice);
      }

      if (targetBlockCombo.getItemCount() > 0) {
        targetBlockCombo.setSelectedIndex(0);
      }
    } finally {
      updatingSelection = false;
    }
  }

  /**
   * Populates target window choices for the selected target block.
   */
  private void populateTargetWindows() {
    updatingSelection = true;
    try {
      targetWindowCombo.removeAllItems();

      RomMirrorPolicy.Rule rule = selectedRule();
      TargetBlockChoice targetBlockChoice = selectedTargetBlockChoice();
      if (rule == null || targetBlockChoice == null) {
        return;
      }

      Set<BankWindow> windows = new LinkedHashSet<>();
      for (BankRange targetRange : rule.allowedTargets()) {
        if (targetRange.startBank() == targetBlockChoice.startBank()
            && targetRange.endBank() == targetBlockChoice.endBank()) {
          windows.add(targetRange.window());
        }
      }

      for (BankWindow window : windows) {
        targetWindowCombo.addItem(new BankWindowChoice(window));
      }

      if (targetWindowCombo.getItemCount() > 0) {
        targetWindowCombo.setSelectedIndex(0);
      }
    } finally {
      updatingSelection = false;
    }
  }

  /**
   * Refreshes summaries, preview, validation and button enablement.
   */
  private void refreshComputedSections() {
    refreshSourceSummary();
    refreshTargetSummary();
    refreshPreview();
    refreshValidation();

    createMirrorButton.setEnabled(
        currentProgram != null && selectedSourceRange() != null && selectedTargetRange() != null);
  }

  /**
   * Updates source summary text.
   */
  private void refreshSourceSummary() {
    BankRange sourceRange = selectedSourceRange();
    if (sourceRange == null) {
      sourceSummaryLabel.setLabel("Select a canonical source block and window.");
      return;
    }

    long sourceSize = (long) sourceRange.bankCount() * sourceRange.chunkSize();
    sourceSummaryLabel.setLabel(
        "Source size: "
            + formatSize(sourceSize)
            + " ("
            + sourceRange.bankCount()
            + " banks x "
            + formatSize(sourceRange.chunkSize())
            + ")\n"
            + "Backed by canonical mapping.");
  }

  /**
   * Updates target summary text.
   */
  private void refreshTargetSummary() {
    BankRange sourceRange = selectedSourceRange();
    BankRange targetRange = selectedTargetRange();

    if (sourceRange == null || targetRange == null) {
      targetSummaryLabel.setLabel("Select a target block and window.");
      return;
    }

    long targetSize = (long) targetRange.bankCount() * targetRange.chunkSize();
    String coverageLine;
    if (targetRange.bankCount() > sourceRange.bankCount()) {
      coverageLine =
          "Source banks will repeat cyclically ("
              + sourceRange.bankCount()
              + " -> "
              + targetRange.bankCount()
              + ").";
    } else {
      coverageLine = "Source and target banks map one-to-one.";
    }

    targetSummaryLabel.setLabel(
        "This will create "
            + targetRange.bankCount()
            + " mirrored banks ("
            + formatSize(targetSize)
            + ").\n"
            + coverageLine);
  }

  /**
   * Updates preview table-like text for selected mapping plan.
   */
  private void refreshPreview() {
    BankRange sourceRange = selectedSourceRange();
    BankRange targetRange = selectedTargetRange();
    if (sourceRange == null || targetRange == null) {
      previewLabel.setLabel("Select source and target values to preview mirror mappings.");
      return;
    }

    List<RomMirrorPolicy.MirrorMapping> plan = RomMirrorPolicy.buildPlan(sourceRange, targetRange);
    if (plan.isEmpty()) {
      previewLabel.setLabel("No mapping plan generated for current selection.");
      return;
    }

    StringBuilder builder = new StringBuilder();
    builder.append("Target window maps to canonical source with same offset.\n\n");
    builder.append("Target (CPU sees)            Maps to (canonical source)\n");

    appendPreviewRow(builder, plan.get(0));
    if (plan.size() > 1) {
      appendPreviewRow(builder, plan.get(1));
    }
    if (plan.size() > 3) {
      builder.append("...\n");
    }
    if (plan.size() > 2) {
      appendPreviewRow(builder, plan.get(plan.size() - 1));
    }

    builder
        .append("\nWindow: ")
        .append(describeWindowCompact(targetRange.window()))
        .append("\nTarget banks: ")
        .append(formatBankRange(targetRange.startBank(), targetRange.endBank()));

    previewLabel.setLabel(builder.toString());
  }

  /**
   * Updates validation text from selected source/target values.
   */
  private void refreshValidation() {
    BankRange sourceRange = selectedSourceRange();
    BankRange targetRange = selectedTargetRange();

    if (sourceRange == null || targetRange == null) {
      validationLabel.setLabel("Select source and target values.");
      return;
    }

    long sourceSize = (long) sourceRange.bankCount() * sourceRange.chunkSize();
    long targetSize = (long) targetRange.bankCount() * targetRange.chunkSize();

    StringBuilder builder = new StringBuilder();
    if (sourceRange.chunkSize() == targetRange.chunkSize()) {
      builder
          .append("[OK] Per-bank window size matches (")
          .append(formatSize(sourceRange.chunkSize()))
          .append(").\n");
    } else {
      builder.append("[ERROR] Source/target per-bank window sizes differ.\n");
    }

    if (targetRange.bankCount() > sourceRange.bankCount()) {
      builder
          .append("[INFO] Target uses repeated source banks (")
          .append(sourceRange.bankCount())
          .append(" source for ")
          .append(targetRange.bankCount())
          .append(" target).\n");
    } else if (targetRange.bankCount() < sourceRange.bankCount()) {
      builder
          .append("[INFO] Only first ")
          .append(targetRange.bankCount())
          .append(" source banks will be used.\n");
    } else {
      builder.append("[OK] One-to-one bank mapping.\n");
    }

    builder
        .append("[OK] Source view size: ")
        .append(formatSize(sourceSize))
        .append("\n")
        .append("[OK] Target view size: ")
        .append(formatSize(targetSize))
        .append("\n")
        .append("Ready to create mirror.");

    validationLabel.setLabel(builder.toString());
  }

  /**
   * Creates mapped ROM mirror blocks for the current selection.
   */
  private void createMirrorView() {
    if (currentProgram == null) {
      setResult("No active program.", ResultTone.WARNING);
      return;
    }

    BankRange sourceRange = selectedSourceRange();
    BankRange targetRange = selectedTargetRange();
    if (sourceRange == null || targetRange == null) {
      setResult("Source or target selection is incomplete.", ResultTone.WARNING);
      return;
    }

    int createdMappings;
    boolean success = false;
    int transactionId = currentProgram.startTransaction("Create SNES ROM mirrors");

    try {
      createdMappings = MemoryMap.createBlockRomMirrors(currentProgram, sourceRange, targetRange);
      success = true;
    } catch (Exception exception) {
      Msg.error(RomMirrorsPage.class, "Unable to create ROM mirror view.", exception);
      setResult("Mirror creation failed. Check log for details.", ResultTone.ERROR);
      return;
    } finally {
      currentProgram.endTransaction(transactionId, success);
    }

    if (createdMappings > 0) {
      setResult(
          "Created "
              + createdMappings
              + " memory mapping"
              + pluralSuffix(createdMappings)
              + " across "
              + createdMappings
              + " bank"
              + pluralSuffix(createdMappings)
              + ".",
          ResultTone.SUCCESS);
      return;
    }

    setResult("No mirrors created (already present or conflicting).", ResultTone.INFO);
  }

  /**
   * Updates post-action result text and tone.
   */
  private void setResult(String text, ResultTone tone) {
    if (!resultSection.isVisible()) {
      resultSection.setVisible(true);
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
   * Enables/disables all interactive controls.
   */
  private void setInteractiveEnabled(boolean enabled) {
    sourceBlockCombo.setEnabled(enabled);
    sourceWindowCombo.setEnabled(enabled);
    targetBlockCombo.setEnabled(enabled);
    targetWindowCombo.setEnabled(enabled);
    createMirrorButton.setEnabled(enabled);

    if (!enabled) {
      setResult("ROM mirror creation is unavailable for this program.", ResultTone.INFO);
    }
  }

  /**
   * Builds the ROM information text block.
   */
  private String buildRomInformationText() {
    if (currentProgram == null) {
      return "No active program.";
    }

    String mapper = SnesOptions.getCartMapper(currentProgram);
    long romSizeBytes = SnesOptions.getRomSizeBytes(currentProgram);
    long headerLocation = SnesOptions.getRomHeader(currentProgram).location();
    String metadataSource = SnesOptions.getMetadataSource(currentProgram);

    return "ROM Type: "
        + mapper
        + "\nROM Size: "
        + formatSizeDetailed(romSizeBytes)
        + "\nHeader Location: "
        + formatFlatAddress(headerLocation)
        + "\nMetadata: "
        + metadataSource;
  }

  /**
   * Builds the canonical block list text from current mapper metadata.
   */
  private String buildCanonicalBlocksText() {
    if (availableRules.isEmpty()) {
      return "No canonical source blocks available.";
    }

    StringBuilder builder = new StringBuilder();
    builder.append("Valid canonical sources:\n");

    int index = 1;
    for (BankRange canonicalSource : rulesBySource.keySet()) {
      long bytes = (long) canonicalSource.bankCount() * canonicalSource.chunkSize();
      builder
          .append(index)
          .append(") ")
          .append(formatBankRange(canonicalSource.startBank(), canonicalSource.endBank()))
          .append("  ")
          .append(describeWindowCompact(canonicalSource.window()))
          .append("  ")
          .append(formatSize(bytes))
          .append("\n");
      index++;
    }

    return builder.toString().trim();
  }

  /**
   * Builds reserved target zones text from policy definitions.
   */
  private String buildReservedZonesText() {
    StringBuilder builder = new StringBuilder();
    for (BankRange reservedRange : RomMirrorPolicy.reservedTargets()) {
      builder
          .append(formatBankRange(reservedRange.startBank(), reservedRange.endBank()))
          .append(" : ")
          .append(describeWindowCompact(reservedRange.window()))
          .append("\n");
    }
    builder.append("These areas should not be used as targets.");
    return builder.toString();
  }

  /**
   * Resolves selected mirror rule from source block/window selections.
   */
  private RomMirrorPolicy.Rule selectedRule() {
    SourceBlockChoice sourceChoice = selectedSourceBlockChoice();
    BankWindowChoice sourceWindowChoice = selectedSourceWindowChoice();

    if (sourceChoice == null || sourceWindowChoice == null) {
      return null;
    }

    List<RomMirrorPolicy.Rule> sourceRules = rulesBySource.get(sourceChoice.range());
    if (sourceRules == null) {
      return null;
    }

    for (RomMirrorPolicy.Rule rule : sourceRules) {
      if (rule.sourceWindow() == sourceWindowChoice.window()) {
        return rule;
      }
    }

    return null;
  }

  /**
   * Returns selected source range with effective selected source window.
   */
  private BankRange selectedSourceRange() {
    RomMirrorPolicy.Rule rule = selectedRule();
    if (rule == null) {
      return null;
    }

    BankRange canonicalSource = rule.canonicalSource();
    return new BankRange(
        canonicalSource.startBank(),
        canonicalSource.endBank(),
        rule.sourceWindow(),
        canonicalSource.fileSkip());
  }

  /**
   * Returns selected target range from selected target block/window.
   */
  private BankRange selectedTargetRange() {
    RomMirrorPolicy.Rule rule = selectedRule();
    TargetBlockChoice targetBlockChoice = selectedTargetBlockChoice();
    BankWindowChoice targetWindowChoice = selectedTargetWindowChoice();

    if (rule == null || targetBlockChoice == null || targetWindowChoice == null) {
      return null;
    }

    for (BankRange targetRange : rule.allowedTargets()) {
      if (targetRange.startBank() == targetBlockChoice.startBank()
          && targetRange.endBank() == targetBlockChoice.endBank()
          && targetRange.window() == targetWindowChoice.window()) {
        return targetRange;
      }
    }

    return null;
  }

  private SourceBlockChoice selectedSourceBlockChoice() {
    return (SourceBlockChoice) sourceBlockCombo.getSelectedItem();
  }

  private BankWindowChoice selectedSourceWindowChoice() {
    return (BankWindowChoice) sourceWindowCombo.getSelectedItem();
  }

  private TargetBlockChoice selectedTargetBlockChoice() {
    return (TargetBlockChoice) targetBlockCombo.getSelectedItem();
  }

  private BankWindowChoice selectedTargetWindowChoice() {
    return (BankWindowChoice) targetWindowCombo.getSelectedItem();
  }

  private static RomMapType resolveRomMapType(Program currentProgram) {
    if (currentProgram == null) {
      return RomMapType.UNKNOWN;
    }

    String mapper = SnesOptions.getCartMapper(currentProgram);
    try {
      return RomMapType.valueOf(mapper);
    } catch (Exception ignored) {
      return RomMapType.UNKNOWN;
    }
  }

  /**
   * Resolves mirror rules for the current program and mapper.
   *
   * <p>LoROM exposes one canonical source for <=64 high-half banks ($80-$BF).
   * When ROM size exceeds 64 banks, a second source ($C0-$FF) is exposed.
   */
  private static List<RomMirrorPolicy.Rule> resolveRules(Program currentProgram, RomMapType romMapType) {
    if (romMapType == RomMapType.UNKNOWN) {
      return List.of();
    }

    List<RomMirrorPolicy.Rule> baseRules = RomMirrorPolicy.rulesFor(romMapType);
    if (romMapType != RomMapType.LoROM || currentProgram == null) {
      return baseRules;
    }

    long romSizeBytes = Math.max(0L, SnesOptions.getRomSizeBytes(currentProgram));
    long loromBankCount = Math.ceilDiv(romSizeBytes, LOROM_BANK_CHUNK_SIZE);
    if (loromBankCount <= LOROM_PRIMARY_SOURCE_BANK_COUNT) {
      return baseRules;
    }

    boolean alreadyHasUpperSource =
        baseRules.stream()
            .anyMatch(
                rule ->
                    rule.canonicalSource().startBank() == 0xc0
                        && rule.canonicalSource().endBank() == 0xff
                        && rule.sourceWindow() == BankWindow.HIGH);
    if (alreadyHasUpperSource) {
      return baseRules;
    }

    List<RomMirrorPolicy.Rule> rules = new ArrayList<>(baseRules);
    for (RomMirrorPolicy.Rule rule : baseRules) {
      BankRange source = rule.canonicalSource();
      if (source.startBank() == 0x80 && source.endBank() == 0xbf && rule.sourceWindow() == BankWindow.HIGH) {
        BankRange upperHalfSource = new BankRange(0xc0, 0xff, BankWindow.HIGH, source.fileSkip());
        rules.add(new RomMirrorPolicy.Rule(upperHalfSource, rule.sourceWindow(), rule.allowedTargets()));
      }
    }

    return rules;
  }

  private static void appendPreviewRow(
      StringBuilder builder, RomMirrorPolicy.MirrorMapping mapping) {
    builder
        .append(formatBankAddressRange(mapping.targetStart(), mapping.size()))
        .append("  ->  ")
        .append(formatBankAddressRange(mapping.sourceStart(), mapping.size()))
        .append("\n");
  }

  private static String formatBankAddressRange(long startAddress, int size) {
    long endAddress = startAddress + size - 1L;
    return formatFlatAddress(startAddress) + "-" + formatFlatAddress(endAddress);
  }

  private static String formatFlatAddress(long address) {
    int bank = (int) ((address >> 16) & 0xff);
    int offset = (int) (address & 0xffff);
    return String.format("$%02X:%04X", bank, offset);
  }

  private static String formatBankRange(int startBank, int endBank) {
    return "$%02X-$%02X".formatted(startBank, endBank);
  }

  private static String describeWindowCompact(BankWindow window) {
    return switch (window) {
      case LOW -> "$0000-$7FFF";
      case HIGH -> "$8000-$FFFF";
      case FULL -> "$0000-$FFFF";
    };
  }

  private static String describeWindowLabel(BankWindow window) {
    return switch (window) {
      case LOW -> "Low: $0000-$7FFF (32 KB)";
      case HIGH -> "High: $8000-$FFFF (32 KB)";
      case FULL -> "Full: $0000-$FFFF (64 KB)";
    };
  }

  private static String formatSizeDetailed(long bytes) {
    return formatSize(bytes) + " (" + bytes + " bytes)";
  }

  private static String formatSize(long bytes) {
    if (bytes >= 1024L * 1024L) {
      return "%.2f MB".formatted(bytes / (1024.0 * 1024.0));
    }
    if (bytes >= 1024L) {
      return "%.2f KB".formatted(bytes / 1024.0);
    }
    return bytes + " B";
  }

  private static String pluralSuffix(int count) {
    return count == 1 ? "" : "s";
  }

  private record SourceBlockChoice(BankRange range) {
    @Override
    public String toString() {
      return formatBankRange(range.startBank(), range.endBank()) + " (" + range.bankCount() + " banks)";
    }
  }

  private record TargetBlockChoice(int startBank, int endBank) {
    @Override
    public String toString() {
      return formatBankRange(startBank, endBank) + " (" + ((endBank - startBank) + 1) + " banks)";
    }
  }

  private record BankWindowChoice(BankWindow window) {
    @Override
    public String toString() {
      return describeWindowLabel(window);
    }
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
