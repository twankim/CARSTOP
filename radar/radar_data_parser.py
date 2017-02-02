from multiprocessing import Process
from util.logger_conf import configure_logs
import time, sys, logging, json, canlib, random, copy

idBase = 1279

class RadarDataParser(Process):
    """ Listens for new Radar messages over CAN and parses for the dispatcher.

    This parser reads messages from the CAN Bus using the Kvaser USB Python SKD
    and formats Radar information into a python object. Then we send the data
    along to the event dispatcher.
    """
    def __init__(self, callback=None, log=True, log_level="DEBUG"):
        """ Initialize the data parser, connect to the can bus. """
        Process.__init__(self)
        self.callback = callback
        self.log = log
        self.log_level = log_level
        self.data = {}

    def run(self):
        """ Start reading data from the CAN Bus and sending full objects to the dispatcher. """
        configure_logs(getattr(logging, self.log_level, None))
        self.logger = logging.getLogger('debug_radar')
        # These are logging properly on Bryce's machinekk:w
        # self.logger.info( "welcome to the debug_radar logger!")
        # logging.getLogger('radar').info("this is a dummy message")

        msgToFunc = {
            1248: self.status_one,
            1249: self.status_two,
            1250: self.status_three,
            1251: self.status_four,
            1280: self.track_msg,
            1281: self.track_msg,
            1282: self.track_msg,
            1283: self.track_msg,
            1284: self.track_msg,
            1285: self.track_msg,
            1286: self.track_msg,
            1287: self.track_msg,
            1288: self.track_msg,
            1289: self.track_msg,
            1290: self.track_msg,
            1291: self.track_msg,
            1292: self.track_msg,
            1293: self.track_msg,
            1294: self.track_msg,
            1295: self.track_msg,
            1296: self.track_msg,
            1297: self.track_msg,
            1298: self.track_msg,
            1299: self.track_msg,
            1300: self.track_msg,
            1301: self.track_msg,
            1302: self.track_msg,
            1303: self.track_msg,
            1304: self.track_msg,
            1305: self.track_msg,
            1306: self.track_msg,
            1307: self.track_msg,
            1308: self.track_msg,
            1309: self.track_msg,
            1310: self.track_msg,
            1311: self.track_msg,
            1312: self.track_msg,
            1313: self.track_msg,
            1314: self.track_msg,
            1315: self.track_msg,
            1316: self.track_msg,
            1317: self.track_msg,
            1318: self.track_msg,
            1319: self.track_msg,
            1320: self.track_msg,
            1321: self.track_msg,
            1322: self.track_msg,
            1323: self.track_msg,
            1324: self.track_msg,
            1325: self.track_msg,
            1326: self.track_msg,
            1327: self.track_msg,
            1328: self.track_msg,
            1329: self.track_msg,
            1330: self.track_msg,
            1331: self.track_msg,
            1332: self.track_msg,
            1333: self.track_msg,
            1334: self.track_msg,
            1335: self.track_msg,
            1336: self.track_msg,
            1337: self.track_msg,
            1338: self.track_msg,
            1339: self.track_msg,
            1340: self.track_msg,
            1341: self.track_msg,
            1342: self.track_msg,
            1343: self.track_msg,
            1344: self.track_status_msg,
            1488: self.validation_msg_one,
            1489: self.validation_msg_two,
            1508: self.additional_status_one,
            1509: self.additional_status_two,
            1510: self.additional_status_three,
            1511: self.additional_status_four,
            1512: self.additional_status_five,
        }
        cl = canlib.canlib()
        channels = cl.getNumberOfChannels()
        ch = 0; # Hard-coded, might need to change!
        if ch >= channels:
            print("Invalid channel number")
            sys.exit()

        try:
            ch1 = cl.openChannel(ch, canlib.canOPEN_ACCEPT_VIRTUAL)
            print("Using channel: %s, EAN: %s" % (ch1.getChannelData_Name(),
            ch1.getChannelData_EAN()))

            ch1.setBusOutputControl(canlib.canDRIVER_NORMAL)
            ch1.setBusParams(canlib.canBITRATE_500K)
            ch1.busOn()
        except (canlib.canError) as ex:
            print(ex)

        # Initialize the Radar
        message = [0,0,0,0,0,0,191,0]
        ch1.write(1265,message,8)

        msg_counter = 0 # Variable that keeps track of the iteration of msg 1344 we are on
        while True:
            try:
                msgId, msg, dlc, flg, time = ch1.read()
                # self.logger.debug("In radar_data_parser and this is a message")
                # self.logger.debug("msgId: %9d  time: %9d  flg: 0x%02x  dlc: %d " % (msgId, time, flg, dlc))
                print_var = ''.join('{:02x}'.format(x) for x in msg)
                # self.logger.debug((msg,print_var))

                if msgId in msgToFunc:
                    # This message is valid, so we need to parse it
                    if msgId >= 1280 and msgId <= 1343:
                        msgToFunc[msgId](msgId, msg)
                    else:
                        # self.logger.debug("In radar_data_parser and this is msgId %d", msgId)
                        if (msgId == 1344):
                            msgToFunc[msgId](msg_counter, msg)
                            msg_counter += 1
                        elif (msgId > 1344 and msg_counter > 0):
                            msgToFunc[msgId](msg)
                            msg_counter = 0
                        else:
                            msgToFunc[msgId](msg)
                            if (msgId == 1512):
                                # self.callback(copy.deepcopy(self.data))
                                self.callback(self.data)
                                if self.log:
                                    # sends JSON data to radar log file
                                    logging.getLogger('radar').info(json.dumps(self.data))

                                self.data = {} # Start with a fresh object
            except (canlib.canNoMsg) as ex:
                pass
            except (canlib.canError) as ex:
                print(ex)


    def track_msg(self, msgId, msg):
        """ message ID 500-53F or 1280-1343 """
        track_id = str(msgId-idBase)
        status = ((msg[1] & 0xE0) >> 5)
        if (status < 2 or status > 3):
            return
        self.data[track_id + "_track_oncoming"] = (msg[0] & 0x01)
        self.data[track_id + "_track_group_changed"] = ((msg[0] & 0x02) >> 1)
        self.data[track_id + "_track_lat_rate"] = ((msg[0] & 0xFC) >> 2)
        self.data[track_id + "_track_status"] = ((msg[1] & 0xE0) >> 5)
        self.data[track_id + "_track_angle"] = (((msg[1] & 0x1F) << 5) | ((msg[2] & 0xF8) >> 3)) # Spans multiple bytes
        self.data[track_id + "_track_range"] = (((msg[2] & 0x07) << 8) | msg[3]) # Spans multiple bytes
        self.data[track_id + "_track_bridge"] = ((msg[4] & 0x80) >> 7)
        self.data[track_id + "_track_rolling_count"] = ((msg[4] & 0x40) >> 6)
        self.data[track_id + "_track_width"] = ((msg[4] & 0x3C) >> 2)
        self.data[track_id + "_track_range_accel"] = (((msg[4] & 0x03) << 8) | msg[5]) # Spans multiple bytes
        self.data[track_id + "_track_med_range_mode"] = ((msg[6] & 0xC0) >> 6)
        self.data[track_id + "_track_range_rate"] = (((msg[6] & 0x3F) << 8) | msg[7]) # Spans multiple bytes

    def track_status_msg(self, msg_counter, msg):
        """ message ID x540 or 1344 """
        add_group = False
        for i in range(1, 8):
            track_id = str((msg_counter*7)+i)
            try:
                status = self.data[track_id + "_track_status"]
                add_group = True
            except KeyError:
                continue
            self.data[track_id + "_track_moving_fast"] = ((msg[i] & 0x80) >> 7)
            self.data[track_id + "_track_moving_slow"] = ((msg[i] & 0x40) >> 6)
            self.data[track_id + "_track_moving"] = ((msg[i] & 0x20) >> 5)
            self.data[track_id + "_track_power"] = (msg[i] & 0x1F)
            if ((msg_counter*7)+i) >= 64:
                break

        if add_group:
            group = str(msg_counter)
            self.data[group + "_weird_rolling_count"] = ((msg[0] & 0x10) >> 4)
            self.data[group + "_can_id_group"] = (msg[0] & 0x0F)

    def validation_msg_one(self, msg):
        """ message ID x5D0 or 1488 """
        # lr = Long Range
        self.data["valid_lr_serial_no"] = msg[0]
        self.data["valid_lr_range"] = (msg[1] << 8 | msg[2]) # spans multiple bytes
        self.data["valid_lr_range_rate"] = (msg[3] << 8 | msg[4]) # spans multiple bytes
        self.data["valid_lr_angle"] = (msg[5] << 8 | msg[6]) # spans multiple bytes
        self.data["valid_lr_power"] = msg[7]

    def validation_msg_two(self, msg):
        """ message ID x501 or 1488 """
        # mr = Mid Range
        self.data["valid_mr_serial_no"] = msg[0]
        self.data["valid_mr_range"] = (msg[1] << 8 | msg[2]) # spans multiple bytes
        self.data["valid_mr_range_rate"] = (msg[3] << 8 | msg[4]) # spans multiple bytes
        self.data["valid_mr_angle"] = (msg[5] << 8 | msg[6]) # spans multiple bytes
        self.data["valid_mr_power"] = msg[7]

    def additional_status_one(self, msg):
        """ message ID x5E4 or 1508 """
        self.data["switched_battery_ad"] = msg[0]
        self.data["ignition_ad"] = msg[1]
        self.data["thermistor_1_ad"] = msg[2]
        if len(msg) > 3:
            self.data["thermistor_2_ad"] = msg[3]
            self.data["5va_supply_ad"] = msg[4]
            self.data["5vdx_supply_ad"] = msg[5]
            self.data["3.3v_supply_ad"] = msg[6]
            self.data["10v_supply_ad"] = msg[7]

    def additional_status_two(self, msg):
        """
        message ID x5E5 or 1509

        Byte 0 - 1.8V supply A/D reading
        Byte 1 - -5V supply A/D reading
        Byte 2 - Wave Diff A/D reading
        Byte 3 bits 4-7 - DSP SW Version 3rd byte
        Byte 3 bit 3 - Vertical Align Updated
        Byte 3 bits 0-2 - System Power Mode
        1 - RADIATE_OFF, 2 - RADIATE_ON
        Byte 4 bit 7 - Found Target
        Byte 4 bit 6 - Recommend Unconverge
        Byte 4 bits 3-5 - Factory Align Status 1
        Byte 4 bits 0-2 - Factory Align Status 2
        Byte 5 - Factory Misalignment
        Byte 6 - Serv Align Updates Done
        Byte 7 - Vertical Misalignment
        """
        self.data["1.8v_supply_ad_reading"] = msg[0]
        self.data["-5v_supply_ad_reading"] = msg[1]
        self.data["wave_diff_ad_reading"] = msg[2]
        self.data["dsp_sw_version_3rd_byte"] = ((msg[3] & 0xF0) >> 4)
        self.data["vertical_align_updated"] = ((msg[3] & 0x08) >> 3)
        self.data["system_power_mode"] = ((msg[3] & 0x07) >> 2)
        self.data["found_target"] = ((msg[4] & 0x80) >> 7)
        self.data["recommend_unconverge"] = ((msg[4] & 0x40) >> 6)
        self.data["factory_align_status_1"] = ((msg[4] & 0x38) >> 3)
        self.data["factory_align_status_2"] = (msg[4] & 0x07)
        self.data["factory_misalignment"] = msg[5]
        self.data["serv_align_updates_done"] = msg[6]
        self.data["vertical_misalignment"] = msg[7]

    def additional_status_three(self, msg):
        """ message ID x5E6 or 1510 """
        # Byte x - Active Fault x
        self.data["active_fault_0"] = msg[0]
        self.data["active_fault_1"] = msg[1]
        self.data["active_fault_2"] = msg[2]
        self.data["active_fault_3"] = msg[3]
        self.data["active_fault_4"] = msg[4]
        self.data["active_fault_5"] = msg[5]
        self.data["active_fault_6"] = msg[6]
        self.data["active_fault_7"] = msg[7]

    def additional_status_four(self, msg):
        """ message ID x5E7 or 1511 """
        self.data["history_fault_0"] = msg[0]
        self.data["history_fault_1"] = msg[1]
        self.data["history_fault_2"] = msg[2]
        self.data["history_fault_3"] = msg[3]
        self.data["history_fault_4"] = msg[4]
        self.data["history_fault_5"] = msg[5]
        self.data["history_fault_6"] = msg[6]
        self.data["history_fault_7"] = msg[7]

    def additional_status_five(self, msg):
        """ message ID x5E8 or 1512 """
        self.data["average_power_cw_blockage_algo"] = (msg[0] << 4 | ((msg[1] & 0xF0) >> 4)) # spans multiple bytes
        self.data["sideslip_angle"] = (((msg[1] & 0x03) << 8) | msg[2]) # spans multiple bytes
        self.data["serial_no_3rd_byte"] = msg[3]
        self.data["water_spray_target_id"] = ((msg[4] & 0xFE) >> 1)
        self.data["filtered_xohp_of_acc_cipv_target"] = ((msg[4] & 0x01) << 8 | msg[5])
        self.data["path_id_acc_2"] = msg[6]
        self.data["path_id_acc_3"] = msg[7]

    def status_one(self, msg):
        """ message ID x4E0 or 1248 """
        self.data["status_1_rolling_count"] = ((msg[0] & 0xC0) >> 6)
        self.data["dsp_timestamp"] = (((msg[0] & 0x3F) << 1) | ((msg[1] & 0x80) >> 7)) # Spans multiple bytes
        self.data["comm_error"] = ((msg[1] & 0x40) >> 6)
        self.data["radius_curvature"] = (((msg[1] & 0x3F) << 8) | msg[2]) # Spans multiple bytes
        self.data["scan_index"] = ((msg[3] << 8) | msg[4]) # Spans multiple bytes
        self.data["yaw_rate"] = ((msg[5] << 4) | ((msg[6] & 0xF0) >> 4)) # Spans multiple bytes
        self.data["vehicle_speed"] = (((msg[6] & 0x07) << 8) | msg[7]) # Spans multiple bytes

    def status_two(self, msg):
        """ message ID x4E1 or 1249
        Byte 0 bits 0-1 - Rolling Count
        Byte 0 bits 2-7 - Maximum tracks (number of objects of interest)
        Byte 1 bit 7 - Overheat Error
        Byte 1 bit 6 - Range Perf Error
        Byte 1 bit 5 - Internal Error
        Byte 1 bit 4 - XCVR Operational
        0 - Not radiating, 1 - radiating
        Byte 1 bit 3 - Raw Data Mode
        Byte 1 bits 0-2, Byte 2 - Steering Angle Ack
        Byte 3 - Temperature
        Byte 4 bits 2-7 - Speed Comp Factor
        Byte 4 bits 0-1 - Grouping Mode
        Byte 5 - Yaw Rate Bias
        Bytes 6-7 - SW Version DSP
        """
        self.data["status_two_rolling_count"] = (msg[0] & 0x03)
        self.data["maximum_tracks"] = ((msg[0] & 0xFC) >> 2)
        self.data["overheat_error"] = ((msg[1] & 0x80) >> 7)
        self.data["range_perf_error"] = ((msg[1] & 0x40) >> 6)
        self.data["internal_error"] = ((msg[1] & 0x20) >> 5)
        self.data["radiating"] = ((msg[1] & 0x10) >> 4)
        self.data["raw_data_mode"] = ((msg[1] & 0x08) >> 3)
        self.data["steering_angle_ack"] = (((msg[1] & 0x07) << 8) | msg[2]) # spans multiple bytes
        self.data["temperature"] = msg[3]
        self.data["speed_comp_factor"] = ((msg[4] & 0xFC) >> 2)
        self.data["grouping_mode"] = (msg[4] & 0x03)
        self.data["yaw_rate_bias"] = msg[5]
        self.data["sw_version_dsp"] = ((msg[6] << 8) | msg[7]) # spans multiple bytes

    def status_three(self, msg):
        """ message ID x4E2 or 1250 """
        self.data["interface_version"] = ((msg[0] & 0xF0) >> 4)
        self.data["hw_version"] = (msg[0] & 0x0F)
        self.data["sw_version_host"] = (msg[1] << 16 | msg[2] << 8 | msg[3]) # Spans multiple bytes
        self.data["serial_num"] = (msg[4] << 16 | msg[5] << 8 | msg[6]) # Spans multiple bytes
        self.data["sw_version_pld"] = msg[7]

    def status_four(self, msg):
        """ message ID x4E3 or 1251

        Byte 0 bit 7 - Truck Target
        Byte 0 bit 6 - Only Grating Lobe
        Byte 0 bit 5 - Sidelobe Blockage
        Byte 0 bit 4 - Partial Blockage
        Byte 0 bits 2-3 - MR/LR Mode
        Byte 0 bits 0-1 - Rolling Count
        Byte 1 - Path ID ACC
        Byte 2 - Path ID CMBB Move
        Byte 3 - Path ID CMBB Stat
        Byte 4 - Path ID FCW Move
        Byte 5 - Path ID FCW Stat
        Byte 6 - Auto Align Angle
        Byte 7 - Path ID ACC Stat
        """
        self.data["truck_target"] = ((msg[0] & 0x80) >> 7)
        self.data["only_grating_lobe"] = ((msg[0] & 0x40) >> 6)
        self.data["sidelobe_blockage"] = ((msg[0] & 0x20) >> 5)
        self.data["partial_blockage"] = ((msg[0] & 0x10) >> 4)
        self.data["mr_lr_mode"] = ((msg[0] & 0x0C) >> 2)
        self.data["status_4_rolling_count"] = (msg[0] & 0x03)
        self.data["path_id_acc"] = msg[1]
        self.data["path_id_cmbb_move"] = msg[2]
        self.data["path_id_cmbb_stat"] = msg[3]
        self.data["path_id_fcw_move"] = msg[4]
        self.data["path_id_fcw_stat"] = msg[5]
        self.data["auto_align_angle"] = msg[6]
        self.data["path_id_acc_stat"] = msg[7]
