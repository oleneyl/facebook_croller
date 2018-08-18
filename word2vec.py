from konlpy.tag import Twitter

fnames = ["data/posttxt" + str(i) + ".dat" for i in range(0, 35)]
fnames += ["data_ys/posttxt" +str(i) + ".dat" for i in range(0,7)]
def read_data(fname):
    with open(fname, "r") as f:
        data = [" ".join(line.split(' ')[1:]) for line in f.read().splitlines()]
        data = data   # header 제외
    return data

train_data = []
for fname in fnames:
    train_data += read_data(fname)

pos_tagger = Twitter()
def tokenize(doc):
    # norm, stem은 optional
    return ['/'.join(t) for t in pos_tagger.pos(doc, norm=True, stem=True)]
    
train_docs = [tokenize(row) for row in train_data]
#test_docs = [(tokenize(row[1]), row[2]) for row in test_data]
# 잘 들어갔는지 확인
from pprint import pprint
pprint(train_docs[0])


