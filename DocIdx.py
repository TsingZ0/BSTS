import ujson
import time

start = time.time()

dir = "/home/zjq/WSM/"
doc_root = dir + "trials/"

with open(doc_root + "index.json") as f:
    indexs = ujson.load(f)

# convert the first line of one Doc to global line, given DocID
docidx = {}
length = 0
for idx, line in enumerate(indexs):
    if line[0] not in docidx:
        length = 1
        docidx[line[0]] = [idx, length]
    else:
        docidx[line[0]][1] += 1

with open(doc_root + "docidx.json", 'w+') as f:
    ujson.dump(docidx, f)

print("Building Docidx costs time: ", time.time()-start)