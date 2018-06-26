From bvlc/caffe:gpu
COPY $PWD/requirement.txt /requirement.txt
RUN cudafile='/etc/apt/sources.list.d/cuda.list' \
    && nvidiafile='/etc/apt/sources.list.d/nvidia-ml.list' \
    && rm $cudafile $nvidiafile \
    && apt-get update \
    && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64 /">$cudafile \
    && echo "deb https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1604/x86_64 /">$nvidiafile \
    && apt-get install -y apt-transport-https \
    && wget -qO - https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub | apt-key add - \
    && apt-get install software-properties-common \
    $$ add-apt-repository ppa:alex-p/tesseract-ocr \
    && apt-get update \
    && buildDeps='adium-theme-ubuntu libmysqlclient-dev unity-lens-photos tesseract-ocr libtesseract-dev' \
    && apt-get install -y $buildDeps \
    && pip install -r /requirement.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
COPY $PWD/chi_sim.traineddata /usr/share/tesseract-ocr/4.00/tessdata/chi_sim.traineddata
WORKDIR /mnt/train_files/infer_env
ENTRYPOINT ["sh","/mnt/train_files/infer_env/start_caffe.sh"]
