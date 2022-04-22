FROM nvidia/cuda:11.1-runtime-ubuntu20.04
RUN apt update
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.9 python3-pip git -y
RUN pip3 install --upgrade pip

RUN pip install torch==1.10.0+cu111 -f https://download.pytorch.org/whl/cu111/torch_stable.html
RUN pip install torch-cluster -f https://data.pyg.org/whl/torch-1.10.0+cu111.html
RUN pip install torch-sparse -f https://data.pyg.org/whl/torch-1.10.0+cu111.html
RUN pip install torch-geometric -f https://data.pyg.org/whl/torch-1.10.0+cu111.html
RUN pip install torch-scatter -f https://data.pyg.org/whl/torch-1.10.0+cu111.html
RUN pip install torch-spline-conv -f https://data.pyg.org/whl/torch-1.10.0+cu111.html

RUN pip install -q git+https://github.com/facebookresearch/esm.git
RUN pip install -q urllib3==1.23 pandas tabulate biotite biopython

COPY esm_if1_gvp4_t16_142M_UR50.pt /root/.cache/torch/hub/checkpoints/esm_if1_gvp4_t16_142M_UR50.pt
COPY run.py run.py
COPY preprocess.py preprocess.py
COPY sample.pdb sample.pdb