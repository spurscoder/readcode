# get the data for this project.
wget http://mattmahoney.net/dc/text8.zip
unzip -a text8.zip
wget https://storage.googleapis.com/google-code-archive-source/v2/code.google.com/word2vec/source-archive.zip
unzip -p source-archive.zip  word2vec/trunk/questions-words.txt > questions-words.txt
rm text8.zip source-archive.zip

# compile the .so file
TF_CFLAGS=( $(python -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_compile_flags()))') )
TF_LFLAGS=( $(python -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_link_flags()))') )
g++ -std=c++11 -shared word2vec_ops.cc word2vec_kernels.cc -o word2vec_ops.so -fPIC ${TF_CFLAGS[@]} ${TF_LFLAGS[@]} -O2 
# for mac, add params: -undefined dynamic_lookup

# run
python word2vec_optimized.py --train_data=text8 --eval_data=questions-words.txt --save_path=/tmp/
