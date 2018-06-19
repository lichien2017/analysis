#!/bin/sh

python infer.py \
--model_path 'models/params_pass_00008.tar.gz'  \
--data_path="data/infer_data2/three.txt" \
--word_dict_path="data/dict2/word_dict" \
--label_dict_path="data/dict2/label_dict" \

2>&1 | tee infer.log



#python train.py \
#--nn_type="dnn" \
#--batch_size=64 \
#--num_passes=10 \
#2>&1 | tee train.log
