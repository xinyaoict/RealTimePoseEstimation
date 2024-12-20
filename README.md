# RealTimePoseEstimation with Qt
## Step 0. Download and install Miniconda from the official website.
## Step 1. Create a conda environment and activate it.
```python
conda create --name openmmlab python=3.8 -y
conda activate openmmlab
```
## Step 2. Install PyTorch following official instructions, e.g.
#### On GPU platforms:
```python
conda install pytorch torchvision -c pytorch
```
#### WARNING
This command will automatically install the latest version PyTorch and cudatoolkit, please check whether they match your environment.

#### On CPU platforms:
```python
conda install pytorch torchvision cpuonly -c pytorch
```

## Step 3. Install MMEngine and MMCV using MIM.
```python
pip install -U openmim
mim install mmengine
pip install "mmcv==2.1.0"
```
Note that some of the demo scripts in MMPose require MMDetection (mmdet) for human detection. If you want to run these demo scripts with mmdet, you can easily install mmdet as a dependency by running:
```python mim install "mmdet==3.3.0"```

#### NOTE
#### Here are the version correspondences between mmdet, mmpose and mmcv:
```python
mmdet 2.x <=> mmpose 0.x <=> mmcv 1.x
mmdet 3.x <=> mmpose 1.x <=> mmcv 2.x
```
You can check the appropriate installation command depending on the type of system, CUDA version, PyTorch version, and MMCV version on this link:<https://mmcv.readthedocs.io/en/latest/get_started/installation.html>


## Step 4. Install Qt
To design a GUI using QT, we use PyQt5. Please note OpenCV also uses QT internally when calling window-related functions, which will cause errors if Qt is used again. So we must install the headless version of OpenCV.

Install opencv headless:
```python
pip install opencv-python-headless
```
Install PyQt5:
```python
pip install PyQt5
```
Install Imutils:
```python
pip install imutils
```

## Practices
#### Build this project from the source
To develop and run this project directly, install it from source:
```python
git clone git@github.com:xinyaoict/RealTimePoseEstimation.git
cd RealTimePoseEstimation
pip install -r requirements.txt
pip install -v -e .
cd rtmpose3d
export PYTHONPATH=$(pwd):$PYTHONPATH
cd demo
python main_new.py

# "-v" means verbose, or more output
# "-e" means installing a project in editable mode,
# thus any local modifications made to the code will take effect without reinstallation.
```





