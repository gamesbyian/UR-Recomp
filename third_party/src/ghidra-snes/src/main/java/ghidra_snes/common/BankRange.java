/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.common;

/**
 * Canonical ROM mapping definition for a contiguous bank range.
 *
 * <p>A {@link RomMapType} typically combines one or more of these ranges to
 * describe where canonical ROM data is visible in CPU address space.
 *
 * @param startBank first bank index (inclusive)
 * @param endBank last bank index (inclusive)
 * @param window bank-local address window (FULL/LOW/HIGH)
 * @param fileSkip bytes skipped before each chunk read from ROM file
 */
public record BankRange(int startBank, int endBank, BankWindow window, int fileSkip) {
  public BankRange(int startBank, int endBank, BankWindow window) {
    this(startBank, endBank, window, 0);
  }

  /**
   * Returns the number of banks in this range.
   */
  public int bankCount() {
    return (endBank - startBank) + 1;
  }

  /**
   * Returns mapped bytes per bank for this range.
   */
  public int chunkSize() {
    return window.size();
  }

  /**
   * Returns the inclusive end address for the mapped window in each bank.
   */
  public int addressEndInclusive() {
    return window.endAddressInclusive();
  }
}
