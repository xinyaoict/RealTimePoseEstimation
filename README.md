# RealTimePoseEstimation with Qt
Step 0. Download and install Miniconda from the official website.
Step 1. Create a conda environment and activate it.
conda create --name openmmlab python=3.8 -y
conda activate openmmlab
Step 2. Install PyTorch following official instructions, e.g.
On GPU platforms:
conda install pytorch torchvision -c pytorch
WARNING
This command will automatically install the latest version PyTorch and cudatoolkit, please check whether they match your environment.

On CPU platforms:
conda install pytorch torchvision cpuonly -c pytorch
