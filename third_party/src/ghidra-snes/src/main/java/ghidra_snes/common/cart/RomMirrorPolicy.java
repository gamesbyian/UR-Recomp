/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.common.cart;

import ghidra_snes.common.BankRange;
import ghidra_snes.common.BankWindow;
import ghidra_snes.common.RomMapType;
import java.util.ArrayList;
import java.util.List;

/**
 * Explicit ROM mirror policy definitions used by the Options UI.
 *
 * <p>This keeps one simple source of truth:
 * canonical source range + selected source window -> allowed target ranges.
 */
public final class RomMirrorPolicy {
  private static final List<BankRange> RESERVED_TARGETS =
      List.of(
          new BankRange(0x00, 0x3f, BankWindow.LOW),
          new BankRange(0x80, 0xbf, BankWindow.LOW));

  private static final List<BankRange> HALF_TARGETS =
      List.of(
          new BankRange(0x00, 0x3f, BankWindow.HIGH),
          new BankRange(0x40, 0x7d, BankWindow.LOW),
          new BankRange(0x40, 0x7d, BankWindow.HIGH),
          new BankRange(0xc0, 0xff, BankWindow.LOW),
          new BankRange(0xc0, 0xff, BankWindow.HIGH));

  private static final List<BankRange> FULL_TARGETS =
      List.of(
          new BankRange(0x40, 0x7d, BankWindow.FULL),
          new BankRange(0xc0, 0xff, BankWindow.FULL));

  private RomMirrorPolicy() {}

  /**
   * One selectable mirror rule line.
   *
   * @param canonicalSource canonical source range from {@link RomMapType#ranges()}
   * @param sourceWindow selected source window used for mirroring
   * @param allowedTargets explicit allowed target ranges for this selection
   */
  public record Rule(BankRange canonicalSource, BankWindow sourceWindow, List<BankRange> allowedTargets) {
    /**
     * Constructs an immutable mirror rule.
     */
    public Rule {
      allowedTargets = List.copyOf(allowedTargets);
    }
  }

  /**
   * One concrete bank-level mapping produced from a source/target selection.
   *
   * @param sourceBank canonical source bank
   * @param targetBank target bank
   * @param sourceStart source CPU address
   * @param targetStart target CPU address
   * @param size mapped byte size
   */
  public record MirrorMapping(
      int sourceBank, int targetBank, long sourceStart, long targetStart, int size) {}

  /**
   * Returns fixed reserved zones that should never be selectable as targets.
   */
  public static List<BankRange> reservedTargets() {
    return RESERVED_TARGETS;
  }

  /**
   * Returns explicit mirror rules for the given ROM map type.
   */
  public static List<Rule> rulesFor(RomMapType romMapType) {
    List<BankRange> canonical = romMapType.ranges();
    List<Rule> rules = new ArrayList<>();

    switch (romMapType) {
      case LoROM -> {
        BankRange source = canonical.get(0);
        rules.add(new Rule(source, BankWindow.HIGH, HALF_TARGETS));
      }
      case HiROM, SA_1 -> {
        BankRange source = canonical.get(0);
        rules.add(new Rule(source, BankWindow.FULL, FULL_TARGETS));
        rules.add(new Rule(source, BankWindow.HIGH, HALF_TARGETS));
        rules.add(new Rule(source, BankWindow.LOW, HALF_TARGETS));
      }
      case ExHiROM, SPC7110, S_DD1 -> {
        BankRange source0 = canonical.get(0);
        BankRange source1 = canonical.get(1);
        BankRange source2 = canonical.get(2);

        rules.add(new Rule(source0, BankWindow.FULL, FULL_TARGETS));
        rules.add(new Rule(source0, BankWindow.HIGH, HALF_TARGETS));
        rules.add(new Rule(source0, BankWindow.LOW, HALF_TARGETS));

        rules.add(new Rule(source1, BankWindow.FULL, FULL_TARGETS));
        rules.add(new Rule(source1, BankWindow.HIGH, HALF_TARGETS));
        rules.add(new Rule(source1, BankWindow.LOW, HALF_TARGETS));

        rules.add(new Rule(source2, BankWindow.HIGH, HALF_TARGETS));
      }
      case UNKNOWN -> throw new IllegalStateException("Cannot define mirror rules for unknown ROM type");
    }

    return rules;
  }

  /**
   * Returns allowed targets for one explicit source selection.
   *
   * <p>The source match uses full {@link BankRange} equality (including
   * {@code fileSkip}), plus the selected {@link BankWindow}.
   */
  public static List<BankRange> targetsFor(
      RomMapType romMapType, BankRange canonicalSource, BankWindow sourceWindow) {
    for (Rule rule : rulesFor(romMapType)) {
      if (rule.canonicalSource().equals(canonicalSource) && rule.sourceWindow() == sourceWindow) {
        return rule.allowedTargets();
      }
    }

    return List.of();
  }

  /**
   * Builds bank-level mappings for a selected source range and target range.
   *
   * <p>When the target contains more banks than the source, source banks repeat cyclically.
   */
  public static List<MirrorMapping> buildPlan(BankRange sourceRange, BankRange targetRange) {
    int sourceBankCount = sourceRange.bankCount();
    int targetBankCount = targetRange.bankCount();
    int mappedSize = sourceRange.chunkSize();
    List<MirrorMapping> mappings = new ArrayList<>(targetBankCount);

    for (int targetOffset = 0; targetOffset < targetBankCount; targetOffset++) {
      int sourceBank = sourceRange.startBank() + (targetOffset % sourceBankCount);
      int targetBank = targetRange.startBank() + targetOffset;

      long sourceStart = ((long) sourceBank << 16) | (sourceRange.window().startAddress() & 0xffffL);
      long targetStart = ((long) targetBank << 16) | (targetRange.window().startAddress() & 0xffffL);
      mappings.add(new MirrorMapping(sourceBank, targetBank, sourceStart, targetStart, mappedSize));
    }

    return mappings;
  }
}
