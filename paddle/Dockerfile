From paddlepaddle/paddle:latest-gpu
COPY $PWD/requirement.txt /requirement.txt
RUN buildDeps='adium-theme-ubuntu libmysqlclient-dev unity-lens-photos' \
    && apt-get update \
    && apt-get install -y $buildDeps \
    && pip install -r /requirement.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
WORKDIR /mnt/train_files/infer_env
ENTRYPOINT ["sh","/mnt/train_files/infer_env/start_paddle.sh"]
