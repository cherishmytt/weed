
#!C:\Python314\python.exe
"""
模拟树莓派客户端
按照通信机制与 Spring Boot 服务端进行 HTTP 通信
使用 rich 库实现实时监控面板
"""

import os
import sys
import random
import time
import datetime
import json
import threading
import signal
import logging
from pathlib import Path
from queue import Queue, Empty

import requests

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

# 配置信息
SERVER_BASE_URL = os.environ.get('RASPBERRY_SERVER_BASE_URL', 'http://localhost:8080')
USERNAME = os.environ.get('RASPBERRY_USERNAME', 'admin')
PASSWORD = os.environ.get('RASPBERRY_PASSWORD', '123456')

# 时间间隔配置（秒）- 测试加速版
STATUS_INTERVAL = float(os.environ.get('RASPBERRY_STATUS_INTERVAL_SECONDS', '0.02'))
MIN_POLL_INTERVAL = float(os.environ.get('RASPBERRY_MIN_POLL_INTERVAL_SECONDS', '0.3'))
MAX_POLL_INTERVAL = float(os.environ.get('RASPBERRY_MAX_POLL_INTERVAL_SECONDS', '0.8'))
MIN_DETECTION_INTERVAL = float(os.environ.get('RASPBERRY_MIN_DETECTION_INTERVAL_SECONDS', '5'))
MAX_DETECTION_INTERVAL = float(os.environ.get('RASPBERRY_MAX_DETECTION_INTERVAL_SECONDS', '10'))

# 起始 GPS 坐标
START_LONGITUDE = float(os.environ.get('RASPBERRY_START_LONGITUDE', '116.310000'))
START_LATITUDE = float(os.environ.get('RASPBERRY_START_LATITUDE', '39.990000'))
LONGITUDE_RANGE = 0.005
LATITUDE_RANGE = 0.005

# 示例图片目录
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'samples')

# 日志队列（用于可视化显示）
log_queue = Queue(maxsize=100)
status_queue = Queue(maxsize=10)
detection_queue = Queue(maxsize=10)
command_queue = Queue(maxsize=20)

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put_nowait((record.levelname, msg))
        except:
            pass

# 配置日志 - 只输出到队列，不输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[QueueHandler()]
)
logger = logging.getLogger(__name__)


class RaspberryPiSimulator:
    """树莓派模拟器"""

    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.running = True
        self.sample_images = self._load_sample_images()

        # 状态变量
        self.battery = 100.0
        self.laser_on = False
        self.longitude = START_LONGITUDE
        self.latitude = START_LATITUDE
        self.initial_longitude = START_LONGITUDE
        self.initial_latitude = START_LATITUDE
        self.cpu_usage = 0
        self.temperature = 35
        self.speed = 0

        # 统计
        self.status_count = 0
        self.detection_count = 0
        self.command_count = 0
        self.last_status = None
        self.last_detection = None

        # 高优先级停止机制
        self.current_firing_cmd_id = None  # 当前正在执行的照射指令ID
        self.stop_requested = False  # 停止标志

    def _get_current_timestamp(self):
        return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

    def _get_today_date_string(self):
        return datetime.datetime.now().date().strftime('%Y-%m-%d')

    def _load_sample_images(self):
        samples = list(Path(SAMPLES_DIR).glob('*.jpg'))
        samples += list(Path(SAMPLES_DIR).glob('*.jpeg'))
        samples += list(Path(SAMPLES_DIR).glob('*.png'))
        return samples

    def _get_headers(self):
        if not self.token:
            return {}
        return {'Authorization': f'Bearer {self.token}'}

    def login(self):
        url = f'{SERVER_BASE_URL}/api/v1/auth/login'
        data = {'username': USERNAME, 'password': PASSWORD}
        try:
            resp = requests.post(url, json=data, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get('code') == 200:
                    self.token = result['data']['token']
                    self.session.headers.update(self._get_headers())
                    logger.info(f"登录成功，用户: {result['data']['username']}")
                    return True
        except Exception as e:
            logger.error(f"登录异常: {e}")
        return False

    def generate_random_status(self):
        self.longitude += random.uniform(-0.0001, 0.0001)
        self.latitude += random.uniform(-0.0001, 0.0001)

        self.longitude = max(self.initial_longitude - LONGITUDE_RANGE,
                            min(self.initial_longitude + LONGITUDE_RANGE, self.longitude))
        self.latitude = max(self.initial_latitude - LATITUDE_RANGE,
                           min(self.initial_latitude + LATITUDE_RANGE, self.latitude))

        self.battery -= random.uniform(0.05, 0.15)
        self.battery = max(0, self.battery)

        self.cpu_usage = random.uniform(20, 80)
        self.temperature = 35 + (self.cpu_usage / 80) * 15 + random.uniform(-2, 2)
        self.speed = random.uniform(0, 1.5)

        imu = {
            'accel': {'x': random.uniform(-0.1, 0.1), 'y': random.uniform(-0.1, 0.1), 'z': 9.81 + random.uniform(-0.2, 0.2)},
            'gyro': {'x': random.uniform(-0.01, 0.01), 'y': random.uniform(-0.01, 0.01), 'z': random.uniform(-0.005, 0.005)},
            'pitch': random.uniform(-5, 5),
            'roll': random.uniform(-5, 5)
        }

        status = {
            'battery': round(self.battery, 1),
            'speed': round(self.speed, 2),
            'temperature': round(self.temperature, 1),
            'laserOn': self.laser_on,
            'cpuUsage': round(self.cpu_usage, 1),
            'longitude': round(self.longitude, 6),
            'latitude': round(self.latitude, 6),
            'imu': imu,
            'reportedAt': self._get_current_timestamp(),
            'reportDate': self._get_today_date_string()
        }
        return status

    def report_status(self):
        while self.running:
            if not self.token:
                time.sleep(1)
                continue

            status = self.generate_random_status()
            self.last_status = status

            try:
                url = f'{SERVER_BASE_URL}/api/v1/robot/status'
                resp = self.session.post(url, json=status, timeout=10)
                if resp.status_code == 200:
                    self.status_count += 1
                    status_queue.put(status)
                    logger.info(f"状态上报成功: 电量={status['battery']}%")
                elif resp.status_code == 401:
                    logger.warning("Token 失效，需要重新登录")
                    self.login()
            except Exception as e:
                logger.error(f"状态上报异常: {e}")

            time.sleep(STATUS_INTERVAL)

    def poll_commands(self):
        while self.running:
            if not self.token:
                time.sleep(1)
                continue

            try:
                url = f'{SERVER_BASE_URL}/api/v1/robot/commands/pending'
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('code') == 200:
                        commands = result['data']
                        if commands:
                            logger.info(f"获取到 {len(commands)} 条待执行指令")
                            for cmd in commands:
                                self._execute_command(cmd)
                elif resp.status_code == 401:
                    self.login()
            except Exception as e:
                logger.error(f"轮询指令异常: {e}")

            interval = random.uniform(MIN_POLL_INTERVAL, MAX_POLL_INTERVAL)
            time.sleep(interval)

    def _update_laser_status(self, status, status_text):
        """更新激光设备状态并上报到后端"""
        try:
            url = f'{SERVER_BASE_URL}/api/v1/robot/laser/status-update'
            data = {
                'status': status,
                'statusText': status_text,
                'timestamp': self._get_current_timestamp()
            }
            self.session.post(url, json=data, timeout=5)
        except Exception as e:
            pass  # 静默失败，不影响主流程

    def _check_stop_signal(self):
        """检查后端停止信号，返回 True 表示需要立即停止"""
        try:
            url = f'{SERVER_BASE_URL}/api/v1/robot/laser/status'
            resp = self.session.get(url, timeout=2)
            if resp.status_code == 200:
                result = resp.json()
                if result.get('code') == 200:
                    data = result.get('data', {})
                    # 检查是否为停止状态（待机但正在中断）
                    status = data.get('status', '')
                    status_text = data.get('statusText', '')
                    # 如果状态不是 firing（照射中），说明有停止信号
                    if status != 'firing' or '停止' in status_text or '中断' in status_text:
                        logger.info(f'检测到停止信号: status={status}, statusText={status_text}')
                        return True
        except Exception as e:
            pass  # 静默失败，继续执行
        return False

    def _execute_fire(self, cmd_id, command_id, duration_ms):
        """执行照射指令，支持中途停止（高优先级）"""
        self.current_firing_cmd_id = cmd_id
        self.stop_requested = False

        # ========== 先随机决定成功/失败 ==========
        # 如果一开始就失败，立即返回，不需要等照射时间
        will_succeed = random.random() < 0.9
        if not will_succeed:
            # 模拟启动失败：只等待 200ms 就返回失败
            time.sleep(0.2)
            logger.info(f'照射启动失败，立即反馈')
            self._update_laser_status('standby', '待机')
            self.current_firing_cmd_id = None
            self.stop_requested = False
            return 'FAILED', f'照射启动失败，执行时间: 200ms'

        # ========== 开始正常照射 ==========
        self._update_laser_status('firing', '照射中')

        # 分阶段休眠，每100ms检查一次停止标志和后端停止信号
        elapsed = 0
        interval = 0.1  # 100ms 检查一次
        total_time = duration_ms / 1000.0

        while elapsed < total_time and not self.stop_requested:
            time.sleep(interval)
            elapsed += interval
            # 每次都检查后端的停止信号（实时中断）
            if self._check_stop_signal():
                self.stop_requested = True
                logger.info(f'检测到后端停止信号，立即中断照射')
                break

        if self.stop_requested:
            # 被停止了
            result = 'SUCCESS'
            message = f'激光照射中断，实际执行: {int(elapsed * 1000)}ms'
        else:
            # 正常完成
            result = 'SUCCESS'
            message = f'照射完成，时长: {duration_ms}ms'

        self._update_laser_status('standby', '待机')
        self.current_firing_cmd_id = None
        self.stop_requested = False

        return result, message

    def _execute_command(self, cmd):
        cmd_id = cmd['id']
        command_id = cmd.get('commandId', f'cmd-{cmd_id}')
        action = cmd.get('action', 'UNKNOWN')
        params = cmd.get('params') or {}

        logger.info(f"开始执行指令: id={cmd_id}, action={action}")
        command_queue.put(('START', cmd_id, action, ''))

        # ========== 高优先级停止指令 ==========
        # 立即中断当前照射，不需要等执行完
        if action == 'STOP':
            # 设置停止标志，中断正在执行的照射
            if self.current_firing_cmd_id is not None:
                self.stop_requested = True
            # 快速响应，不需要等太久
            time.sleep(0.2)
            self._update_laser_status('standby', '照射已停止，待机中')
            result = 'SUCCESS'
            message = '停止指令执行成功'
        # ========== FIRE 照射指令（可被中断）==========
        elif action == 'FIRE':
            # FIRE 指令使用 duration 参数（毫秒）
            duration_ms = params.get('duration', 1000)
            result, message = self._execute_fire(cmd_id, command_id, duration_ms)
        # ========== 其他指令 ==========
        elif action == 'AIM':
            time.sleep(0.5)
            result = 'SUCCESS' if random.random() < 0.9 else 'FAILED'
            message = f'瞄准完成，坐标: X={params.get("targetX")}, Y={params.get("targetY")}'
            if result == 'SUCCESS':
                self._update_laser_status('aiming', '瞄准中')
        else:
            execution_time = {
                'ENABLE': 0.5, 'DISABLE': 0.3, 'SET_POWER': 0.4,
                'SELF_TEST': 1.5, 'RESET': 1.0
            }.get(action, 0.5)
            result = 'SUCCESS' if random.random() < 0.9 else 'FAILED'
            message = f'执行完成，{result}'

            if action == 'ENABLE':
                time.sleep(execution_time)
                self.laser_on = True
                self._update_laser_status('standby', '设备已连接，待机中')
            elif action == 'DISABLE':
                time.sleep(execution_time)
                self.laser_on = False
                self._update_laser_status('disconnected', '设备未连接')
            elif action == 'RESET':
                time.sleep(execution_time)
                self.laser_on = False
                self._update_laser_status('disconnected', '设备已复位，等待连接')
            elif action == 'SELF_TEST':
                time.sleep(execution_time)
                if result == 'SUCCESS':
                    self._update_laser_status('standby', '自检完成，待机中')
            elif action == 'SET_POWER':
                time.sleep(execution_time)
                message = f'功率设置成功: {params.get("power", 0)}W'
                self._update_laser_status('standby', f'当前功率: {params.get("power", 0)}W')
            else:
                time.sleep(execution_time)

        try:
            url = f'{SERVER_BASE_URL}/api/v1/robot/commands/{cmd_id}/ack'
            data = {'result': result, 'message': message, 'executedAt': self._get_current_timestamp()}
            resp = self.session.put(url, json=data, timeout=10)
            if resp.status_code == 200:
                self.command_count += 1
                command_queue.put(('END', cmd_id, action, result))
                logger.info(f"指令 {cmd_id} 确认成功")
        except Exception as e:
            logger.error(f"指令确认异常: {e}")

        # 激光反馈上报
        laser_feedback_status = 'N/A'
        if action in ['ENABLE', 'DISABLE', 'FIRE', 'STOP', 'SET_POWER', 'AIM', 'SELF_TEST', 'RESET']:
            laser_feedback_status = self._report_laser_feedback(command_id, action, result, message)

        # 更新指令状态（包含激光反馈结果）
        command_queue.put(('LASER', cmd_id, action, laser_feedback_status))

    def _report_laser_feedback(self, command_id, action, result, message):
        try:
            url = f'{SERVER_BASE_URL}/api/v1/robot/laser/feedback'
            data = {
                'commandId': command_id, 'action': action, 'result': result,
                'message': message, 'timestamp': self._get_current_timestamp(),
                'reportDate': self._get_today_date_string()
            }
            resp = self.session.post(url, json=data, timeout=10)
            if resp.status_code == 200:
                logger.info(f"激光反馈上报成功: commandId={command_id}, result={result}")
        except Exception as e:
            logger.error(f"激光反馈上报异常: {e}")

    def call_yolo_detection(self, image_path):
        url = f'{SERVER_BASE_URL}/api/v1/detection/yolo-predict'
        conf = float(os.environ.get('RASPBERRY_YOLO_CONF', '0.25'))
        classes = os.environ.get('RASPBERRY_YOLO_CLASSES', '')

        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                data = {'conf': str(conf)}
                if classes and classes.strip():
                    data['classes'] = classes.strip()

                logger.info(f"调用YOLO检测: {image_path.name}")
                start_time = time.time()
                resp = self.session.post(url, files=files, data=data, timeout=60)
                elapsed_ms = int((time.time() - start_time) * 1000)

                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('code') == 200:
                        data = result['data']
                        logger.info(f"YOLO检测完成: 耗时={data.get('elapsedMs', elapsed_ms)}ms")
                        return data
        except Exception as e:
            logger.error(f"YOLO检测异常: {e}", exc_info=True)
        return None

    def count_weed_and_crop(self, detections):
        crop_count = 0
        weed_count = 0
        for det in detections:
            class_id = det.get('classId')
            class_name = det.get('className', '')
            if class_id == 0 or class_name.lower() == 'crop':
                crop_count += 1
            else:
                weed_count += 1
        return weed_count, crop_count

    def get_result_image_local_path(self, yolo_data, base_upload_path):
        prediction = yolo_data.get('result', {})
        output_url = prediction.get('outputImageUrl')
        if not output_url:
            return None
        relative_path = output_url.replace('/files/', '')
        local_path = os.path.join(base_upload_path, relative_path)
        return Path(local_path)

    def report_detection(self):
        if not self.sample_images or not self.token:
            return

        base_upload_path = os.environ.get('FILE_STORAGE_BASE_PATH', './uploads')
        if not os.path.isabs(base_upload_path):
            base_upload_path = os.path.join(os.path.dirname(__file__), '..', base_upload_path)

        raw_image_path = random.choice(self.sample_images)
        yolo_result = self.call_yolo_detection(raw_image_path)
        if yolo_result is None:
            return

        prediction = yolo_result.get('result', {})
        inference_result = prediction.get('result', {})
        elapsed_ms = yolo_result.get('elapsedMs', 0)

        detections = inference_result.get('detections', [])
        weed_count, crop_count = self.count_weed_and_crop(detections)

        detection_result = {
            'weedCount': weed_count,
            'cropCount': crop_count,
            'inferenceTime': elapsed_ms,
            'image': raw_image_path.name,
            'detectedAt': self._get_current_timestamp(),
            'detections': detections  # 添加detections字段
        }
        self.last_detection = detection_result
        detection_queue.put(detection_result)

        try:
            result_image_path = self.get_result_image_local_path(yolo_result, base_upload_path)
            if result_image_path is None or not result_image_path.exists():
                result_image_path = raw_image_path

            url = f'{SERVER_BASE_URL}/api/v1/detection/report'
            files = {
                'rawImage': (raw_image_path.name, open(raw_image_path, 'rb'), 'image/jpeg'),
                'resultImage': (result_image_path.name, open(result_image_path, 'rb'), 'image/jpeg')
            }
            data = {'result': json.dumps(detection_result, ensure_ascii=False)}

            resp = self.session.post(url, files=files, data=data, timeout=30)
            for f in files.values():
                f[1].close()

            if resp.status_code == 200:
                result = resp.json()
                if result.get('code') == 200:
                    self.detection_count += 1
                    logger.info(f"检测上报成功: 杂草={weed_count}, 作物={crop_count}")
        except Exception as e:
            logger.error(f"检测上报异常: {e}", exc_info=True)

    def detection_thread_func(self):
        while self.running:
            if not self.token:
                time.sleep(5)
                continue
            interval = random.uniform(MIN_DETECTION_INTERVAL, MAX_DETECTION_INTERVAL)
            time.sleep(interval)
            if not self.running:
                break
            self.report_detection()

    def handle_shutdown(self, signum, frame):
        self.running = False
        logger.info("收到关闭信号，正在停止...")
        sys.exit(0)

    def run(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        if not self.login():
            logger.error("登录失败，退出")
            sys.exit(1)

        status_thread = threading.Thread(target=self.report_status, daemon=True)
        poll_thread = threading.Thread(target=self.poll_commands, daemon=True)
        detection_thread = threading.Thread(target=self.detection_thread_func, daemon=True)

        status_thread.start()
        poll_thread.start()
        detection_thread.start()

        return status_thread, poll_thread, detection_thread


def create_visual_dashboard(simulator):
    """创建可视化监控面板"""
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.progress import BarColumn, Progress

    console = Console()

    # 历史数据保存
    logs_history = []
    commands_history = []
    detections_history = []

    def generate_layout():
        layout = Layout()
        layout.split(
            Layout(name='header', size=3),
            Layout(name='main', ratio=1),
        )
        layout['main'].split_row(
            Layout(name='left', ratio=1),
            Layout(name='right', ratio=1),
        )
        layout['left'].split(
            Layout(name='status', ratio=1),
            Layout(name='detection', ratio=1),
        )
        layout['right'].split(
            Layout(name='commands', ratio=1),
            Layout(name='logs', ratio=1),
        )
        return layout

    def build_battery_bar(percent):
        color = 'green' if percent > 50 else 'yellow' if percent > 20 else 'red'
        bar = Progress(BarColumn(complete_style=color, finished_style=color))
        task = bar.add_task('', total=100, completed=percent)
        return bar

    def get_status_panel():
        status = simulator.last_status
        if status:
            battery = status['battery']
            temp = status['temperature']
            laser = '🔴 ON' if status['laserOn'] else '⚫ OFF'

            table = Table(show_header=False, box=None, padding=1)
            table.add_column('key', style='cyan')
            table.add_column('value')
            table.add_row('🔋 电量', f'{battery}%')
            table.add_row('', build_battery_bar(battery))
            table.add_row('🌡️  温度', f'{temp}℃')
            table.add_row('💻 CPU', f"{status['cpuUsage']}%")
            table.add_row('🚀 速度', f"{status['speed']} m/s")
            table.add_row('📍 GPS', f"{status['longitude']:.6f}")
            table.add_row('', f"{status['latitude']:.6f}")
            table.add_row('🔦 激光', laser)

            return Panel(table, title='📊 实时状态', border_style='blue')
        return Panel('等待状态数据...', title='📊 实时状态', border_style='blue')

    def get_detection_panel():
        while not detection_queue.empty():
            try:
                det = detection_queue.get_nowait()
                detections_history.insert(0, det)
                if len(detections_history) > 8:
                    detections_history.pop()
            except Empty:
                break

        table = Table(show_header=True, box=None, padding=0)
        table.add_column('时间', style='dim', width=8)
        table.add_column('图片', style='cyan', width=15)
        table.add_column('杂草', style='red', width=4)
        table.add_column('作物', style='green', width=4)
        table.add_column('耗时', style='yellow', width=6)

        for det in detections_history:
            time_str = det['detectedAt'][11:19] if 'detectedAt' in det else ''
            img = det.get('image', '')[:12] if det.get('image') else ''
            table.add_row(
                time_str,
                img,
                str(det.get('weedCount', 0)),
                str(det.get('cropCount', 0)),
                f"{det.get('inferenceTime', 0)}ms"
            )

        if not detections_history:
            return Panel('等待检测数据...', title='🔍 检测结果', border_style='green')
        return Panel(table, title='🔍 检测结果', border_style='green')

    def get_commands_panel():
        while not command_queue.empty():
            try:
                cmd = command_queue.get_nowait()
                commands_history.insert(0, cmd)
                if len(commands_history) > 12:
                    commands_history.pop()
            except Empty:
                break

        table = Table(show_header=True, box=None, padding=0)
        table.add_column('状态', width=6)
        table.add_column('ID', style='cyan', width=8)
        table.add_column('动作', style='yellow', width=12)
        table.add_column('结果', width=8)

        for cmd in commands_history:
            status_type, cmd_id, action, result = cmd
            status_icon = '⏳' if status_type == 'START' else '✅' if result == 'SUCCESS' else '❌'
            result_style = 'green' if result == 'SUCCESS' else 'red' if result == 'FAILED' else 'white'
            table.add_row(
                status_icon,
                str(cmd_id),
                action,
                Text(str(result or ""), style=result_style)
            )

        if not commands_history:
            return Panel('等待指令...', title='📋 指令执行', border_style='yellow')
        return Panel(table, title='📋 指令执行', border_style='yellow')

    def get_logs_panel():
        while not log_queue.empty():
            try:
                level, msg = log_queue.get_nowait()
                logs_history.insert(0, (level, msg))
                if len(logs_history) > 15:
                    logs_history.pop()
            except Empty:
                break

        log_text = Text()
        for level, msg in logs_history:
            style = 'green' if level == 'INFO' else 'yellow' if level == 'WARNING' else 'red'
            log_text.append(msg + '\n', style=style)

        return Panel(log_text, title='📝 运行日志', border_style='magenta')

    def get_header():
        stats = f"📈 状态上报: {simulator.status_count}  |  🔍 检测上报: {simulator.detection_count}  |  📋 指令执行: {simulator.command_count}"
        return Panel(Text(stats, style='bold white', justify='center'),
                    title='🌿 除草机器人 - 树莓派模拟器', border_style='bright_blue')

    layout = generate_layout()

    with Live(layout, console=console, refresh_per_second=4, screen=True):
        while simulator.running:
            layout['header'].update(get_header())
            layout['status'].update(get_status_panel())
            layout['detection'].update(get_detection_panel())
            layout['commands'].update(get_commands_panel())
            layout['logs'].update(get_logs_panel())
            time.sleep(0.25)


def main():
    """主入口"""
    simulator = RaspberryPiSimulator()

    # 检查 rich 库是否安装
    try:
        import rich
    except ImportError:
        print("正在安装 rich 库用于可视化...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'rich'])

    # 启动工作线程
    threads = simulator.run()

    # 启动可视化界面
    try:
        create_visual_dashboard(simulator)
    except KeyboardInterrupt:
        simulator.running = False
        print("\n模拟器已停止")


if __name__ == '__main__':
    main()

