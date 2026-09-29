/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.common;

/**
 * Canonical address window inside each SNES bank.
 *
 * <p>This is intentionally aligned with ROM mirror terminology used by the UI:
 * FULL ($0000-$FFFF), LOW ($0000-$7FFF), HIGH ($8000-$FFFF).
 *
 * <p>The enum is shared by canonical ROM mapping metadata ({@link BankRange})
 * and mirror UI constraints so both layers use the same vocabulary.
 */
public enum BankWindow {
  /** Complete bank window: $0000-$FFFF (64 KiB). */
  FULL(0x0000, 0x10000),
  /** Lower half window: $0000-$7FFF (32 KiB). */
  LOW(0x0000, 0x8000),
  /** Upper half window: $8000-$FFFF (32 KiB). */
  HIGH(0x8000, 0x8000);

  private final int startAddress;
  private final int size;

  BankWindow(int startAddress, int size) {
    this.startAddress = startAddress;
    this.size = size;
  }

  /**
   * Returns the first CPU-visible address for this window inside one bank.
   */
  public int startAddress() {
    return startAddress;
  }

  /**
   * Returns the mapped window size, in bytes, for one bank.
   */
  public int size() {
    return size;
  }

  /**
   * Returns the inclusive end address within a bank for this window.
   */
  public int endAddressInclusive() {
    return startAddress + size - 1;
  }
}
