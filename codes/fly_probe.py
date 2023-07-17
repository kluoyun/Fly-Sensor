# Support for Fly-Sensor
#
# Copyright (C) 2023  FlyMaker <service@3dmellow.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
from . import bus
from . import probe

DEFAULT_IIC_ADDR = 0x2B


class FlyprobeEndstopWrapper:
    def __init__(self, config):
        self.printer = printer = config.get_printer()
        self.probe_mode = config.getint("probe_mode", 0)
        # self.i2c = bus.MCU_I2C_from_config(
        # config, default_addr=DEFAULT_IIC_ADDR, default_speed=100000)
        self.stow_on_each_sample = config.getboolean("deactivate_on_each_sample", True)
        gcode_macro = self.printer.load_object(config, "gcode_macro")
        self.activate_gcode = gcode_macro.load_template(config, "activate_gcode", "")
        self.deactivate_gcode = gcode_macro.load_template(
            config, "deactivate_gcode", ""
        )
        self.position_endstop = config.getfloat("z_offset", minval=0.0)
        ppins = printer.lookup_object("pins")
        pin = config.get("probe_pwm_pin")
        pin_params = ppins.lookup_pin(pin)
        mcu = pin_params["chip"]
        self.probe_pwm_pin = pin_params["pin"]
        pin_params = ppins.lookup_pin(config.get("calibration_pin"))
        mcu = pin_params["chip"]
        self.calibration_pin = pin_params["pin"]
        self.mcu = mcu
        self.oid = self.mcu.create_oid()
        self.mcu.register_config_callback(self.build_config)
        self.add_config_cmd = (
            self.fly_probe_send_cmd
        ) = self.fly_probe_calibration_cmd = None
        gcode = self.printer.lookup_object("gcode")
        gcode.register_command(
            "GET_FLY_PROBE", self.cmd_GET_FLY_PROBE, desc=self.cmd_GET_FLY_PROBE_help
        )
        gcode.register_command(
            "FLY_PROBE_CALIBRATION",
            self.cmd_SET_FLY_PROBE_CA,
            desc=self.cmd_GET_FLY_PROBE_help,
        )

        pin = config.get("sensor_pin")
        pin_params = ppins.lookup_pin(pin, can_invert=True, can_pullup=True)
        mcu = pin_params["chip"]
        self.mcu_endstop = mcu.setup_pin("endstop", pin_params)
        # self.printer.register_event_handler('klippy:mcu_identify',
        #                                    self._handle_mcu_identify)
        # Wrappers
        self.get_mcu = self.mcu_endstop.get_mcu
        self.add_stepper = self.mcu_endstop.add_stepper
        self.get_steppers = self.mcu_endstop.get_steppers
        self.home_wait = self.mcu_endstop.home_wait
        self.query_endstop = self.mcu_endstop.query_endstop
        self.home_start = self.mcu_endstop.home_start
        # multi probes state
        self.multi = "OFF"

    def build_config(self):
        self.mcu.add_config_cmd(
            "config_fly_probe_pin oid=%d probe_pwm_pin=%s calibration_pin=%s"
            % (self.oid, self.probe_pwm_pin, self.calibration_pin)
        )

        cmd_queue = self.mcu.alloc_command_queue()

        self.probe_value = 0
        self.fly_probe_send_cmd = self.mcu.lookup_query_command(
            "fly_probe oid=%c",
            "fly_probe_value oid=%c value=%u",
            oid=self.oid,
            cq=cmd_queue,
        )

        self.fly_probe_calibration_cmd = self.mcu.lookup_command(
            "fly_probe_calibration oid=%c"
        )

    def get_status(self, eventtime):
        return {"value": self.probe_value}

    def cmd_SET_FLY_PROBE_CA(self, gcmd):
        self.toolhead = self.printer.lookup_object("toolhead")
        self.toolhead.wait_moves()
        self.fly_probe_calibration_cmd.send([self.oid])

    def raise_probe(self):
        toolhead = self.printer.lookup_object("toolhead")
        start_pos = toolhead.get_position()
        self.deactivate_gcode.run_gcode_from_command()
        if toolhead.get_position()[:3] != start_pos[:3]:
            raise self.printer.command_error(
                "Toolhead moved during probe activate_gcode script"
            )

    def lower_probe(self):
        toolhead = self.printer.lookup_object("toolhead")
        start_pos = toolhead.get_position()
        self.activate_gcode.run_gcode_from_command()
        if toolhead.get_position()[:3] != start_pos[:3]:
            raise self.printer.command_error(
                "Toolhead moved during probe deactivate_gcode script"
            )

    def multi_probe_begin(self):
        if self.stow_on_each_sample:
            return
        self.multi = "FIRST"

    def multi_probe_end(self):
        if self.stow_on_each_sample:
            return
        self.raise_probe()
        self.multi = "OFF"

    def probe_prepare(self, hmove):
        if self.multi == "OFF" or self.multi == "FIRST":
            self.lower_probe()
            if self.multi == "FIRST":
                self.multi = "ON"

    def probe_finish(self, hmove):
        if self.multi == "OFF":
            self.raise_probe()

    def get_position_endstop(self):
        return self.position_endstop

    cmd_GET_FLY_PROBE_help = "Get Fly probe value"

    def cmd_GET_FLY_PROBE(self, gcmd):
        pr = self.fly_probe_send_cmd.send([self.oid])
        str_probe = str((pr["value"] - 30) / 100)
        gcmd.respond_info(str_probe)

    def get_probe_va(self):
        self.toolhead = self.printer.lookup_object("toolhead")
        self.gcode = self.printer.lookup_object("gcode")
        # self.toolhead.wait_moves()
        pr = self.fly_probe_send_cmd.send([self.oid])
        # str_temp = str((pr['value']-30)/100)
        # self.gcode.respond_info(" va %.2f"
        #                        % ((pr['value']-30)/100))
        return (pr["value"] - 30) / 100


def load_config(config):
    fly_probe = FlyprobeEndstopWrapper(config)
    config.get_printer().add_object("probe", probe.PrinterProbe(config, fly_probe))
    return fly_probe
