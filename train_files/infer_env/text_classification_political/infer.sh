#!/bin/sh

python infer.py \
--model_path 'models/params_pass_00009.tar.gz'  \
--data_path="data/infer_data2/two.txt" \
--word_dict_path="data/dict3/word_dict" \
--label_dict_path="data/dict3/label_dict" \

2>&1 | tee infer.log



#python train.py \
#--nn_type="dnn" \
#--batch_size=64 \
#--num_passes=10 \
#2>&1 | tee train.log
