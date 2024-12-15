import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal
from body3d_img2pose_demo import process_one_image  # 确保您已经将 body3d_img2pose_demo.py 放在同目录下
from mmpose.apis import init_model



class RTMPose3DProcessor(QObject):
    frame_ready = Signal(np.ndarray)  # 信号，用于将处理后的帧发送给主线程

    def __init__(self, det_config, det_checkpoint, pose3d_config, pose3d_checkpoint, device='cuda:0'):
        super().__init__()
        self.detector = init_model(det_config, det_checkpoint, device=device)
        self.pose_estimator = init_model(pose3d_config, pose3d_checkpoint, device=device)
        self.running = False

    def start_camera(self, camera_index=0):
        """启动摄像头并实时处理帧"""
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("Error: Unable to open camera")
            return

        self.running = True
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to read frame")
                break

            print("Frame captured")  # 调试输出

            # 使用 rtmpose3d 处理帧
            processed_frame = self.process_frame(frame)
            if processed_frame is not None:
                print("Frame processed successfully")  # 添加调试输出
                self.frame_ready.emit(processed_frame)
            else:
                print("Frame processing failed")  # 添加调试输出
            # 使用 rtmpose3d 处理帧
            #processed_frame = self.process_frame(frame)
            #if processed_frame is not None:
            #    self.frame_ready.emit(processed_frame)

        cap.release()

    def stop_camera(self):
        """停止摄像头"""
        self.running = False

    def process_frame(self, frame):
        try:
            visualize_frame = np.copy(frame)
            print("Running process_one_image...")  # 调试输出
            pose_est_results, _, pred_3d_instances, _ = process_one_image(
                args=None,
                detector=self.detector,
                frame=frame,
                frame_idx=0,
                pose_estimator=self.pose_estimator,
                pose_est_results_last=[],
                pose_est_results_list=[],
                next_id=0,
                visualize_frame=visualize_frame,
                visualizer=None,
            )
            print("Pose estimation successful")  # 调试输出
            return visualize_frame
        except Exception as e:
            print(f"Error in process_frame: {e}")  # 调试输出
            return None

