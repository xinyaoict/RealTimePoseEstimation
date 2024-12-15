import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
from pose_ui import Ui_Form  # 导入由 Qt Designer 生成的 UI 文件

class PoseEstimationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # 绑定按钮点击事件
        self.ui.pose_button.clicked.connect(self.start_pose_estimation)

        # 摄像头显示相关
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.capture = None

    def start_pose_estimation(self):
        """启动 RTMPose3D 的命令"""
        # 在后台启动 RTMPose3D 脚本
        self.process = subprocess.Popen(
            [
                "python", "body3d_img2pose_demo.py",
                "../configs/rtmdet_m_640-8xb32_coco-person.py",
                "https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_m_8xb32-100e_coco-obj365-person-235e8209.pth",
                "../configs/rtmw3d-l_8xb64_cocktail14-384x288.py",
                "../configs/rtmw3d-l_8xb64_cocktail14-384x288-794dbc78_20240626.pth",
                "--input", "webcam", "--show"
            ]
        )

        # 打开摄像头流
        self.capture = cv2.VideoCapture(0)
        self.timer.start(30)  # 每30ms刷新一帧

    def update_frame(self):
        """更新图像帧"""
        if self.capture is not None:
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                qimg = QImage(frame.data, width, height, width * channel, QImage.Format_RGB888)
                self.ui.image_label.setPixmap(QPixmap.fromImage(qimg))
            else:
                self.timer.stop()

    def closeEvent(self, event):
        """关闭事件时释放资源"""
        if self.capture is not None:
            self.capture.release()
        if self.process is not None:
            self.process.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoseEstimationApp()
    window.show()
    sys.exit(app.exec_())
