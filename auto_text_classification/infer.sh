#!/bin/sh

python infer.py \
--model_path '/mnt/train_files/train_data/political/models/params_pass_00008.tar.gz'  \
--data_path="/mnt/train_files/test_data/political/1.txt" \
--word_dict_path="/mnt/train_files/train_data/political/dict/word_dict" \
--label_dict_path="/mnt/train_files/train_data/political/dict/label_dict" 



#python train.py \
#--nn_type="dnn" \
#--batch_size=64 \
#--num_passes=10 \
#2>&1 | tee train.log
