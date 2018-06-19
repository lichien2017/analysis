#!/bin/sh

python train.py \
--train_data_dir="data/train_data2" \
--word_dict_path="data/dict2/word_dict" \
--label_dict_path="data/dict2/label_dict" \
2>&1 | tee train.log



#python train.py \
#--nn_type="dnn" \
#--batch_size=64 \
#--num_passes=10 \
#2>&1 | tee train.log
