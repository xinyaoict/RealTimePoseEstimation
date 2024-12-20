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

### Best Practices
#### Build MMPose from source
To develop and run mmpose directly, install it from source:
```python
git clone https://github.com/open-mmlab/mmpose.git
cd mmpose
pip install -r requirements.txt
pip install -v -e .
# "-v" means verbose, or more output
# "-e" means installing a project in editable mode,
# thus any local modifications made to the code will take effect without reinstallation.
```

#### Install as a Python package
To use mmpose as a dependency or third-party package, install it with pip:
```python
mim install "mmpose>=1.1.0"
```



#### Verify the installation
To verify that MMPose is installed correctly, you can run an inference demo with the following steps.
##### Step 1. We need to download config and checkpoint files.
mim download mmpose --config td-hm_hrnet-w48_8xb32-210e_coco-256x192  --dest .

The downloading will take several seconds or more, depending on your network environment. When it is done, you will find two files td-hm_hrnet-w48_8xb32-210e_coco-256x192.py and td-hm_hrnet-w48_8xb32-210e_coco-256x192-0e67c616_20220913.pth in your current folder.

##### Step 2. Run the inference demo.
##### Option (A). If you install mmpose from source, just run the following command under the folder $MMPOSE:
```python
python demo/image_demo.py \
    tests/data/coco/000000000785.jpg \
    td-hm_hrnet-w48_8xb32-210e_coco-256x192.py \
    td-hm_hrnet-w48_8xb32-210e_coco-256x192-0e67c616_20220913.pth \
    --out-file vis_results.jpg \
    --draw-heatmap
```

If everything goes fine, you will be able to get the following visualization result from vis_results.jpg in your current folder, which displays the predicted keypoints and heatmaps overlaid on the person in the image.

##### Option (B). If you install mmpose with pip, open you python interpreter and copy & paste the following codes.
```python
from mmpose.apis import inference_topdown, init_model
from mmpose.utils import register_all_modules

register_all_modules()

config_file = 'td-hm_hrnet-w48_8xb32-210e_coco-256x192.py'
checkpoint_file = 'td-hm_hrnet-w48_8xb32-210e_coco-256x192-0e67c616_20220913.pth'
model = init_model(config_file, checkpoint_file, device='cpu')  # or device='cuda:0'

# please prepare an image with person
results = inference_topdown(model, 'demo.jpg')
```



