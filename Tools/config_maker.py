import json
from pprint import pprint


def read_channels_file() -> dict:
    channels_route = "C:/Users/Vip3ria/Documents/My Games/WRC/telemetry/readme/channels.json"
    with open(channels_route, "r", encoding="utf8") as f:
        content = f.read()
    content = json.loads(content)
    return content


def make_config(content):
    config_route = "C:/Users/Vip3ria/Documents/My Games/WRC/telemetry/udp/cali_auto.json"
    with open(config_route, "w+", encoding="utf8") as f:
        f.write(content)


if __name__ == "__main__":

    type_dict = {
        "float32" : "f",
        "float64": "d",
        "uint8": "B",
        "boolean": "?"
    }

    channels_dict = read_channels_file()

    channel_list_start = [
        "shiftlights_rpm_start",
        "shiftlights_rpm_end",
        "vehicle_gear_index_neutral",
        "vehicle_gear_index_reverse",
        "vehicle_gear_maximum",
        "vehicle_engine_rpm_max",
        "vehicle_engine_rpm_idle",
        "stage_length"
    ]

    channel_list_update = [
        "game_delta_time",
        "shiftlights_fraction",
        "shiftlights_rpm_valid",
        "vehicle_gear_index",
        "vehicle_speed",
        "vehicle_transmission_speed",
        "vehicle_position_x",
        "vehicle_position_y",
        "vehicle_position_z",
        "vehicle_velocity_x",
        "vehicle_velocity_y",
        "vehicle_velocity_z",
        "vehicle_acceleration_x",
        "vehicle_acceleration_y",
        "vehicle_acceleration_z",
        "vehicle_left_direction_x",
        "vehicle_left_direction_y",
        "vehicle_left_direction_z",
        "vehicle_forward_direction_x",
        "vehicle_forward_direction_y",
        "vehicle_forward_direction_z",
        "vehicle_up_direction_x",
        "vehicle_up_direction_y",
        "vehicle_up_direction_z",
        "vehicle_hub_position_bl",
        "vehicle_hub_position_br",
        "vehicle_hub_position_fl",
        "vehicle_hub_position_fr",
        "vehicle_hub_velocity_bl",
        "vehicle_hub_velocity_br",
        "vehicle_hub_velocity_fl",
        "vehicle_hub_velocity_fr",
        "vehicle_cp_forward_speed_bl",
        "vehicle_cp_forward_speed_br",
        "vehicle_cp_forward_speed_fl",
        "vehicle_cp_forward_speed_fr",
        "vehicle_brake_temperature_bl",
        "vehicle_brake_temperature_br",
        "vehicle_brake_temperature_fl",
        "vehicle_brake_temperature_fr",
        "vehicle_engine_rpm_current",
        "vehicle_throttle",
        "vehicle_brake",
        "vehicle_clutch",
        "vehicle_steering",
        "vehicle_handbrake",
        "stage_current_time",
        "stage_current_distance"
    ]

    for c in channel_list_start:
        for channel in channels_dict["channels"]:
            if c == channel["id"]:
                print(type_dict[channel["type"]],end='')
                break

    print('')

    for c in channel_list_update:
        for channel in channels_dict["channels"]:
            if c == channel["id"]:
                print(type_dict[channel["type"]],end='')
                break


    # # 要存储进文件的内容
    # content = {}
    # content["versions"] = {"schema": 1, "data": 3}
    # content["id"] = "cali_auto"
    # content["header"] = {"channels": []}
    # content["packets"] = [
    #     {"id": "session_update",
    #      "channels": []}
    # ]
