#include "basecmd.h"    // oid_alloc
#include "board/gpio.h" // struct gpio_in
#include "board/irq.h"  // irq_disable
#include "command.h"    // DECL_COMMAND
#include "sched.h"      // struct timer
#include "autoconf.h"
#include "board/misc.h"

struct fly_probe
{

  struct gpio_in probe_pwm_pin; // calibration_pin_in;
  struct gpio_out calibration_pin_out;
};

// static struct task_wake fly_probe_wake;

void command_config_pin(uint32_t *args)
{
  struct fly_probe *a = oid_alloc(
      args[0], command_config_pin, sizeof(*a));

  a->probe_pwm_pin = gpio_in_setup(args[1], 1);
  // a->calibration_pin_in  =  gpio_in_setup(args[2],1);
  a->calibration_pin_out = gpio_out_setup(args[2], 1);
  gpio_out_write(a->calibration_pin_out, 1);
}
DECL_COMMAND(command_config_pin, "config_fly_probe_pin oid=%c probe_pwm_pin=%u calibration_pin=%u ");

static unsigned int
nsecs_to_ticks(uint32_t ns)
{
  return timer_from_us(ns * 1000) / 1000000;
}

static void
probe_delay(unsigned int ticks)
{
  unsigned int t = timer_read_time() + nsecs_to_ticks(ticks);
  while (t > timer_read_time())
    ;
}

void set_fly_probe_calibration(uint32_t *args)
{
  struct fly_probe *a = oid_lookup(args[0], command_config_pin);
  gpio_out_reset(a->calibration_pin_out, 0);
  probe_delay(200000);
  gpio_out_write(a->calibration_pin_out, 1);
  // gpio_in_reset(a->calibration_pin_in, 1);
}
DECL_COMMAND(set_fly_probe_calibration, "fly_probe_calibration oid=%c");

uint32_t
get_fly_probe(uint32_t *args)
{

  struct fly_probe *a = oid_lookup(args[0], command_config_pin);
  uint32_t sys_time = 0;
  uint32_t START_time = 0;
  uint32_t cur_time = 0;
  uint32_t time_out_us = 2000;

  sys_time = timer_read_time();
  while (gpio_in_read(a->probe_pwm_pin) == 1)
  {
    cur_time = timer_read_time();
    if ((cur_time - sys_time) >= timer_from_us(time_out_us))
    {

      return 11;
    }
  }

  while (gpio_in_read(a->probe_pwm_pin) == 0)
  {
    cur_time = timer_read_time();
    if ((cur_time - sys_time) >= timer_from_us(time_out_us))
    {

      return 22;
    }
  }
  START_time = timer_read_time();

  while (gpio_in_read(a->probe_pwm_pin) == 1)
  {
    cur_time = timer_read_time();
    if ((cur_time - sys_time) >= timer_from_us(time_out_us))
    {

      return 33;
    }
  }
  if ((cur_time - START_time) < 30)
    return 0;
  else
    return ((cur_time - START_time) / timer_from_us(1));
}

void fly_probe_task(uint32_t *args)
{

  uint8_t oid = args[0];

  uint32_t value = get_fly_probe(args);

  sendf("fly_probe_value oid=%c value=%u", oid, value);
}
DECL_COMMAND(fly_probe_task, "fly_probe oid=%c");
// DECL_TASK(fly_probe_task);
