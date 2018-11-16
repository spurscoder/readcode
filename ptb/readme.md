# 数据来自于rnnlm的数据

wget http://www.fit.vutbr.cz/~imikolov/rnnlm/simple-examples.tgz
tar xvf simple-examples.tgz

# 这条命令的数据可以来自于本rep
python ptb_word_lm.py --data_path=simple-examples/data/

python ptb_word_lm.py --data_path=../rnnlm/rnnlm-examples/data/

