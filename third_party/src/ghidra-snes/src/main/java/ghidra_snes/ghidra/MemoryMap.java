/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ghidra;

import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Program;
import ghidra_snes.common.BankRange;
import ghidra_snes.common.BankWindow;
import ghidra_snes.common.RomMapType;
import ghidra_snes.common.SnesRomHeader;
import ghidra_snes.common.cart.RomMirrorPolicy;
import ghidra_snes.common.registers.Mmio;
import java.util.List;

public class MemoryMap {
  /**
   * Canonical SNES system region definition.
   *
   * <p>These regions represent the CPU-visible internal SNES areas mirrored
   * across banks 00-3F and 80-BF.
   */
  public record SystemRegion(String bankName, String name, long start, long size) {}

  /**
   * Canonical SNES system regions.
   *
   * <p>The canonical mapping always lives in bank 00. Mirror blocks are later
   * generated into the visible CPU banks.
   */
  public static final List<SystemRegion> SYSTEM_REGIONS = List.of(
      new SystemRegion("snes_low_ram", "SNES Low RAM", 0x0, 0x2000),
      new SystemRegion("snes_io", "SNES I/O", 0x2000, 0x4000)
    );

  /**
   * Creates the canonical SNES system regions in bank $00.
   *
   * <p>This creates the base low RAM and I/O blocks used by all mirrored system
   * views.
   *
   * @param program the current program
   * @return number of blocks created
   */
  public static int createBlockSystemRegion(Program program) throws Exception {
    int created = 0;

    for (SystemRegion memoryRegion : SYSTEM_REGIONS) {
      created +=
          MemoryMapUtils.ensureUninitializedBlock(
              program,
              memoryRegion.bankName(),
              memoryRegion.start(),
              memoryRegion.size(),
              "SNES:Canonical",
              String.format("%s at 0x%06x", memoryRegion.name(), memoryRegion.start()));
    }
    Mmio.createMmioLabels(program, 0x0);

    return created;
  }

  /**
   * Creates mirrored SNES system region blocks for one visible CPU bank.
   *
   * <p>The canonical regions remain mapped in bank 00 while visible banks expose
   * mapped mirrors pointing back to the canonical blocks. Banks outside the SNES
   * system mirror ranges are ignored.
   *
   * @param program the current program
   * @param bank bank to expose
   * @return number of blocks created
   */
  public static int createBlockSystemRegionMirrors(Program program, int bank) throws Exception {
    if (bank == 0x00) {
      return createBlockSystemRegion(program);
    }
    if (!MemoryMapUtils.isSystemBank(bank)) {
      return 0;
    }

    int created = 0;

    for (SystemRegion memoryRegion : SYSTEM_REGIONS) {
      long canonicalStart = memoryRegion.start();
      long bankedStart = ((long) bank << 16) | (canonicalStart & 0xffff);
      Address mappedAddress =
          program.getAddressFactory().getDefaultAddressSpace().getAddress(canonicalStart);

      created +=
          MemoryMapUtils.ensureMappedBlock(
              program,
              "bank_%02x_%s_mirror".formatted(bank, memoryRegion.bankName()),
              bankedStart,
              mappedAddress,
              memoryRegion.size(),
              "SNES:Mirror",
              "Mirror of %s at 0x%06x".formatted(memoryRegion.name(), bankedStart));
    }
    Mmio.createMmioLabels(program, bank);

    return created;
  }


  /**
   * Creates the main SNES WRAM memory block ($7E–$7F) if missing.
   *
   * The block is created as uninitialized, read/write, non-executable memory.
   *
   * @param program the current program
   * @return 1 if created, 0 if already present
   */
  public static int createBlockWram(Program program) throws Exception {
    return MemoryMapUtils.ensureUninitializedBlock(
        program, "snes_wram", 0x7e0000, 0x20000, "SNES:Canonical", "SNES WRAM at 0x7e0000");
  }

  /**
   * Creates high-half ROM mirror blocks for the detected ROM mapping type.
   *
   * <p>The loader maps ROM into a canonical ROM view. This method exposes
   * additional CPU-visible {@code 8000-FFFF} aliases as mapped blocks, skipping
   * banks that are protected or not part of the high-half ROM mirror for the
   * given mapping type.
   *
   * <p>For LoROM, this maps {@code $00-$7D:8000-FFFF} to
   * {@code $80-$FD:8000-FFFF}. For HiROM, this maps {@code $00-$3F:8000-FFFF} to
   * {@code $C0-$FF:8000-FFFF}. ExHiROM uses the same high-half mirror rule as
   * HiROM for now.
   *
   * @param program the current program
   * @param romMapType detected ROM mapping type
   * @param romHeader detected ROM header, used to anchor bank `$00` mirrors
   * @param maxBank highest mirror bank to expose
   * @return number of blocks created
   */
  public static int createBlockHighHalfRomMirrors(Program program, RomMapType romMapType, SnesRomHeader romHeader, int maxBank)
      throws Exception {
    int created = 0;
    int lastBank = Math.max(0x00, Math.min(maxBank, 0xff));

    for (int bank = 0x00; bank <= lastBank; bank++) {
      Long canonicalStart = canonicalRomMirrorStart(romMapType, romHeader, bank);
      if (canonicalStart == null) {
        continue;
      }

      long mirrorStart = ((long) bank << 16) | 0x8000L;
      Address mappedAddress =
          program.getAddressFactory().getDefaultAddressSpace().getAddress(canonicalStart);

      created +=
          MemoryMapUtils.ensureMappedBlock(
              program,
              "bank_%02x_rom_mirror".formatted(bank),
              mirrorStart,
              mappedAddress,
              0x8000,
              "Mirror",
              "Mirror of ROM at 0x%06x".formatted(canonicalStart));
    }

    return created;
  }

  /**
   * Creates ROM mirror mapped blocks for one source/target selection.
   *
   * <p>Each created target bank maps to a canonical ROM source bank with the
   * same in-window offset. Existing/conflicting blocks are skipped.
   *
   * @param program active program receiving mapped blocks
   * @param sourceRange selected canonical source range and window
   * @param targetRange selected target range and window
   * @return number of mapped blocks created
   */
  public static int createBlockRomMirrors(
      Program program, BankRange sourceRange, BankRange targetRange) throws Exception {
    int created = 0;
    String windowSuffix = mirrorWindowSuffix(targetRange.window());

    for (RomMirrorPolicy.MirrorMapping mapping : RomMirrorPolicy.buildPlan(sourceRange, targetRange)) {
      Address mappedAddress =
          program.getAddressFactory().getDefaultAddressSpace().getAddress(mapping.sourceStart());

      created +=
          MemoryMapUtils.ensureMappedBlock(
              program,
              "bank_%02x_rom_%s_mirror".formatted(mapping.targetBank(), windowSuffix),
              mapping.targetStart(),
              mappedAddress,
              mapping.size(),
              "SNES:Mirror",
              "ROM mirror of 0x%06x at 0x%06x"
                  .formatted(mapping.sourceStart(), mapping.targetStart()));
    }

    return created;
  }

  /**
   * Resolves the canonical ROM source address for a high-half mirror bank.
   *
   * <p>This converts a CPU-visible {@code 8000-FFFF} ROM mirror bank into the
   * corresponding canonical high-half ROM address.
   *
   * @param romMapType detected ROM mapping type
   * @param romHeader detected ROM header, used to anchor bank `$00` mirrors
   * @param bank mirror bank index
   * @return canonical ROM address, or null if the bank is not mirrored
   */
  static Long canonicalRomMirrorStart(
      RomMapType romMapType, SnesRomHeader romHeader, int bank) {
    if (bank == 0x00) {
      return firstBankMirrorStart(romMapType, romHeader);
    }

    return switch (romMapType) {
      case LoROM -> {
        if (bank >= 0x01 && bank <= 0x7d) {
          yield 0x800000L + ((long) bank << 16) + 0x8000L;
        }
        yield null;
      }
      case HiROM, ExHiROM, SA_1, SPC7110, S_DD1 -> {
        if (bank >= 0x01 && bank <= 0x3f) {
          yield 0xc00000L + ((long) bank << 16) + 0x8000L;
        }
        yield null;
      }
      case UNKNOWN -> null;
    };
  }

  /**
   * Resolves the canonical source for the CPU-visible first ROM mirror at
   * {@code $00:8000-$FFFF}.
   *
   * <p>The first mirror must contain the detected internal ROM header at
   * {@code $00:FFC0-$00:FFFF}. This method returns the canonical memory address
   * that backs that visible mirror, not the raw ROM file offset.
   *
   * <p>This matters for enhancement-chip cartridges: SA-1 and S-DD1 commonly
   * keep their header at the LoROM header location while their canonical ROM
   * view is HiROM-like.
   */
  static long firstBankMirrorStart(RomMapType romMapType, SnesRomHeader romHeader) {
    if (romHeader.location() == SnesRomHeader.LOROM_HEADER_OFFSET - 1) {
      return switch (romMapType) {
        case LoROM -> 0x808000L;
        case HiROM, ExHiROM, SA_1, SPC7110, S_DD1 -> 0xc00000L;
        case UNKNOWN -> 0x808000L;
      };
    }

    if (romHeader.location() == SnesRomHeader.HIROM_HEADER_OFFSET - 1) {
      return 0xc08000L;
    }

    if (romHeader.location() == SnesRomHeader.EXHIROM_HEADER_OFFSET - 1) {
      return 0x408000L;
    }

    return romHeader.location() - (SnesRomHeader.LOROM_HEADER_OFFSET - 1);
  }

  private static String mirrorWindowSuffix(BankWindow window) {
    return switch (window) {
      case LOW -> "low";
      case HIGH -> "high";
      case FULL -> "full";
    };
  }
}
