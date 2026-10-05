/*
 * SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef __PULP_IDMA_UTILS_H__
#define __PULP_IDMA_UTILS_H__

#include "pmsis.h"

// HAL length is unsigned short: split long 1D transfers at runtime, so every tile
// shares one call shape. Word-aligned chunks keep the offsets aligned.
#define DEEPLOY_IDMA_CHUNK (0xFFFFu & ~3u)

static inline void deeploy_idma_transfer_1d_and_wait(unsigned int direction,
                                                     unsigned int ext,
                                                     unsigned int loc,
                                                     unsigned int size) {
  while (size > 0xFFFFu) {
    pulp_idma_transfer_1d_and_wait(direction, ext, loc, DEEPLOY_IDMA_CHUNK);
    ext += DEEPLOY_IDMA_CHUNK;
    loc += DEEPLOY_IDMA_CHUNK;
    size -= DEEPLOY_IDMA_CHUNK;
  }
  pulp_idma_transfer_1d_and_wait(direction, ext, loc, (unsigned short)size);
}

#endif // __PULP_IDMA_UTILS_H__
