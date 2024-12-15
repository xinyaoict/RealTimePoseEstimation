# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtMultimedia import (QAudioInput, QCamera, QCameraDevice,
                                  QImageCapture, QMediaCaptureSession,
                                  QMediaDevices, QMediaMetaData,
                                  QMediaRecorder)
from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox
from PySide6.QtGui import QAction, QActionGroup, QIcon, QImage, QPixmap
from PySide6.QtCore import QDateTime, QDir, QTimer, Qt, Slot, qWarning

from metadatadialog import MetaDataDialog
from imagesettings import ImageSettings
from videosettings import VideoSettings, is_android

if is_android or sys.platform == "darwin":
    from PySide6.QtCore import QMicrophonePermission, QCameraPermission

if is_android:
    from ui_camera_mobile import Ui_Camera
else:
    from ui_camera import Ui_Camera

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import QMainWindow, QVBoxLayout
from ui_camera import Ui_Camera
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtMultimediaWidgets import QVideoWidget


class MatplotlibWidget(FigureCanvas):       
    def update_pose(self, keypoints, links):
        self.axes.clear()
        # 绘制关键点
        for keypoint in keypoints:
            x, y, z = keypoint
            self.axes.scatter(x, y, z, c='r')
        # 绘制骨架
        for link in links:
            p1, p2 = link
            x = [keypoints[p1][0], keypoints[p2][0]]
            y = [keypoints[p1][1], keypoints[p2][1]]
            z = [keypoints[p1][2], keypoints[p2][2]]
            self.axes.plot(x, y, z, c='b')
        self.draw()
    def __init__(self, parent=None):
        fig = Figure()
        self.axes = fig.add_subplot(111, projection="3d")
        super().__init__(fig)
        self.setParent(parent)

from PySide6.QtCore import QThread, Signal

class RTMPoseThread(QThread):
    dataReady = Signal(object, object)  # 信号：关键点和骨架数据

    def __init__(self, demo_script_path, args, parent=None):
        super().__init__(parent)
        self.demo_script_path = demo_script_path
        self.args = args

    def run(self):
        # 导入 body3d_img2pose_demo 的处理逻辑
        from body3d_img2pose_demo_qttest import process_frames, init_detector, init_model, VISUALIZERS

        # 初始化模型
        detector = init_detector(
            self.args.det_config, self.args.det_checkpoint, device=self.args.device.lower()
        )
        pose_estimator = init_model(
            self.args.pose3d_estimator_config, self.args.pose3d_estimator_checkpoint, device=self.args.device.lower()
        )
        visualizer = VISUALIZERS.build(pose_estimator.cfg.visualizer)

        # 读取帧数据
        for keypoints, links in process_frames(
            video_source=self.args.input, detector=detector, pose_estimator=pose_estimator, visualizer=visualizer, args=self.args
        ):
            self.dataReady.emit(keypoints, links)  # 发射信号


class Camera(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化 UI
        self._ui = Ui_Camera()
        self._ui.setupUi(self)

        # 初始化 QMediaCaptureSession
        self.m_captureSession = QMediaCaptureSession()

        # 初始化摄像头
        self.m_camera = QCamera(QMediaDevices.defaultVideoInput())
        self.m_captureSession.setCamera(self.m_camera)

        # 初始化标志位
        self.m_isCapturingImage = False  # 用于标记是否正在捕获图像
        self.m_applicationExiting = False  # 用于标记应用程序是否正在退出


        # 初始化 Viewfinder 和 MatplotlibWidget
        self._ui.viewfinder = QVideoWidget(self)
        layout = QVBoxLayout(self._ui.viewfinderPage)
        layout.addWidget(self._ui.viewfinder)
        self._ui.viewfinderPage.setLayout(layout)       
        self.mpl_widget = MatplotlibWidget(self._ui.matplotlibWidget)
        self._ui.matplotlibWidget.layout().addWidget(self.mpl_widget)  # 添加到已有布局


        # 绑定 Viewfinder 到摄像头捕获会话
        self.m_captureSession.setVideoOutput(self._ui.viewfinder)

        # 初始化成员变量
        self.m_mediaRecorder = None  # 初始化媒体录制器

        self.m_devices = QMediaDevices()  # 初始化设备管理器

        self.m_imageCapture = None  # 初始化为 None

        self.mpl_widget = MatplotlibWidget(self._ui.matplotlibWidget)
        layout = QVBoxLayout(self._ui.matplotlibWidget)  # 添加布局
        layout.addWidget(self.mpl_widget)  # 将 MatplotlibWidget 添加到布局中
        self._ui.matplotlibWidget.setLayout(layout)  # 设置布局

        if not self._ui.viewfinderPage.layout():
            layout = QVBoxLayout(self._ui.viewfinderPage)
            layout.addWidget(self._ui.viewfinder)


        # 启动摄像头
        self.m_camera.start()

        # 摄像头和设备初始化
        self.initializeUI()
        self.initialize()
        
    def initializeUI(self):
        """初始化 UI 组件的默认状态"""
        # 设置图标
        image = Path(__file__).parent / "shutter.svg"
        self._ui.takeImageButton.setIcon(QIcon(os.fspath(image)))

        # 禁用部分按钮
        self.updateCameraActive(False)
        self.readyForCapture(False)
        self._ui.recordButton.setEnabled(False)
        self._ui.pauseButton.setEnabled(False)
        self._ui.stopButton.setEnabled(False)
        self._ui.metaDataButton.setEnabled(False)

        # 关于 Qt 的动作
        if not is_android:
            self._ui.actionAbout_Qt.triggered.connect(qApp.aboutQt)  # noqa: F821    

    @Slot()
    def initialize(self):
        """初始化摄像头和音频输入"""
        self.m_audioInput = QAudioInput()
        self.m_captureSession.setAudioInput(self.m_audioInput)

        # 设备列表更新和信号连接
        self._video_devices_group = QActionGroup(self)
        self._video_devices_group.setExclusive(True)
        self.updateCameras()
        self.m_devices.videoInputsChanged.connect(self.updateCameras)
        self._video_devices_group.triggered.connect(self.updateCameraDevice)

        # 设置默认摄像头
        self.setCamera(QMediaDevices.defaultVideoInput())

    @Slot(QCameraDevice)
    def setCamera(self, cameraDevice):
        self.m_camera = QCamera(cameraDevice)
        self.m_captureSession.setCamera(self.m_camera)

        self.m_camera.activeChanged.connect(self.updateCameraActive)
        self.m_camera.errorOccurred.connect(self.displayCameraError)

        if not self.m_mediaRecorder:
            self.m_mediaRecorder = QMediaRecorder()  # 初始化 m_mediaRecorder
            self.m_captureSession.setRecorder(self.m_mediaRecorder)
            self.m_mediaRecorder.recorderStateChanged.connect(self.updateRecorderState)
            self.m_mediaRecorder.durationChanged.connect(self.updateRecordTime)
            self.m_mediaRecorder.errorChanged.connect(self.displayRecorderError)

        if not self.m_imageCapture:
            self.m_imageCapture = QImageCapture()
            self.m_captureSession.setImageCapture(self.m_imageCapture)
            self.m_imageCapture.readyForCaptureChanged.connect(self.readyForCapture)
            self.m_imageCapture.imageCaptured.connect(self.processCapturedImage)
            self.m_imageCapture.imageSaved.connect(self.imageSaved)
            self.m_imageCapture.errorOccurred.connect(self.displayCaptureError)

            self.m_captureSession.setVideoOutput(self._ui.viewfinder)

            self.updateCameraActive(self.m_camera.isActive())
            self.updateRecorderState(self.m_mediaRecorder.recorderState())
            self.readyForCapture(self.m_imageCapture.isReadyForCapture())

            self.updateCaptureMode()

            self.m_camera.start()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        key = event.key()
        if key == Qt.Key_CameraFocus:
            self.displayViewfinder()
            event.accept()
        elif key == Qt.Key_Camera:
            if self.m_doImageCapture:
                self.takeImage()
            else:
                if self.m_mediaRecorder.recorderState() == QMediaRecorder.RecordingState:
                    self.stop()
                else:
                    self.record()

            event.accept()
        else:
            super().keyPressEvent(event)

    @Slot()
    def updateRecordTime(self):
        d = self.m_mediaRecorder.duration() / 1000
        self._ui.statusbar.showMessage(f"Recorded {d} sec")

    @Slot(int, QImage)
    def processCapturedImage(self, requestId, img):
        scaled_image = img.scaled(self._ui.viewfinder.size(), Qt.KeepAspectRatio,
                                  Qt.SmoothTransformation)

        self._ui.lastImagePreviewLabel.setPixmap(QPixmap.fromImage(scaled_image))

        # Display captured image for 4 seconds.
        self.displayCapturedImage()
        QTimer.singleShot(4000, self.displayViewfinder)

    @Slot()
    def configureCaptureSettings(self):
        if self.m_doImageCapture:
            self.configureImageSettings()
        else:
            self.configureVideoSettings()

    @Slot()
    def configureVideoSettings(self):
        settings_dialog = VideoSettings(self.m_mediaRecorder)

        if settings_dialog.exec():
            settings_dialog.apply_settings()

    @Slot()
    def configureImageSettings(self):
        settings_dialog = ImageSettings(self.m_imageCapture)

        if settings_dialog.exec():
            settings_dialog.apply_image_settings()

    @Slot()
    def record(self):
        self.m_mediaRecorder.record()
        self.updateRecordTime()

    @Slot()
    def pause(self):
        self.m_mediaRecorder.pause()

    @Slot()
    def stop(self):
        self.m_mediaRecorder.stop()

    @Slot(bool)
    def setMuted(self, muted):
        self.m_captureSession.audioInput().setMuted(muted)

    @Slot()
    def takeImage(self):
        self.m_isCapturingImage = True
        self.m_imageCapture.captureToFile()

    @Slot(int, QImageCapture.Error, str)
    def displayCaptureError(self, id, error, errorString):
        QMessageBox.warning(self, "Image Capture Error", errorString)
        self.m_isCapturingImage = False

    @Slot()
    def startCamera(self):
        self.m_camera.start()

    @Slot()
    def stopCamera(self):
        self.m_camera.stop()

    @Slot()
    def updateCaptureMode(self):
        tab_index = self._ui.captureWidget.currentIndex()
        self.m_doImageCapture = (tab_index == 0)

    @Slot(bool)
    def updateCameraActive(self, active):
        if active:
            self._ui.actionStartCamera.setEnabled(False)
            self._ui.actionStopCamera.setEnabled(True)
            self._ui.captureWidget.setEnabled(True)
            self._ui.actionSettings.setEnabled(True)
        else:
            self._ui.actionStartCamera.setEnabled(True)
            self._ui.actionStopCamera.setEnabled(False)
            self._ui.captureWidget.setEnabled(False)
            self._ui.actionSettings.setEnabled(False)

    @Slot(QMediaRecorder.RecorderState)
    def updateRecorderState(self, state):
        if state == QMediaRecorder.StoppedState:
            self._ui.recordButton.setEnabled(True)
            self._ui.pauseButton.setEnabled(True)
            self._ui.stopButton.setEnabled(False)
            self._ui.metaDataButton.setEnabled(True)
        elif state == QMediaRecorder.PausedState:
            self._ui.recordButton.setEnabled(True)
            self._ui.pauseButton.setEnabled(False)
            self._ui.stopButton.setEnabled(True)
            self._ui.metaDataButton.setEnabled(False)
        elif state == QMediaRecorder.RecordingState:
            self._ui.recordButton.setEnabled(False)
            self._ui.pauseButton.setEnabled(True)
            self._ui.stopButton.setEnabled(True)
            self._ui.metaDataButton.setEnabled(False)

    @Slot(int)
    def setExposureCompensation(self, index):
        self.m_camera.setExposureCompensation(index * 0.5)

    @Slot()
    def displayRecorderError(self):
        if self.m_mediaRecorder.error() != QMediaRecorder.NoError:
            QMessageBox.warning(self, "Capture Error",
                                self.m_mediaRecorder.errorString())

    @Slot()
    def displayCameraError(self):
        if self.m_camera.error() != QCamera.NoError:
            QMessageBox.warning(self, "Camera Error",
                                self.m_camera.errorString())

    @Slot(QAction)
    def updateCameraDevice(self, action):
        self.setCamera(QCameraDevice(action))

    @Slot()
    def displayViewfinder(self):
        self._ui.stackedWidget.setCurrentIndex(0)

    @Slot()
    def displayCapturedImage(self):
        self._ui.stackedWidget.setCurrentIndex(1)

    @Slot(bool)
    def readyForCapture(self, ready):
        self._ui.takeImageButton.setEnabled(ready)

    @Slot(int, str)
    def imageSaved(self, id, fileName):
        f = QDir.toNativeSeparators(fileName)
        self._ui.statusbar.showMessage(f"Captured \"{f}\"")

        self.m_isCapturingImage = False
        if self.m_applicationExiting:
            self.close()


    def closeEvent(self, event):

        if hasattr(self, 'pose_thread') and self.pose_thread.isRunning():
            self.pose_thread.terminate()  # 或者更优雅地停止线程
            self.pose_thread.wait()
        super().closeEvent(event)
        
        if getattr(self, 'm_isCapturingImage', False):  # 确保 m_isCapturingImage 存在
            self.setEnabled(False)
            self.m_applicationExiting = True
            event.ignore()
        else:
            event.accept()


    @Slot()
    def updateCameras(self):
        self._ui.menuDevices.clear()
        available_cameras = QMediaDevices.videoInputs()
        for cameraDevice in available_cameras:
            video_device_action = QAction(cameraDevice.description(),
                                          self._video_devices_group)
            video_device_action.setCheckable(True)
            video_device_action.setData(cameraDevice)
            if cameraDevice == QMediaDevices.defaultVideoInput():
                video_device_action.setChecked(True)

            self._ui.menuDevices.addAction(video_device_action)

    @Slot()
    def showMetaDataDialog(self):
        if not self.m_metaDataDialog:
            self.m_metaDataDialog = MetaDataDialog(self)
        self.m_metaDataDialog.setAttribute(Qt.WA_DeleteOnClose, False)
        if self.m_metaDataDialog.exec() == QDialog.Accepted:
            self.saveMetaData()

    @Slot()
    def saveMetaData(self):
        data = QMediaMetaData()
        for i in range(0, QMediaMetaData.NumMetaData):
            val = self.m_metaDataDialog.m_metaDataFields[i].text()
            if val:
                key = QMediaMetaData.Key(i)
                if key == QMediaMetaData.CoverArtImage:
                    cover_art = QImage(val)
                    data.insert(key, cover_art)
                elif key == QMediaMetaData.ThumbnailImage:
                    thumbnail = QImage(val)
                    data.insert(key, thumbnail)
                elif key == QMediaMetaData.Date:
                    date = QDateTime.fromString(val)
                    data.insert(key, date)
                else:
                    data.insert(key, val)

        self.m_mediaRecorder.setMetaData(data)



    def debug_camera_devices():
        """调试当前系统中可用的摄像头设备"""
        available_cameras = QMediaDevices.videoInputs()
        if not available_cameras:
            print("No camera devices found.")
        else:
            print("Available camera devices:")
            for camera in available_cameras:
                print(f" - {camera.description()}")

    # 调试摄像头设备
    debug_camera_devices()   

from PySide6.QtCore import QThread, Signal

class PoseEstimationThread(QThread):
    dataReady = Signal(object, object)  # 信号：关键点和骨架数据

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        # 导入 body3d_img2pose_demo.py 中的逻辑
        from body3d_img2pose_demo_qttest import process_frames, init_detector, init_model, VISUALIZERS

        # 配置文件路径
        det_config = "../configs/rtmdet_m_640-8xb32_coco-person.py"
        det_checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_m_8xb32-100e_coco-obj365-person-235e8209.pth"
        pose3d_config = "../configs/rtmw3d-l_8xb64_cocktail14-384x288.py"
        pose3d_checkpoint = "../configs/rtmw3d-l_8xb64_cocktail14-384x288-794dbc78_20240626.pth"

        # 初始化检测器和模型
        detector = init_detector(det_config, det_checkpoint, device='cuda:0')
        pose_estimator = init_model(pose3d_config, pose3d_checkpoint, device='cuda:0')
        visualizer = VISUALIZERS.build(pose_estimator.cfg.visualizer)

        # 读取帧并处理
        for keypoints, links in process_frames(
            video_source="webcam",
            detector=detector,
            pose_estimator=pose_estimator,
            visualizer=visualizer,
            args=argparse.Namespace,  # 如果 `args` 是命名空间对象，则替换为合适的参数
        ):
            self.dataReady.emit(keypoints, links)  # 发送信号

@Slot(object, object)
def updatePoseDisplay(self, keypoints, links):
    """更新 MatplotlibWidget 中的显示"""
    self.mpl_widget.update_pose(keypoints, links)


def startPoseEstimation(self):
    """启动 RTMPose3D 线程"""
    self.pose_thread = PoseEstimationThread()
    self.pose_thread.dataReady.connect(self.updatePoseDisplay)  # 连接信号到更新方法
    self.pose_thread.start()



