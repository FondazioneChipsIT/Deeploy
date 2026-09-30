/*
 * SPDX-FileCopyrightText: 2026 ETH Zurich, University of Bologna and Fondazione Chips-IT
 *
 * SPDX-License-Identifier: Apache-2.0
 */

// OT cluster harness (from PULPOpen_iDMA): no L3, persistent mailbox worker.
// The OT host rings RCV per run; tot_err goes back via cluster-ctrl, LETTER0 and SND.

#include <math.h>

#include "CycleCounter.h"
#include "Network.h"
#include "pmsis.h"
#include "testinputs.h"
#include "testoutputs.h"

#ifndef ARCHI_HAS_MAILBOXES
#error "OpenTitanCluster harness needs the SDK opentitan_cluster chip (mailboxes)"
#endif

#define MAINSTACKSIZE 8000
#define SLAVESTACKSIZE 3800

struct pi_device cluster_dev;

static struct pi_cluster_task cluster_task;

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
    uint32_t output_buf_index = compare_args->output_buf_index;
    uint32_t *err_count = compare_args->err_count;

    uint32_t local_err_count = 0;

    for (uint32_t i = 0; i < num_elements; i++) {
      float expected_val = expected[i];
      float actual_val = actual[i];
      float diff = expected_val - actual_val;

      if ((diff < -1e-4) || (diff > 1e-4) || isnan(diff)) {
        local_err_count += 1;

        printf("Expected: %10.6f  ", expected_val);
        printf("Actual: %10.6f  ", actual_val);
        printf("Diff: %10.6f at Index %12u in Output %u\r\n", diff, i,
               output_buf_index);
      }
    }

    *err_count = local_err_count;
  }
}

static void send_task(void (*entry)(void *), void *arg) {
  pi_cluster_task(&cluster_task, entry, arg);
  cluster_task.stack_size = MAINSTACKSIZE;
  cluster_task.slave_stack_size = SLAVESTACKSIZE;
  pi_cluster_send_task_to_cl(&cluster_dev, &cluster_task);
}

// Inputs in, RunNetwork, outputs checked; returns the error count
static uint32_t run_and_check(void) {
  for (uint32_t buf = 0; buf < DeeployNetwork_num_inputs; buf++) {
    if ((uint32_t)DeeployNetwork_inputs[buf] >= 0x10000000) {
      memcpy(DeeployNetwork_inputs[buf], testInputVector[buf],
             DeeployNetwork_inputs_bytes[buf]);
    }
  }

  plp_idma_enable_clk();
  ResetTimer();
  StartTimer();
  send_task(RunNetwork, NULL);
  StopTimer();
  plp_idma_disable_clk();

  uint32_t tot_err = 0;
  uint32_t tot_tested = 0;
  FloatCompareArgs float_compare_args;
  uint32_t float_error_count = 0;

  for (uint32_t buf = 0; buf < DeeployNetwork_num_outputs; buf++) {
    void *compbuf = DeeployNetwork_outputs[buf];
    tot_tested += DeeployNetwork_outputs_bytes[buf] / sizeof(OUTPUTTYPE);

    if (ISOUTPUTFLOAT) {
      float_error_count = 0;
      float_compare_args.expected = testOutputVector[buf];
      float_compare_args.actual = compbuf;
      float_compare_args.num_elements =
          DeeployNetwork_outputs_bytes[buf] / sizeof(float);
      float_compare_args.output_buf_index = buf;
      float_compare_args.err_count = &float_error_count;

      send_task(CompareFloatOnCluster, &float_compare_args);

      tot_err += float_error_count;
    } else {

      for (uint32_t i = 0;
           i < DeeployNetwork_outputs_bytes[buf] / sizeof(OUTPUTTYPE); i++) {
        OUTPUTTYPE expected = ((OUTPUTTYPE *)testOutputVector[buf])[i];
        OUTPUTTYPE actual = ((OUTPUTTYPE *)compbuf)[i];
        int32_t error = expected - actual;
        OUTPUTTYPE diff = (OUTPUTTYPE)(error < 0 ? -error : error);

        if (diff) {
          tot_err += 1;
          printf("Expected: %4d  ", expected);
          printf("Actual: %4d  ", actual);
          printf("Diff: %4d at Index %12u in Output %u\r\n", diff, i, buf);
        }
      }
    }
  }

  printf("Runtime: %u cycles\r\n", getCycles());
  printf("Errors: %u out of %u \r\n", tot_err, tot_tested);

  return tot_err;
}

int main(void) {
  struct pi_cluster_conf conf;

  pi_cluster_conf_init(&conf);
  conf.id = 0;
  pi_open_from_conf(&cluster_dev, &conf);
  if (pi_cluster_open(&cluster_dev))
    return -1;

  send_task(InitNetwork, NULL);

  while (1) {
    // Other events in core 0's mask can wake it: wait for the mailbox one
    while (!(eu_evt_maskWaitAndClr(1 << ARCHI_CL_EVT_MBOX) &
             (1 << ARCHI_CL_EVT_MBOX)))
      ;
    hal_mailboxes_clear_receive_irq();
    // The host drives the irq as an edge: drop the event it re-latched
    eu_evt_clr(1 << ARCHI_CL_EVT_MBOX);

    uint32_t tot_err = run_and_check();

    hal_cluster_ctrl_return_set(0, (int)tot_err);
    hal_cluster_ctrl_eoc_set(1);
    hal_mailboxes_write_return_value((int)tot_err);
    hal_mailboxes_ring_doorbell();
  }
}
