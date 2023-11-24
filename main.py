from dataclasses import dataclass
from pprint import pprint
import math
import numpy as np
import socket
import struct
import sys

from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsLineItem, \
    QVBoxLayout, QWidget, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QIcon, QPixmap

from hud import Ui_MainWindow  # 导入生成的UI文件
import hud_media_rc  # 导入资源文件


@dataclass
class DataFrameStart:
    shiftlights_rpm_start: float
    shiftlights_rpm_end: float
    vehicle_gear_index_neutral: int
    vehicle_gear_index_reverse: int
    vehicle_gear_maximum: int
    vehicle_engine_rpm_max: float
    vehicle_engine_rpm_idle: float
    stage_length: float


@dataclass
class DataFrameUpdate:
    game_delta_time: float
    shiftlights_fraction: float
    shiftlights_rpm_valid: bool
    vehicle_gear_index: int
    vehicle_speed: float
    vehicle_transmission_speed: float
    vehicle_position_x: float
    vehicle_position_y: float
    vehicle_position_z: float
    vehicle_velocity_x: float
    vehicle_velocity_y: float
    vehicle_velocity_z: float
    vehicle_acceleration_x: float
    vehicle_acceleration_y: float
    vehicle_acceleration_z: float
    vehicle_left_direction_x: float
    vehicle_left_direction_y: float
    vehicle_left_direction_z: float
    vehicle_forward_direction_x: float
    vehicle_forward_direction_y: float
    vehicle_forward_direction_z: float
    vehicle_up_direction_x: float
    vehicle_up_direction_y: float
    vehicle_up_direction_z: float
    vehicle_hub_position_bl: float
    vehicle_hub_position_br: float
    vehicle_hub_position_fl: float
    vehicle_hub_position_fr: float
    vehicle_hub_velocity_bl: float
    vehicle_hub_velocity_br: float
    vehicle_hub_velocity_fl: float
    vehicle_hub_velocity_fr: float
    vehicle_cp_forward_speed_bl: float
    vehicle_cp_forward_speed_br: float
    vehicle_cp_forward_speed_fl: float
    vehicle_cp_forward_speed_fr: float
    vehicle_brake_temperature_bl: float
    vehicle_brake_temperature_br: float
    vehicle_brake_temperature_fl: float
    vehicle_brake_temperature_fr: float
    vehicle_engine_rpm_current: float
    vehicle_throttle: float
    vehicle_brake: float
    vehicle_clutch: float
    vehicle_steering: float
    vehicle_handbrake: float
    stage_current_time: float
    stage_current_distance: float


@dataclass
class DataFrameEnd:
    stage_current_time: float
    stage_current_distance: float


class ListenerStart(QThread):
    update_signal = pyqtSignal(DataFrameStart)

    def run(self):
        # 创建一个UDP套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 绑定服务器地址和端口
        server_address = ('localhost', 20778)
        server_socket.bind(server_address)

        print('开始监听区间开始...')

        while True:
            data, client_address = server_socket.recvfrom(1024)
            data_list = struct.unpack("<ffBBBffd", data)
            self.update_signal.emit(DataFrameStart(*data_list))


class ListenerEnd(QThread):
    update_signal = pyqtSignal(DataFrameEnd)

    def run(self):
        # 创建一个UDP套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 绑定服务器地址和端口
        server_address = ('localhost', 20779)
        server_socket.bind(server_address)

        print('开始监听区间打断...')

        while True:
            data, client_address = server_socket.recvfrom(1024)
            data_list = struct.unpack("<fd", data)
            self.update_signal.emit(DataFrameEnd(*data_list))


class ListenerUpdate(QThread):
    update_signal = pyqtSignal(DataFrameUpdate)

    def run(self):
        # 创建一个UDP套接字
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 绑定服务器地址和端口
        server_address = ('localhost', 20777)
        server_socket.bind(server_address)

        print('开始监听区间更新...')

        while True:
            data, client_address = server_socket.recvfrom(1024)
            data_list = struct.unpack("<ff?Bfffffffffffffffffffffffffffffffffffffffffffd", data)
            self.update_signal.emit(DataFrameUpdate(*data_list))


class MyMainWindow(QMainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()

        # 使用生成的UI文件创建UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.var_init()  # 初始化变量
        self.ai_init()  # 姿态仪初始化
        self.ui_addition_set()  # 额外设置ui
        self.start_listeners()  # 开始监听

    def var_init(self):
        self.stage_length = None
        self.fresh_timer = 0

    def ai_init(self):
        """姿态表初始化"""

        scene = QGraphicsScene()
        view = self.ui.view_ai
        view.setScene(scene)

        view.setSceneRect(0, 0, 80, 80)

        # 天
        self.ai_sky = QGraphicsRectItem(-40, -40, 160, 80)
        self.ai_sky.setBrush(QColor(33, 148, 255))
        scene.addItem(self.ai_sky)
        self.ai_sky.setTransformOriginPoint(40, 40)

        # 地
        self.ai_land = QGraphicsRectItem(-40, 40, 160, 80)
        self.ai_land.setBrush(QColor(185, 119, 44))
        scene.addItem(self.ai_land)
        self.ai_land.setTransformOriginPoint(40, 40)

        # 标线l
        self.ai_line_l = QGraphicsRectItem(15, 39, 20, 2)
        self.ai_line_l.setBrush(Qt.green)
        scene.addItem(self.ai_line_l)

        # 标线m
        self.ai_line_m = QGraphicsRectItem(39, 39, 2, 2)
        self.ai_line_m.setBrush(Qt.green)
        scene.addItem(self.ai_line_m)

        # 标线r
        self.ai_line_r = QGraphicsRectItem(45, 39, 20, 2)
        self.ai_line_r.setBrush(Qt.green)
        scene.addItem(self.ai_line_r)

    def ui_addition_set(self):
        """程序化设置ui参数"""
        # 离合、刹车、油门百分比
        self.bar_clutch_max = 1000
        self.ui.bar_clutch.setMaximum(self.bar_clutch_max)
        self.bar_brake_max = 1000
        self.ui.bar_brake.setMaximum(self.bar_brake_max)
        self.bar_throttle_max = 1000
        self.ui.bar_throttle.setMaximum(self.bar_throttle_max)

        # 所有LCD黑暗模式
        addition_css = """
            QLCDNumber {
                color:white;
            }
            
            #lcd_gear {
                border: 1px solid white;
            }
        """

        # 详细区黑暗模式
        # 轮胎
        addition_css += """
            #wheel_fl, #wheel_fr, #wheel_bl, #wheel_br{
                background: black;
                border: 2px solid white;
            }
        """
        # 差速器
        addition_css += """
            #diff_b, #diff_f {
                background:black;
                border: 1px solid white;
            }
        """
        # 所有label
        addition_css += """
            QLabel {
                color:white;
            }
        """

        # 所有groupbox
        addition_css += """
            QGroupBox:title {
                color: white;
            }
        """

        latest_css = self.styleSheet() + addition_css
        self.setStyleSheet(latest_css)

        # 驱动轴
        self.ui.shaft_1.setStyleSheet("color: white;")
        self.ui.shaft_2.setStyleSheet("color: white;")
        self.ui.shaft_3.setStyleSheet("color: white;")
        self.ui.shaft_4.setStyleSheet("color: white;")
        self.ui.shaft_5.setStyleSheet("color: white;")
        self.ui.shaft_6.setStyleSheet("color: white;")
        self.ui.shaft_7.setStyleSheet("color: white;")

        self.ui.panel_compass.setVisible(False)

    def start_listeners(self):
        """启动监听线程"""
        self.listener_start = ListenerStart()
        self.listener_start.update_signal.connect(self.heard_start)
        self.listener_start.start()

        self.listener_end = ListenerEnd()
        self.listener_end.update_signal.connect(self.heard_end)
        self.listener_end.start()

        self.listener_update = ListenerUpdate()
        self.listener_update.update_signal.connect(self.heard_update)
        self.listener_update.start()

    def heard_start(self, d: DataFrameStart):
        """启动触发"""
        self.stage_length = d.stage_length

        # 初始化里程表
        self.update_odo(stage_length=self.stage_length)
        self.ui.lcd_cd_0.setProperty("intValue", 0)
        self.ui.lcd_cd_1.setProperty("intValue", 0)
        self.ui.bar_distance.setValue(0)

    def heard_end(self, d: DataFrameEnd):
        """打断触发"""
        # 更新计时器
        self.update_timer(d.stage_current_time)

    def heard_update(self, d: DataFrameUpdate):
        """更新触发"""
        # 降低更新频率
        self.fresh_timer += d.game_delta_time
        if self.fresh_timer < 1 / 30:
            return
        else:
            self.fresh_timer = 0

        # 更新离合、刹车、油门条
        self.ui.bar_clutch.setValue(percent(d.vehicle_clutch, self.bar_clutch_max))
        self.ui.bar_brake.setValue(percent(d.vehicle_brake, self.bar_brake_max))
        self.ui.bar_throttle.setValue(percent(d.vehicle_throttle, self.bar_throttle_max))

        # 更新档位
        self.ui.lcd_gear.setProperty("intValue", d.vehicle_gear_index)

        # 更新转向
        self.update_steering_bar(d.vehicle_steering)

        # 更新换挡提示器
        _ = self.update_shiftlights(d.shiftlights_fraction) if d.shiftlights_rpm_valid else self.update_shiftlights(-1)

        # 更新计时器
        self.update_timer(d.stage_current_time)

        # 更新手刹提示
        self.update_handbrake(d.vehicle_handbrake)

        # 更新刹车盘温度
        self.update_brake_temperature(d.vehicle_brake_temperature_fl, d.vehicle_brake_temperature_fr,
                                      d.vehicle_brake_temperature_bl, d.vehicle_brake_temperature_br)

        # 更新车体速度
        self.ui.lcd_body_speed.setProperty("intValue", int(d.vehicle_speed * 3.6))

        # 更新驱动系统速度
        self.ui.lcd_trans_speed.setProperty("intValue", int(d.vehicle_transmission_speed * 3.6))

        # 更新里程表
        self.update_odo(current_distance=d.stage_current_distance)

        # 更新GPS
        self.update_gps(d.vehicle_position_x, d.vehicle_position_y, d.vehicle_position_z)

        # 更新弹簧压缩
        self.update_spring(d.vehicle_hub_position_fl, d.vehicle_hub_position_fr,
                           d.vehicle_hub_position_bl, d.vehicle_hub_position_br)

        # 更新姿态仪和指南针
        self.update_ai_and_compass(np.array(
            [[d.vehicle_left_direction_x, d.vehicle_left_direction_y, d.vehicle_left_direction_z],
             [d.vehicle_up_direction_x, d.vehicle_up_direction_y, d.vehicle_left_direction_z],
             [d.vehicle_forward_direction_x, d.vehicle_forward_direction_y, d.vehicle_forward_direction_z]]))

    def update_steering_bar(self, steering: float):
        """更新转向显示"""
        if steering < 0:
            self.ui.bar_steering_l.setValue(percent(-steering))
            self.ui.bar_steering_r.setValue(0)
        else:
            self.ui.bar_steering_l.setValue(0)
            self.ui.bar_steering_r.setValue(percent(steering))

    def update_shiftlights(self, f: float):
        """更新换挡提示器"""
        if f == -1:
            self.ui.rpm_light_l_1.setVisible(False)
            self.ui.rpm_light_l_2.setVisible(False)
            self.ui.rpm_light_l_3.setVisible(False)
            self.ui.rpm_light_l_4.setVisible(False)
            self.ui.rpm_light_r_1.setVisible(False)
            self.ui.rpm_light_r_2.setVisible(False)
            self.ui.rpm_light_r_3.setVisible(False)
            self.ui.rpm_light_r_4.setVisible(False)
            self.ui.rpm_light_m_1.setVisible(False)
            self.ui.rpm_light_m_2.setVisible(False)
        if f < .1:
            self.ui.rpm_light_l_1.setVisible(True)
            self.ui.rpm_light_r_1.setVisible(True)
            self.ui.rpm_light_l_2.setVisible(False)
            self.ui.rpm_light_r_2.setVisible(False)
            self.ui.rpm_light_l_3.setVisible(False)
            self.ui.rpm_light_r_3.setVisible(False)
            self.ui.rpm_light_l_4.setVisible(False)
            self.ui.rpm_light_r_4.setVisible(False)
            self.ui.rpm_light_m_1.setVisible(False)
            self.ui.rpm_light_m_2.setVisible(False)
        elif f < .4:
            self.ui.rpm_light_l_1.setVisible(True)
            self.ui.rpm_light_r_1.setVisible(True)
            self.ui.rpm_light_l_2.setVisible(True)
            self.ui.rpm_light_r_2.setVisible(True)
            self.ui.rpm_light_l_3.setVisible(False)
            self.ui.rpm_light_r_3.setVisible(False)
            self.ui.rpm_light_l_4.setVisible(False)
            self.ui.rpm_light_r_4.setVisible(False)
            self.ui.rpm_light_m_1.setVisible(False)
            self.ui.rpm_light_m_2.setVisible(False)
        elif f < .7:
            self.ui.rpm_light_l_1.setVisible(True)
            self.ui.rpm_light_r_1.setVisible(True)
            self.ui.rpm_light_l_2.setVisible(True)
            self.ui.rpm_light_r_2.setVisible(True)
            self.ui.rpm_light_l_3.setVisible(True)
            self.ui.rpm_light_r_3.setVisible(True)
            self.ui.rpm_light_l_4.setVisible(False)
            self.ui.rpm_light_r_4.setVisible(False)
            self.ui.rpm_light_m_1.setVisible(False)
            self.ui.rpm_light_m_2.setVisible(False)
        elif f < 1:
            self.ui.rpm_light_l_1.setVisible(True)
            self.ui.rpm_light_r_1.setVisible(True)
            self.ui.rpm_light_l_2.setVisible(True)
            self.ui.rpm_light_r_2.setVisible(True)
            self.ui.rpm_light_l_3.setVisible(True)
            self.ui.rpm_light_r_3.setVisible(True)
            self.ui.rpm_light_l_4.setVisible(True)
            self.ui.rpm_light_r_4.setVisible(True)
            self.ui.rpm_light_m_1.setVisible(False)
            self.ui.rpm_light_m_2.setVisible(False)
        else:
            self.ui.rpm_light_l_1.setVisible(False)
            self.ui.rpm_light_r_1.setVisible(False)
            self.ui.rpm_light_l_2.setVisible(False)
            self.ui.rpm_light_r_2.setVisible(False)
            self.ui.rpm_light_l_3.setVisible(True)
            self.ui.rpm_light_r_3.setVisible(True)
            self.ui.rpm_light_l_4.setVisible(True)
            self.ui.rpm_light_r_4.setVisible(True)
            self.ui.rpm_light_m_1.setVisible(True)
            self.ui.rpm_light_m_2.setVisible(True)

    def update_timer(self, time: float):
        """更新计时器"""
        time = int(time * 1000)
        ms = str(time % 1000).zfill(3)  # 毫秒数
        sec = str(time // 1000 % 60).zfill(2)  # 秒数
        min = str(time // 1000 // 60).zfill(2)  # 分钟数

        self.ui.lcd_timer_ms_0.setProperty("intValue", ms[0])
        self.ui.lcd_timer_ms_1.setProperty("intValue", ms[1])
        self.ui.lcd_timer_ms_2.setProperty("intValue", ms[2])

        self.ui.lcd_timer_sec_0.setProperty("intValue", sec[0])
        self.ui.lcd_timer_sec_1.setProperty("intValue", sec[1])

        self.ui.lcd_timer_min_0.setProperty("intValue", min[0])
        self.ui.lcd_timer_min_1.setProperty("intValue", min[1])

    def update_handbrake(self, f: float):
        if f > .5:
            self.ui.lcd_gear.setStyleSheet('QLCDNumber { color: red; }')
        else:
            self.ui.lcd_gear.setStyleSheet('QLCDNumber { color: white; }')

    def update_brake_temperature(self, fl, fr, bl, br):
        max_temp = 300
        if fl or fr or bl or br:
            if 0 < fl < max_temp:
                self.ui.bar_temp_fl.setValue(percent(fl / max_temp))
            else:
                self.ui.bar_temp_fl.setValue(0)
            if 0 < fr < max_temp:
                self.ui.bar_temp_fr.setValue(percent(fr / max_temp))
            else:
                self.ui.bar_temp_fr.setValue(0)
            if 0 < bl < max_temp:
                self.ui.bar_temp_bl.setValue(percent(bl / max_temp))
            else:
                self.ui.bar_temp_bl.setValue(0)
            if 0 < br < max_temp:
                self.ui.bar_temp_br.setValue(percent(br / max_temp))
            else:
                self.ui.bar_temp_br.setValue(0)
        else:
            self.ui.bar_temp_fl.setValue(100)
            self.ui.bar_temp_fr.setValue(100)
            self.ui.bar_temp_bl.setValue(100)
            self.ui.bar_temp_br.setValue(100)

    def update_odo(self, stage_length: float = None, current_distance: float = None):
        if stage_length:
            self.ui.lcd_sl_0.setProperty("intValue", stage_length // 1000)
            self.ui.lcd_sl_1.setProperty("intValue", int(stage_length % 1000 / 100))
        elif stage_length == -1:
            self.ui.lcd_sl_0.setProperty("intValue", 0)
            self.ui.lcd_sl_1.setProperty("intValue", 0)

        if current_distance:
            self.ui.lcd_cd_0.setProperty("intValue", current_distance // 1000)
            self.ui.lcd_cd_1.setProperty("intValue", int(current_distance % 1000 / 100))

            if self.stage_length:
                self.ui.bar_distance.setValue(percent(current_distance / self.stage_length))
            else:
                self.ui.bar_distance.setValue(0)

        elif current_distance == -1:
            self.ui.lcd_cd_0.setProperty("intValue", 0)
            self.ui.lcd_cd_1.setProperty("intValue", 0)

    def update_gps(self, x, y, z):
        self.ui.lcd_gps_x_0.setProperty("intValue", int(x))
        self.ui.lcd_gps_x_1.setProperty("intValue", int(x * 10 % 10))
        self.ui.lcd_gps_y_0.setProperty("intValue", int(y))
        self.ui.lcd_gps_y_1.setProperty("intValue", int(y * 10 % 10))
        self.ui.lcd_gps_z_0.setProperty("intValue", int(z))
        self.ui.lcd_gps_z_1.setProperty("intValue", int(z * 10 % 10))

    def update_spring(self, fl, fr, bl, br):
        max = 10
        if fl < max:
            self.ui.bar_spring_fl.setValue(percent(-fl * 100 / max))
        else:
            self.ui.bar_spring_fl.setValue(100)
        if fr < max:
            self.ui.bar_spring_fr.setValue(percent(-fr * 100 / max))
        else:
            self.ui.bar_spring_fr.setValue(100)
        if bl < max:
            self.ui.bar_spring_bl.setValue(percent(-bl * 100 / max))
        else:
            self.ui.bar_spring_bl.setValue(100)
        if br < max:
            self.ui.bar_spring_br.setValue(percent(-br * 100 / max))
        else:
            self.ui.bar_spring_br.setValue(100)

    def update_ai_and_compass(self, array):
        eular = rot2euler(array)
        ai_pitch = eular[0]
        if ai_pitch < -90:
            ai_pitch = 180 + ai_pitch
        elif ai_pitch > 90:
            ai_pitch = 180 - ai_pitch

        ai_yaw = eular[1]

        ai_roll = eular[2]
        if ai_roll < -90:
            ai_roll = 180 + ai_roll
        elif ai_roll > 90:
            ai_roll = 180 - ai_roll
        ai_roll = -ai_roll

        # print("俯仰:{:.1f}° 偏航:{:.1f}° 翻滚:{:.1f}°".format(ai_pitch, ai_yaw, ai_roll))

        # 更新ui
        self.ai_sky.setPos(0, int(ai_pitch))
        self.ai_land.setPos(0, int(ai_pitch))
        self.ai_sky.setRotation(ai_roll)
        self.ai_land.setRotation(ai_roll)

        # 更新指南针
        # self.ui.slider_compass.setValue(int(ai_yaw))


def rot2euler(R):
    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6
    if not singular:
        x = math.atan2(R[2, 1], R[2, 2]) * 180 / np.pi
        y = math.atan2(-R[2, 0], sy) * 180 / np.pi
        z = math.atan2(R[1, 0], R[0, 0]) * 180 / np.pi
    else:
        x = math.atan2(-R[1, 2], R[1, 1]) * 180 / np.pi
        y = math.atan2(-R[2, 0], sy) * 180 / np.pi
        z = 0
    return np.array([x, y, z])


def percent(i: float, max: int = 100) -> int:
    return int(i * max)


if __name__ == "__main__":
    __version__ = "0.0.1"

    # 启用任务栏icon
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # 启用HD缩放

    app = QApplication(sys.argv)
    mainWindow = MyMainWindow()

    mainWindow.setWindowTitle("EA WRC HUD by CaliFall V{}".format(__version__))  # 设置软件标题

    # 设置软件icon
    icon = QIcon()
    icon.addPixmap(QPixmap(":/Media/logo.ico"), QIcon.Normal, QIcon.Off)
    mainWindow.setWindowIcon(icon)

    mainWindow.show()
    sys.exit(app.exec_())
