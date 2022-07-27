FROM nvidia/cuda:11.1-runtime-ubuntu20.04

RUN rm /etc/apt/sources.list.d/cuda.list && \
    apt-key del 7fa2af80 && \
    apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub

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

RUN pip install -q git+https://github.com/facebookresearch/esm.git@98017169c5e55388f3fa3b467693d3a162d084fd
RUN pip install -q urllib3==1.23 pandas tabulate biotite biopython
COPY patched_util.py /usr/local/lib/python3.8/dist-packages/esm/inverse_folding/util.py
COPY esm_if1_gvp4_t16_142M_UR50.pt /root/.cache/torch/hub/checkpoints/esm_if1_gvp4_t16_142M_UR50.pt

WORKDIR /home/biolib
COPY run.py run.py
COPY preprocess.py preprocess.py
COPY sample.pdb example.pdb
COPY patched_gvp_transformer.py /usr/local/lib/python3.8/dist-packages/esm/inverse_folding/gvp_transformer.py