/*
 * SPDX-FileCopyrightText: 2020 ETH Zurich and University of Bologna
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "CycleCounter.h"
#include "Network.h"
#include "dory_mem.h"
#include "pmsis.h"
#include "testinputs.h"
#include "testoutputs.h"

#define MAINSTACKSIZE 8000
#define SLAVESTACKSIZE 3800

// Bytes of an L3 output read back at a time; a multiple of every element size
#define CMP_CHUNK 1024

#define RUNTIME_FMT "Runtime: %u cycles\r\n"
#define ERRORS_FMT "Errors: %u out of %u \r\n"

// L3 (HyperRAM) addresses start at 0 and sit below the L1 (0x10000000) and L2
// (0x1C000000) windows; a 64 MB HyperRAM reaches 0x4000000.
#define IS_L3(addr) ((uint32_t)(addr) < 0x10000000)

// Memory arenas allocated by InitNetwork. Weak: a network without an L3 (or
// L1) arena does not define it, and then its address is NULL.
extern int8_t *DeeployNetwork_MEMORYARENA_L1;
#pragma weak DeeployNetwork_MEMORYARENA_L1
extern int8_t *DeeployNetwork_MEMORYARENA_L2;
#pragma weak DeeployNetwork_MEMORYARENA_L2
extern int8_t *DeeployNetwork_MEMORYARENA_L3;
#pragma weak DeeployNetwork_MEMORYARENA_L3

// A failed arena allocation is not checked by the generated code and would
// hang the network later, so report it right after InitNetwork
static int arena_failed(const char *level, int8_t **arena) {
  if (arena == NULL || *arena != NULL)
    return 0;
  printf("ERROR: %s memory arena allocation failed\r\n", level);
  return 1;
}

struct pi_device cluster_dev;

typedef struct {
  void *expected;
  void *actual;
  uint32_t num_elements;
  uint32_t output_buf_index;
  uint32_t *err_count;
} FloatCompareArgs;

void CompareFloatOnCluster(void *args) {

  if (pi_core_id() == 0) {
    FloatCompareArgs *compare_args = (FloatCompareArgs *)args;
    float *expected = (float *)compare_args->expected;
    float *actual = (float *)compare_args->actual;
    uint32_t num_elements = compare_args->num_elements;
    uint32_t *err_count = compare_args->err_count;

    uint32_t local_err_count = 0;

    for (uint32_t i = 0; i < num_elements; i++) {
      float expected_val = expected[i];
      float actual_val = actual[i];
      float diff = expected_val - actual_val;

      if ((diff < -1e-4) || (diff > 1e-4) || isnan(diff)) {
        local_err_count += 1;
      }
    }

    *err_count = local_err_count;
  }
}

int main(void) {
#ifndef CI
  printf("HELLO WORLD:\r\n");
#endif
  struct pi_cluster_conf conf;

  pi_cluster_conf_init(&conf);
  conf.id = 0;
  pi_open_from_conf(&cluster_dev, &conf);
  if (pi_cluster_open(&cluster_dev))
    return -1;

  mem_init();
#ifndef NOFLASH
  open_fs();
#endif

  printf("Intializing\r\n");

  struct pi_cluster_task cluster_task;

  pi_cluster_task(&cluster_task, InitNetwork, NULL);
  cluster_task.stack_size = MAINSTACKSIZE;
  cluster_task.slave_stack_size = SLAVESTACKSIZE;
  pi_cluster_send_task_to_cl(&cluster_dev, &cluster_task);

  if (arena_failed("L1", &DeeployNetwork_MEMORYARENA_L1) |
      arena_failed("L2", &DeeployNetwork_MEMORYARENA_L2) |
      arena_failed("L3", &DeeployNetwork_MEMORYARENA_L3))
    return -1;

#ifndef CI
  printf("Initialized\r\n");
#endif
  for (uint32_t buf = 0; buf < DeeployNetwork_num_inputs; buf++) {
    if ((uint32_t)DeeployNetwork_inputs[buf] >= 0x10000000) {
      memcpy(DeeployNetwork_inputs[buf], testInputVector[buf],
             DeeployNetwork_inputs_bytes[buf]);
    }
  }

#ifndef CI
  printf("Input copied\r\n");
#endif

  pi_cluster_task(&cluster_task, RunNetwork, NULL);
  cluster_task.stack_size = MAINSTACKSIZE;
  cluster_task.slave_stack_size = SLAVESTACKSIZE;
  plp_idma_enable_clk();
  ResetTimer();
  StartTimer();
  pi_cluster_send_task_to_cl(&cluster_dev, &cluster_task);
  StopTimer();
  plp_idma_disable_clk();

  // Cycles first: the network is done, the check below only reads outputs
  printf(RUNTIME_FMT, getCycles());

#ifndef CI
  printf("Output:\r\n");
#endif

  uint32_t tot_err = 0, tot_tested = 0;
  // L3 outputs are read back through one small L2 buffer, chunk by chunk, so
  // the check needs no large allocation in an almost full L2
  void *chunk = NULL;
  FloatCompareArgs float_compare_args;
  uint32_t float_error_count = 0;

  for (uint32_t buf = 0; buf < DeeployNetwork_num_outputs; buf++) {
    uint32_t bytes = DeeployNetwork_outputs_bytes[buf];
    int in_l3 = IS_L3(DeeployNetwork_outputs[buf]);
    tot_tested += bytes / sizeof(OUTPUTTYPE);

    if (in_l3 && chunk == NULL) {
      chunk = pi_l2_malloc(CMP_CHUNK);
      if (chunk == NULL) {
        printf("No L2 left to read back the outputs\r\n");
        return -1;
      }
    }

    for (uint32_t off = 0; off < bytes; off += CMP_CHUNK) {
      uint32_t len = bytes - off < CMP_CHUNK ? bytes - off : CMP_CHUNK;
      void *actual_buf;
      if (in_l3) {
        ram_read(chunk, (char *)DeeployNetwork_outputs[buf] + off, len);
        actual_buf = chunk;
      } else {
        actual_buf = (char *)DeeployNetwork_outputs[buf] + off;
      }
      void *expected_buf = (char *)testOutputVector[buf] + off;

      if (ISOUTPUTFLOAT) {
        float_error_count = 0;
        float_compare_args.expected = expected_buf;
        float_compare_args.actual = actual_buf;
        float_compare_args.num_elements = len / sizeof(float);
        float_compare_args.output_buf_index = buf;
        float_compare_args.err_count = &float_error_count;

        pi_cluster_task(&cluster_task, CompareFloatOnCluster,
                        &float_compare_args);
        cluster_task.stack_size = MAINSTACKSIZE;
        cluster_task.slave_stack_size = SLAVESTACKSIZE;
        pi_cluster_send_task_to_cl(&cluster_dev, &cluster_task);

        tot_err += float_error_count;
      } else {
        for (uint32_t i = 0; i < len / sizeof(OUTPUTTYPE); i++) {
          OUTPUTTYPE expected = ((OUTPUTTYPE *)expected_buf)[i];
          OUTPUTTYPE actual = ((OUTPUTTYPE *)actual_buf)[i];
          if (expected != actual) {
            tot_err += 1;
          }
        }
      }
    }
  }
  if (chunk != NULL) {
    pi_l2_free(chunk, CMP_CHUNK);
  }

  printf(ERRORS_FMT, tot_err, tot_tested);

  return (int)tot_err;
}
