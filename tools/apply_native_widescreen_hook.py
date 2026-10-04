#!/usr/bin/env python3
"""Apply the accepted +8 hook plus host-owned random-access Widescreen capacity.

Generated code is ROM-derived and is intentionally not committed. This injector
is the durable source: it fails closed unless the exact accepted preparation
and live preparation boundaries are present.

Runtime contract:
  no Widescreen env          -> untouched stock behavior
  URRECOMP_WS_VIEW=authentic-16x9
                             -> accepted Authentic policy binding, resolved to +48
  URRECOMP_WS_VIEW=authentic-16x9-candidate
                             -> compatibility alias for authentic-16x9
  URRECOMP_WS_MARGIN=8       -> accepted one adjacent future horizontal strip;
                               in split-screen, one 8-word strip per viewport
  URRECOMP_WS_MARGIN=16      -> same accepted guest strip plus one host-owned
                               strip materialized from live course tables
  URRECOMP_WS_MARGIN=24..72  -> same accepted guest strip plus N host-owned
                               strips materialized from live course tables
  URRECOMP_WS_MARGIN always wins when explicitly supplied; unknown view names
  fail closed to stock margin 0.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MARKER = "UR-Recomp native Widescreen +8 strip hook"
TRACE_RE = re.compile(r"cpu_trace_block\(cpu,\s*0x([0-9A-Fa-f]+)\s*\);")

A59E_CALLEE_RE = re.compile(r"(?P<callee>bank_[0-9A-Fa-f]{2}_A59E_M0X0)\(cpu\)")

PCS = {
    "wrapper_after_first_helper": 0x01A59A,
    "wrapper_after_descriptor_builder": 0x01A59D,
}

SUPPORT = r'''
/* UR-Recomp native Widescreen +8 strip hook.
 *
 * This mirrors the accepted PR #219 diagnostic contract but removes all
 * guest-visible side effects from the extra helper execution. The second
 * stock A59E pass runs against a complete CPU + low-WRAM snapshot. We then
 * restore that snapshot and retain only:
 *   - the future 32-byte strip at $0453;
 *   - the secondary horizontal edge/count pair $0509/$052F until AB88 reads it.
 * $0453 remains live through the intervening NMI and is restored at the next
 * live A59A preparation boundary, before another secondary strip is staged.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int ur_ws_native_margin_cache = -32768;
static int ur_ws_native_trace_cache = -1;
static int ur_ws_native_second_pass = 0;
static int ur_ws_native_payload_live = 0;
static unsigned ur_ws_native_shadow_live_count = 0;
static CpuState ur_ws_native_cpu_snapshot;
static uint8 ur_ws_native_low_wram_snapshot[0x2000];
static uint8 ur_ws_native_future_payload[32];
static uint8 ur_ws_native_vs_p1_future_payload[16];
static uint8 ur_ws_native_vs_p2_future_payload[16];
static uint16 ur_ws_native_vs_p1_payload_addr = 0;
static uint16 ur_ws_native_vs_p2_payload_addr = 0;
static unsigned ur_ws_native_vs_p1_payload_len = 0;
static unsigned ur_ws_native_vs_p2_payload_len = 0;
static int ur_ws_native_vs_payload_live = 0;
static uint8 ur_ws_native_vs_shadow_payload[2][16];
static uint16 ur_ws_native_vs_shadow_edge[2];
static int ur_ws_native_vs_materializer_match[2];
#define UR_WS_NATIVE_MAX_HOST_COLUMNS 8u
static uint8 ur_ws_native_shadow_payload[UR_WS_NATIVE_MAX_HOST_COLUMNS][32];
static uint16 ur_ws_native_shadow_edge[UR_WS_NATIVE_MAX_HOST_COLUMNS];
static uint16 ur_ws_native_shadow_count[UR_WS_NATIVE_MAX_HOST_COLUMNS];

static int ur_ws_native_margin(void) {
  if (ur_ws_native_margin_cache == -32768) {
    const char *margin = getenv("URRECOMP_WS_MARGIN");
    if (margin && *margin) {
      ur_ws_native_margin_cache = atoi(margin);
    } else {
      const char *view = getenv("URRECOMP_WS_VIEW");
      ur_ws_native_margin_cache =
          (view && (strcmp(view, "authentic-16x9") == 0 ||
                    strcmp(view, "authentic-16x9-candidate") == 0)) ? 48 : 0;
    }
  }
  return ur_ws_native_margin_cache;
}

static int ur_ws_native_trace(void) {
  if (ur_ws_native_trace_cache < 0) {
    const char *s = getenv("URRECOMP_WS_NATIVE_TRACE");
    ur_ws_native_trace_cache = (s && *s && strcmp(s, "0") != 0) ? 1 : 0;
  }
  return ur_ws_native_trace_cache;
}

static uint16 ur_ws_native_read16(CpuState *cpu, uint16 addr) {
  return (uint16)(cpu->ram[addr] | ((uint16)cpu->ram[(uint16)(addr + 1)] << 8));
}

static void ur_ws_native_write16(CpuState *cpu, uint16 addr, uint16 value) {
  cpu->ram[addr] = (uint8)(value & 0xff);
  cpu->ram[(uint16)(addr + 1)] = (uint8)(value >> 8);
}

static uint16 ur_ws_native_snapshot_read16(uint16 addr) {
  return (uint16)(ur_ws_native_low_wram_snapshot[addr] |
                  ((uint16)ur_ws_native_low_wram_snapshot[(uint16)(addr + 1)] << 8));
}

static void ur_ws_native_trace_primary(CpuState *cpu) {
  const uint16 edge = ur_ws_native_read16(cpu, 0x0505);
  const uint16 count = ur_ws_native_read16(cpu, 0x052b);
  if (!ur_ws_native_trace() || edge == 0xffff || count != 16)
    return;
  fprintf(stderr, "URWS_PRIMARY margin=%d camx=%u edge=%04X count=%u payload=",
          ur_ws_native_margin(),
          (unsigned)ur_ws_native_read16(cpu, 0x0419),
          (unsigned)edge, (unsigned)count);
  for (unsigned j = 0; j < 32; j++)
    fprintf(stderr, "%02X", (unsigned)cpu->ram[0x0433 + j]);
  fprintf(stderr, " camy=%u edgey=%04X county=%u\n",
          (unsigned)ur_ws_native_read16(cpu, 0x041d),
          (unsigned)ur_ws_native_read16(cpu, 0x050d),
          (unsigned)ur_ws_native_read16(cpu, 0x0533));
}

static uint16 ur_ws_native_read16_bank(CpuState *cpu, uint8 bank, uint16 addr) {
  return cpu_read16(cpu, bank, addr);
}

static int ur_ws_native_vertical_fine_y(CpuState *cpu) {
  const uint16 camy = ur_ws_native_read16(cpu, 0x041d);
  const uint16 approx = (uint16)((camy + 4u) >> 4);
  const uint16 edgey = ur_ws_native_read16(cpu, 0x050d);
  const uint16 county = ur_ws_native_read16(cpu, 0x0533);
  if (edgey == 0xffff || county == 0)
    return (int)(camy >> 4);

  const uint16 phase = (uint16)(((edgey & 0x001fu) + 2u) & 0x001fu);
  int candidate = (int)((approx & 0xffe0u) | phase);
  while (candidate - (int)approx > 16)
    candidate -= 32;
  while ((int)approx - candidate > 16)
    candidate += 32;
  return candidate;
}

static int ur_ws_native_vs_vertical_fine_y(CpuState *cpu, unsigned player) {
  const uint16 camy = ur_ws_native_read16(cpu, player ? 0x041f : 0x041d);
  const uint16 edgey = ur_ws_native_read16(cpu, player ? 0x050f : 0x050d);
  const uint16 county =
      (uint16)(ur_ws_native_read16(cpu, player ? 0x0535 : 0x0533) +
               ur_ws_native_read16(cpu, player ? 0x0539 : 0x0537));
  if (edgey == 0xffff || county == 0)
    return (int)(camy >> 4);

  const uint16 phase = (uint16)(((edgey & 0x001fu) + 2u) & 0x001fu);
  const uint16 approx = (uint16)((camy + 4u) >> 4);
  int candidate = (int)((approx & 0xffe0u) | phase);
  while (candidate - (int)approx > 16)
    candidate -= 32;
  while ((int)approx - candidate > 16)
    candidate += 32;
  return candidate;
}

/* Split-screen uses 8-word vertical strips. Depth 0 reproduces the accepted
 * second A59E pass from the exact direction-dependent source coordinate;
 * depth 1 is the first host-owned deeper course column. The accepted +8
 * payload calibrates this live-course materializer in the same frame before
 * any deeper column is admitted as evidence. */
static int ur_ws_native_vs_column_from_course_adjusted(
    CpuState *cpu, unsigned player, int depth, int y_adjust,
    uint8 out[16]) {
  const uint16 camx = ur_ws_native_read16(cpu, player ? 0x041b : 0x0419);
  const int16 velocity =
      (int16)ur_ws_native_read16(cpu, player ? 0x04f7 : 0x04f5);
  const uint16 coarse_width = ur_ws_native_read16(cpu, 0x04f1);
  const uint16 coarse_height = ur_ws_native_read16(cpu, 0x04f3);
  const uint16 world_mask = ur_ws_native_read16(cpu, 0x0d49);
  if (!coarse_width || !coarse_height || velocity == 0)
    return 0;

  /* A59E's split-screen horizontal payload path is direction-dependent.
   * Positive motion prepares from cameraX + $0100 (wrapped by $0D49);
   * negative motion prepares from cameraX. B27F then samples the 16-pixel
   * course cell derived from that coordinate. Deeper host capacity advances
   * one live course column farther in the same motion direction. */
  uint16 source_px = camx;
  if (velocity > 0)
    source_px = (uint16)((camx + 0x0100u) & world_mask);

  const int fine_width = (int)coarse_width * 4;
  const int fine_height = (int)coarse_height * 4;
  int fine_x = (int)(source_px >> 4) + (velocity > 0 ? depth : -depth);
  while (fine_x < 0)
    fine_x += fine_width;
  while (fine_x >= fine_width)
    fine_x -= fine_width;

  const int fine_y0 = ur_ws_native_vs_vertical_fine_y(cpu, player) + y_adjust;

  for (unsigned j = 0; j < 8; j++) {
    const int fine_y = fine_y0 + (int)j;
    uint16 word = 0;
    if (fine_y >= 0 && fine_y < fine_height) {
      const uint16 sector_x = (uint16)(fine_x >> 2);
      const uint16 sector_y = (uint16)(fine_y >> 2);
      const uint32 coarse_index =
          (uint32)sector_y * (uint32)coarse_width + (uint32)sector_x;
      const uint16 record = ur_ws_native_read16_bank(
          cpu, 0x7f, (uint16)(0x000f + coarse_index * 2u));
      const uint16 local =
          (uint16)(((fine_y & 3) * 4) + (fine_x & 3));
      const uint32 fine_addr =
          0x800fu + (uint32)record * 32u + (uint32)local * 2u;
      if (fine_addr <= 0xfffeu)
        word = ur_ws_native_read16_bank(cpu, 0x7f, (uint16)fine_addr);
    }
    out[j * 2] = (uint8)(word & 0xff);
    out[j * 2 + 1] = (uint8)(word >> 8);
  }
  return 1;
}

static int ur_ws_native_vs_column_from_course(CpuState *cpu, unsigned player,
                                               int depth, uint8 out[16]) {
  return ur_ws_native_vs_column_from_course_adjusted(
      cpu, player, depth, 0, out);
}

/* Materialize one arbitrary vertical 16-cell strip directly from the live
 * course presentation tables. 7F:000F is the u16 coarse-sector index;
 * 7F:800F contains 32-byte / 4x4 fine records of packed surface words.
 *
 * The stock primary strip is camera-cell X + 16 on the retained Dragster
 * fixture. Column +1 is intentionally left on the accepted guest +8 path
 * at +17. Host-owned column +2 is therefore camera-cell X + 18. Stock vertical
 * strip scheduling owns an independent vertical ring coordinate at $050D.
 * When that lane is live, its low-five-bit coordinate maps to the source
 * fine row with +2 phase and is unwrapped near camera Y. Camera Y is only
 * the unwrap reference while the vertical lane is active. When that lane is
 * inactive, stock behavior follows the unrounded camera cell (camy >> 4).
 */
static int ur_ws_native_shadow_from_course(CpuState *cpu, uint16 first_edge,
                                           unsigned host_index) {
  if (host_index >= UR_WS_NATIVE_MAX_HOST_COLUMNS)
    return 0;
  const uint16 camx = ur_ws_native_read16(cpu, 0x0419);
  const uint16 camy = ur_ws_native_read16(cpu, 0x041d);
  const uint16 coarse_width = ur_ws_native_read16(cpu, 0x04f1);
  const uint16 coarse_height = ur_ws_native_read16(cpu, 0x04f3);
  if (!coarse_width || !coarse_height)
    return 0;

  const int fine_x = (int)(camx >> 4) + 18 + (int)host_index;
  const int fine_y0 = ur_ws_native_vertical_fine_y(cpu);
  const int fine_width = (int)coarse_width * 4;
  const int fine_height = (int)coarse_height * 4;

  for (unsigned j = 0; j < 16; j++) {
    const int fine_y = fine_y0 + (int)j;
    uint16 word = 0;
    if (fine_x >= 0 && fine_x < fine_width &&
        fine_y >= 0 && fine_y < fine_height) {
      const uint16 sector_x = (uint16)(fine_x >> 2);
      const uint16 sector_y = (uint16)(fine_y >> 2);
      const uint32 coarse_index =
          (uint32)sector_y * (uint32)coarse_width + (uint32)sector_x;
      const uint16 record = ur_ws_native_read16_bank(
          cpu, 0x7f, (uint16)(0x000f + coarse_index * 2u));
      const uint16 local =
          (uint16)(((fine_y & 3) * 4) + (fine_x & 3));
      const uint32 fine_addr =
          0x800fu + (uint32)record * 32u + (uint32)local * 2u;
      if (fine_addr <= 0xfffeu)
        word = ur_ws_native_read16_bank(cpu, 0x7f, (uint16)fine_addr);
      /* Live presentation can transiently expose a sentinel/non-record entry
       * while the vertical edge moves. Stock renders that cell blank; mirror
       * that presentation result instead of failing the whole host strip. */
    }
    ur_ws_native_shadow_payload[host_index][j * 2] = (uint8)(word & 0xff);
    ur_ws_native_shadow_payload[host_index][j * 2 + 1] = (uint8)(word >> 8);
  }

  ur_ws_native_shadow_edge[host_index] =
      (uint16)((first_edge & 0xffe0u) |
               ((first_edge + 1u + host_index) & 0x001fu));
  ur_ws_native_shadow_count[host_index] = 16;
  return 1;
}

static int ur_ws_native_should_prepare(CpuState *cpu) {
  const int margin = ur_ws_native_margin();
  if (margin < 8 || margin > 72 || (margin & 7) != 0 ||
      ur_ws_native_payload_live)
    return 0;

  if (cpu->ram[0x0ddb] != 0) {
    const int p1 =
        ur_ws_native_read16(cpu, 0x0505) != 0xffff &&
        ur_ws_native_read16(cpu, 0x052b) == 8;
    const int p2 =
        ur_ws_native_read16(cpu, 0x0507) != 0xffff &&
        ur_ws_native_read16(cpu, 0x052d) == 8;
    /* The recovered VS seam is proven only for one adjacent strip. Deeper
     * split-screen materialization remains a separate discriminator. */
    return (margin == 8 || margin == 16) && (p1 || p2);
  }

  return ur_ws_native_read16(cpu, 0x0505) != 0xffff &&
         ur_ws_native_read16(cpu, 0x052b) == 16;
}

static void ur_ws_native_begin_second_pass(CpuState *cpu) {
  ur_ws_native_cpu_snapshot = *cpu;
  memcpy(ur_ws_native_low_wram_snapshot, cpu->ram,
         sizeof(ur_ws_native_low_wram_snapshot));
  ur_ws_native_second_pass = 1;
}

static void ur_ws_native_finish_second_pass(CpuState *cpu, RecompReturn result) {
  const int split = ur_ws_native_cpu_snapshot.ram[0x0ddb] != 0;

  if (split) {
    const uint16 p1_second_edge = ur_ws_native_read16(cpu, 0x0505);
    const uint16 p1_second_count = ur_ws_native_read16(cpu, 0x052b);
    const uint16 p2_second_edge = ur_ws_native_read16(cpu, 0x0507);
    const uint16 p2_second_count = ur_ws_native_read16(cpu, 0x052d);
    const uint16 p1_second_vertical =
        (uint16)(ur_ws_native_read16(cpu, 0x0533) +
                 ur_ws_native_read16(cpu, 0x0537));
    const uint16 p2_second_vertical =
        (uint16)(ur_ws_native_read16(cpu, 0x0535) +
                 ur_ws_native_read16(cpu, 0x0539));
    const uint16 p1_stock_count = ur_ws_native_snapshot_read16(0x052b);
    const uint16 p2_stock_count = ur_ws_native_snapshot_read16(0x052d);
    const uint16 p1_stock_vertical =
        (uint16)(ur_ws_native_snapshot_read16(0x0533) +
                 ur_ws_native_snapshot_read16(0x0537));
    const uint16 p2_stock_vertical =
        (uint16)(ur_ws_native_snapshot_read16(0x0535) +
                 ur_ws_native_snapshot_read16(0x0539));
    const uint16 p1_src =
        (uint16)(0x0453 + p1_second_vertical * 2u);
    const uint16 p2_src =
        (uint16)(0x0475 + p2_second_vertical * 2u);
    const uint16 p1_dst =
        (uint16)(0x0433 + (p1_stock_vertical + p1_stock_count) * 2u);
    const uint16 p2_dst =
        (uint16)(0x0475 + (p2_stock_vertical + p2_stock_count) * 2u);
    const int p1_valid =
        result == RECOMP_RETURN_NORMAL &&
        ur_ws_native_snapshot_read16(0x0505) != 0xffff &&
        p1_stock_count == 8 &&
        p1_second_edge != 0xffff && p1_second_count == 8 &&
        p1_src >= 0x0453 && p1_src + 16u <= 0x0475 &&
        p1_dst >= 0x0433 && p1_dst + 16u <= 0x0475;
    const int p2_valid =
        result == RECOMP_RETURN_NORMAL &&
        ur_ws_native_snapshot_read16(0x0507) != 0xffff &&
        p2_stock_count == 8 &&
        p2_second_edge != 0xffff && p2_second_count == 8 &&
        p2_src >= 0x0475 && p2_src + 16u <= 0x04b7 &&
        p2_dst >= 0x0475 && p2_dst + 16u <= 0x04b7;

    if (p1_valid)
      memcpy(ur_ws_native_vs_p1_future_payload, cpu->ram + p1_src, 16);
    if (p2_valid)
      memcpy(ur_ws_native_vs_p2_future_payload, cpu->ram + p2_src, 16);

    ur_ws_native_second_pass = 0;
    *cpu = ur_ws_native_cpu_snapshot;
    memcpy(cpu->ram, ur_ws_native_low_wram_snapshot,
           sizeof(ur_ws_native_low_wram_snapshot));

    ur_ws_native_vs_p1_payload_len = 0;
    ur_ws_native_vs_p2_payload_len = 0;
    ur_ws_native_vs_payload_live = 0;
    ur_ws_native_vs_materializer_match[0] = 0;
    ur_ws_native_vs_materializer_match[1] = 0;

    if (p1_valid) {
      uint8 calibrated[16];
      if (ur_ws_native_vs_column_from_course(cpu, 0, 0, calibrated) &&
          memcmp(calibrated, ur_ws_native_vs_p1_future_payload, 16) == 0)
        ur_ws_native_vs_materializer_match[0] = 1;
    }
    if (p2_valid) {
      uint8 calibrated[16];
      if (ur_ws_native_vs_column_from_course(cpu, 1, 0, calibrated) &&
          memcmp(calibrated, ur_ws_native_vs_p2_future_payload, 16) == 0)
        ur_ws_native_vs_materializer_match[1] = 1;
    }

    if (ur_ws_native_trace()) {
      for (unsigned player = 0; player < 2; player++) {
        const int valid = player ? p2_valid : p1_valid;
        const int matched = ur_ws_native_vs_materializer_match[player];
        const uint8 *accepted =
            player ? ur_ws_native_vs_p2_future_payload
                   : ur_ws_native_vs_p1_future_payload;
        if (!valid || matched)
          continue;
        int found_depth = -99;
        int found_y = 0;
        uint8 candidate[16];
        for (int depth = -2; depth <= 3 && found_depth == -99; depth++) {
          for (int yadj = -4; yadj <= 4; yadj++) {
            if (ur_ws_native_vs_column_from_course_adjusted(
                    cpu, player, depth, yadj, candidate) &&
                memcmp(candidate, accepted, 16) == 0) {
              found_depth = depth;
              found_y = yadj;
              break;
            }
          }
        }
        fprintf(stderr,
                "URWS_VS_CALIBRATION_SEARCH margin=%d player=%u camx=%u camy=%u depth=%d yadj=%d accepted=",
                ur_ws_native_margin(), player + 1u,
                (unsigned)ur_ws_native_read16(cpu, player ? 0x041b : 0x0419),
                (unsigned)ur_ws_native_read16(cpu, player ? 0x041f : 0x041d),
                found_depth, found_y);
        for (unsigned j = 0; j < 16; j++)
          fprintf(stderr, "%02X", (unsigned)accepted[j]);
        fprintf(stderr, "\n");
      }
    }

    if (p1_valid) {
      ur_ws_native_write16(cpu, 0x0509, p1_second_edge);
      ur_ws_native_write16(cpu, 0x052f, p1_second_count);
      memcpy(cpu->ram + p1_dst, ur_ws_native_vs_p1_future_payload, 16);
      ur_ws_native_vs_p1_payload_addr = p1_dst;
      ur_ws_native_vs_p1_payload_len = 16;
      ur_ws_native_vs_payload_live = 1;
      if (ur_ws_native_trace())
        fprintf(stderr,
                "URWS_VS_PREP margin=%d player=1 camx=%u edge=%04X count=%u payload_addr=%04X\n",
                ur_ws_native_margin(),
                (unsigned)ur_ws_native_read16(cpu, 0x0419),
                (unsigned)p1_second_edge, (unsigned)p1_second_count,
                (unsigned)p1_dst);
    }
    if (p2_valid) {
      ur_ws_native_write16(cpu, 0x050b, p2_second_edge);
      ur_ws_native_write16(cpu, 0x0531, p2_second_count);
      memcpy(cpu->ram + p2_dst, ur_ws_native_vs_p2_future_payload, 16);
      ur_ws_native_vs_p2_payload_addr = p2_dst;
      ur_ws_native_vs_p2_payload_len = 16;
      ur_ws_native_vs_payload_live = 1;
      if (ur_ws_native_trace())
        fprintf(stderr,
                "URWS_VS_PREP margin=%d player=2 camx=%u edge=%04X count=%u payload_addr=%04X\n",
                ur_ws_native_margin(),
                (unsigned)ur_ws_native_read16(cpu, 0x041b),
                (unsigned)p2_second_edge, (unsigned)p2_second_count,
                (unsigned)p2_dst);
    }
    if (ur_ws_native_trace()) {
      if (p1_valid)
        fprintf(stderr, "URWS_VS_MATERIALIZER margin=%d player=1 calibrated=%d\n",
                ur_ws_native_margin(), ur_ws_native_vs_materializer_match[0]);
      if (p2_valid)
        fprintf(stderr, "URWS_VS_MATERIALIZER margin=%d player=2 calibrated=%d\n",
                ur_ws_native_margin(), ur_ws_native_vs_materializer_match[1]);
    }

    if (ur_ws_native_margin() >= 16) {
      for (unsigned player = 0; player < 2; player++) {
        const int valid = player ? p2_valid : p1_valid;
        const uint16 first_edge = player ? p2_second_edge : p1_second_edge;
        if (!valid || !ur_ws_native_vs_materializer_match[player])
          continue;
        if (!ur_ws_native_vs_column_from_course(
                cpu, player, 1, ur_ws_native_vs_shadow_payload[player]))
          continue;
        ur_ws_native_vs_shadow_edge[player] =
            (uint16)((first_edge & 0xffe0u) |
                     ((first_edge + 1u) & 0x001fu));
        if (ur_ws_native_trace()) {
          fprintf(stderr,
                  "URWS_VS_SHADOW16 provider=course-runtime player=%u camx=%u edge=%04X count=8 payload=",
                  player + 1u,
                  (unsigned)ur_ws_native_read16(cpu, player ? 0x041b : 0x0419),
                  (unsigned)ur_ws_native_vs_shadow_edge[player]);
          for (unsigned j = 0; j < 16; j++)
            fprintf(stderr, "%02X",
                    (unsigned)ur_ws_native_vs_shadow_payload[player][j]);
          fprintf(stderr, "\n");
        }
      }
    }

    ur_ws_native_payload_live = ur_ws_native_vs_payload_live;
    return;
  }

  const uint16 second_edge = ur_ws_native_read16(cpu, 0x0505);
  const uint16 second_count = ur_ws_native_read16(cpu, 0x052b);
  memcpy(ur_ws_native_future_payload, cpu->ram + 0x0453,
         sizeof(ur_ws_native_future_payload));

  ur_ws_native_second_pass = 0;
  *cpu = ur_ws_native_cpu_snapshot;
  memcpy(cpu->ram, ur_ws_native_low_wram_snapshot,
         sizeof(ur_ws_native_low_wram_snapshot));

  if (result != RECOMP_RETURN_NORMAL ||
      second_edge == 0xffff || second_count != 16)
    return;

  ur_ws_native_write16(cpu, 0x0509, second_edge);
  ur_ws_native_write16(cpu, 0x052f, second_count);
  memcpy(cpu->ram + 0x0453, ur_ws_native_future_payload,
         sizeof(ur_ws_native_future_payload));
  ur_ws_native_payload_live = 1;

  const int margin = ur_ws_native_margin();
  ur_ws_native_shadow_live_count = 0;
  const unsigned wanted_host_columns =
      margin >= 16 ? (unsigned)(margin / 8 - 1) : 0u;
  for (unsigned i = 0; i < wanted_host_columns; i++) {
    if (!ur_ws_native_shadow_from_course(cpu, second_edge, i))
      break;
    ur_ws_native_shadow_live_count++;
  }

  if (ur_ws_native_trace()) {
    if (margin == 8) {
      fprintf(stderr, "URWS_PREP margin=8 camx=%u edge=%04X count=%u payload=",
              (unsigned)ur_ws_native_read16(cpu, 0x0419),
              (unsigned)second_edge, (unsigned)second_count);
      for (unsigned j = 0; j < 32; j++)
        fprintf(stderr, "%02X", (unsigned)ur_ws_native_future_payload[j]);
      fprintf(stderr, "\n");
    } else if (margin >= 16) {
      if (margin == 16)
        fprintf(stderr, "URWS_PREP16 camx=%u edge=%04X count=%u payload=",
                (unsigned)ur_ws_native_read16(cpu, 0x0419),
                (unsigned)second_edge, (unsigned)second_count);
      else if (margin == 24)
        fprintf(stderr, "URWS_PREP24 camx=%u edge=%04X count=%u payload=",
                (unsigned)ur_ws_native_read16(cpu, 0x0419),
                (unsigned)second_edge, (unsigned)second_count);
      else
        fprintf(stderr, "URWS_PREP_EXT margin=%d camx=%u edge=%04X count=%u payload=",
                margin,
                (unsigned)ur_ws_native_read16(cpu, 0x0419),
                (unsigned)second_edge, (unsigned)second_count);
      for (unsigned j = 0; j < 32; j++)
        fprintf(stderr, "%02X", (unsigned)ur_ws_native_future_payload[j]);
      fprintf(stderr, " camy=%u\n",
              (unsigned)ur_ws_native_read16(cpu, 0x041d));
      for (unsigned i = 0; i < wanted_host_columns; i++) {
        if (i >= ur_ws_native_shadow_live_count) {
          fprintf(stderr, "URWS_STOP margin=%d column=%u reason=course-materializer-miss\n",
                  margin, i + 2u);
          break;
        }
        if (margin == 16)
          fprintf(stderr,
                  "URWS_SHADOW16 provider=course-runtime column=%u camx=%u edge=%04X count=%u payload=",
                  i + 2u,
                  (unsigned)ur_ws_native_read16(cpu, 0x0419),
                  (unsigned)ur_ws_native_shadow_edge[i],
                  (unsigned)ur_ws_native_shadow_count[i]);
        else if (margin == 24)
          fprintf(stderr,
                  "URWS_SHADOW24 provider=course-runtime column=%u camx=%u edge=%04X count=%u payload=",
                  i + 2u,
                  (unsigned)ur_ws_native_read16(cpu, 0x0419),
                  (unsigned)ur_ws_native_shadow_edge[i],
                  (unsigned)ur_ws_native_shadow_count[i]);
        else
          fprintf(stderr,
                  "URWS_SHADOW_EXT provider=course-runtime margin=%d column=%u camx=%u edge=%04X count=%u payload=",
                  margin, i + 2u,
                  (unsigned)ur_ws_native_read16(cpu, 0x0419),
                  (unsigned)ur_ws_native_shadow_edge[i],
                  (unsigned)ur_ws_native_shadow_count[i]);
        for (unsigned j = 0; j < 32; j++)
          fprintf(stderr, "%02X", (unsigned)ur_ws_native_shadow_payload[i][j]);
        fprintf(stderr, " camy=%u finex=%u finey=%u edgey=%04X county=%u\n",
                (unsigned)ur_ws_native_read16(cpu, 0x041d),
                (unsigned)((ur_ws_native_read16(cpu, 0x0419) >> 4) + 18u + i),
                (unsigned)(ur_ws_native_vertical_fine_y(cpu) & 0xffff),
                (unsigned)ur_ws_native_read16(cpu, 0x050d),
                (unsigned)ur_ws_native_read16(cpu, 0x0533));
      }
    }
  }
}

static void ur_ws_native_after_builder(CpuState *cpu) {
  if (!ur_ws_native_payload_live)
    return;
  ur_ws_native_write16(cpu, 0x0509, ur_ws_native_snapshot_read16(0x0509));
  ur_ws_native_write16(cpu, 0x052f, ur_ws_native_snapshot_read16(0x052f));
  if (ur_ws_native_vs_payload_live) {
    ur_ws_native_write16(cpu, 0x050b, ur_ws_native_snapshot_read16(0x050b));
    ur_ws_native_write16(cpu, 0x0531, ur_ws_native_snapshot_read16(0x0531));
  }
}

static void ur_ws_native_cleanup_previous_payload(CpuState *cpu) {
  if (!ur_ws_native_payload_live)
    return;
  if (ur_ws_native_vs_payload_live) {
    if (ur_ws_native_vs_p1_payload_len)
      memcpy(cpu->ram + ur_ws_native_vs_p1_payload_addr,
             ur_ws_native_low_wram_snapshot + ur_ws_native_vs_p1_payload_addr,
             ur_ws_native_vs_p1_payload_len);
    if (ur_ws_native_vs_p2_payload_len)
      memcpy(cpu->ram + ur_ws_native_vs_p2_payload_addr,
             ur_ws_native_low_wram_snapshot + ur_ws_native_vs_p2_payload_addr,
             ur_ws_native_vs_p2_payload_len);
  } else {
    memcpy(cpu->ram + 0x0453,
           ur_ws_native_low_wram_snapshot + 0x0453, 32);
  }
  ur_ws_native_payload_live = 0;
  if (ur_ws_native_trace()) {
    if (ur_ws_native_vs_payload_live)
      fprintf(stderr, "URWS_VS_CLEANUP margin=%d p1=%u p2=%u\n",
              ur_ws_native_margin(), ur_ws_native_vs_p1_payload_len,
              ur_ws_native_vs_p2_payload_len);
    else if (ur_ws_native_margin() == 8)
      fprintf(stderr, "URWS_CLEANUP margin=8\n");
    else if (ur_ws_native_margin() == 16)
      fprintf(stderr, "URWS_CLEANUP16 shadows=%u\n", ur_ws_native_shadow_live_count);
    else if (ur_ws_native_margin() == 24)
      fprintf(stderr, "URWS_CLEANUP24 shadows=%u\n", ur_ws_native_shadow_live_count);
    else if (ur_ws_native_margin() > 24)
      fprintf(stderr, "URWS_CLEANUP_EXT margin=%d shadows=%u\n",
              ur_ws_native_margin(), ur_ws_native_shadow_live_count);
  }
  ur_ws_native_vs_payload_live = 0;
  ur_ws_native_vs_p1_payload_len = 0;
  ur_ws_native_vs_p2_payload_len = 0;
  ur_ws_native_shadow_live_count = 0;
}
'''.strip()

SECOND_PASS = r'''
    ur_ws_native_trace_primary(cpu);
    ur_ws_native_cleanup_previous_payload(cpu);
    if (ur_ws_native_should_prepare(cpu)) {
      ur_ws_native_begin_second_pass(cpu);

      /* Replay the exact stock JSR $A59E host-call ABI emitted at 81:A597. */
      cpu_write8(cpu, 0x00, cpu->S, 0xa5); cpu->S = (uint16)(cpu->S - 1);
      cpu_write8(cpu, 0x00, cpu->S, 0x99); cpu->S = (uint16)(cpu->S - 1);
      cpu->host_return_valid = 2;
      RecompReturn _ur_ws_result = __A59E_CALLEE__(cpu);

      ur_ws_native_finish_second_pass(cpu, _ur_ws_result);
    }
'''.strip("\n")

STAGE_INIT_RE = re.compile(r"(?P<indent>[ \t]*)uint16 (?P<var>_v\d+) = 0x433;\n(?P=indent)cpu_write_y_x\(cpu, \(uint16\)\((?P=var)\)\);")

AFTER_BUILDER = r'''
    ur_ws_native_after_builder(cpu);
'''.strip("\n")



def canon(pc: int) -> int:
    return pc & ~0x800000


def _trace_hits(text: str) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for m in TRACE_RE.finditer(text):
        out.setdefault(canon(int(m.group(1), 16)), []).append(m.start())
    return out


def _insert_before_first_function(text: str, block: str) -> str:
    match = re.search(r"(?m)^RecompReturn\s+[A-Za-z0-9_]+\s*\(", text)
    if not match:
        raise ValueError("generated file has no RecompReturn function definition")
    return text[:match.start()] + block + "\n\n" + text[match.start():]


def _insert_before_postcall_variant_split(text: str, start_pc: int, end_pc: int, snippet: str) -> str:
    hits = _trace_hits(text)
    starts = hits.get(start_pc, [])
    ends = hits.get(end_pc, [])
    if len(starts) != 1 or not ends:
        raise ValueError(
            f"post-call region not exact: start={len(starts)} end={len(ends)}"
        )
    start = starts[0]
    end = min(pos for pos in ends if pos > start)
    region = text[start:end]
    anchor = "switch (((cpu->m_flag & 1) << 1) | (cpu->x_flag & 1)) {"
    positions = []
    off = 0
    while True:
        rel = region.find(anchor, off)
        if rel < 0:
            break
        positions.append(rel)
        off = rel + len(anchor)
    if len(positions) < 2:
        raise ValueError(
            f"expected call dispatch plus post-call variant split, found {len(positions)}"
        )
    pos = start + positions[-1]
    line_start = text.rfind("\n", 0, pos) + 1
    indent = re.match(r"[ \t]*", text[line_start:pos]).group(0)
    rendered = "\n".join(
        indent + line if line else line for line in snippet.splitlines()
    ) + "\n"
    return text[:pos] + rendered + text[pos:]


def _insert_after_deadline_guard(text: str, pc: int, snippet: str) -> str:
    hits = _trace_hits(text).get(pc, [])
    if len(hits) != 1:
        raise ValueError(f"expected exactly one emitted block at {pc:06X}, found {len(hits)}")
    start = hits[0]
    next_trace = TRACE_RE.search(text, start + 1)
    end = next_trace.start() if next_trace else min(len(text), start + 5000)
    region = text[start:end]
    charge = "cpu->coprocessor_master_cycles = cpu->master_cycles;"
    rel = region.find(charge)
    if rel < 0:
        raise ValueError(f"{pc:06X} block lacks expected post-deadline cycle-charge anchor")
    pos = start + rel
    indent = re.match(r"[ \t]*", text[text.rfind("\n", 0, pos) + 1:pos]).group(0)
    rendered = "\n".join(indent + line if line else line for line in snippet.splitlines()) + "\n"
    return text[:pos] + rendered + text[pos:]


def apply(gen_dir: Path) -> dict:
    files = sorted(gen_dir.glob("bank*_v2.c"))
    if not files:
        raise ValueError(f"no generated bank*_v2.c files under {gen_dir}")

    wrapper_pc = PCS["wrapper_after_first_helper"]
    wrapper_candidates = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="strict")
        hits = _trace_hits(text)
        if wrapper_pc in hits:
            wrapper_candidates.append(path)

    if len(wrapper_candidates) != 1:
        raise ValueError(f"expected one wrapper TU, found {len(wrapper_candidates)}")
    wrapper = wrapper_candidates[0]
    wrapper_text = wrapper.read_text(encoding="utf-8")

    if MARKER in wrapper_text:
        return {
            "schema_version": 1,
            "changed": False,
            "wrapper_file": wrapper.name,
            "margin0_control": True,
            "margin8_hook": True,
            "vs_margin8_supported": True,
            "vs_margin16_capacity_probe": True,
            "margin16_supported": True,
            "margin24_supported": True,
        "margin64_supported": True,
            "margin72_supported": True,
            "first_constraint": "none-through-plus72",
        }

    required = [
        PCS["wrapper_after_first_helper"],
    ]
    hits = _trace_hits(wrapper_text)
    missing = [f"{pc:06X}" for pc in required if len(hits.get(pc, [])) != 1]
    if missing:
        raise ValueError("wrapper seam not exact: " + ", ".join(missing))
    callee_matches = A59E_CALLEE_RE.findall(wrapper_text)
    callee_names = sorted(set(callee_matches))
    if len(callee_names) != 1:
        raise ValueError(f"expected one generated M0X0 A59E callee, found {callee_names}")
    a59e_callee = callee_names[0]

    stage_matches = list(STAGE_INIT_RE.finditer(wrapper_text))
    if len(stage_matches) != 1:
        raise ValueError(f"expected one A59E staging initializer, found {len(stage_matches)}")

    wrapper_text = _insert_before_first_function(wrapper_text, SUPPORT)
    stage_match = STAGE_INIT_RE.search(wrapper_text)
    if stage_match is None:
        raise ValueError("A59E staging initializer moved after support insertion")
    indent = stage_match.group("indent")
    var = stage_match.group("var")
    stage_replacement = (
        f"{indent}uint16 {var} = ur_ws_native_second_pass ? 0x453 : 0x433;\n"
        f"{indent}cpu_write_y_x(cpu, (uint16)({var}));"
    )
    wrapper_text = wrapper_text[:stage_match.start()] + stage_replacement + wrapper_text[stage_match.end():]
    second_pass = SECOND_PASS.replace("__A59E_CALLEE__", a59e_callee)
    wrapper_text = _insert_after_deadline_guard(
        wrapper_text, PCS["wrapper_after_first_helper"], second_pass)
    wrapper_text = _insert_before_postcall_variant_split(
        wrapper_text,
        PCS["wrapper_after_first_helper"],
        PCS["wrapper_after_descriptor_builder"],
        AFTER_BUILDER,
    )
    wrapper.write_text(wrapper_text, encoding="utf-8")

    return {
        "schema_version": 1,
        "changed": True,
        "wrapper_file": wrapper.name,
        "margin0_control": True,
        "margin8_hook": True,
        "vs_margin8_supported": True,
        "vs_margin16_capacity_probe": True,
        "margin16_supported": True,
        "margin24_supported": True,
            "margin64_supported": True,
            "margin72_supported": True,
        "first_constraint": "none-through-plus72",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gen_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = apply(args.gen_dir)
    payload = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
