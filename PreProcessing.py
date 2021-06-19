import ujson
import os
import re
from tqdm import tqdm
import time

start = time.time()

dir = "/home/zjq/WSM/"
IRCdir = "/home/zjq/IRClogs/"

read_root = IRCdir
write_root = dir + "trials/"
if not os.path.exists(write_root):
    os.makedirs(write_root)

year_start = 2004
year_end = 2022
user_list = set()
DocID = 0
doc_list = []

# transform raw data to structured data
def trans(s):
    w = s.split()
    if w[0] == "===":
        tp = "name_change"
    elif w[1] == "*":
        tp = "action"
    elif w[1][0] == '<':
        tp = "message"
    else:
        tp = "others"
    st = len(w[0]) + 1
    if tp == "message":
        time = w[0][1:-1]
        sender = w[1][1:-1]
        user_list.add(sender)
        receiver = None
        if (len(w) >= 3) and (len(w[2]) >= 2) and (w[2][-1] in [':', ',']) and (w[2][:-1] in user_list):
            receiver = w[2][:-1]
        text = s[st:]
        return [tp, time, sender, receiver, text]
    elif tp == "name_change":
        user_list.add(w[1])
        user_list.add(w[-1])
        sender1 = w[1]
        sender2 = w[-1]
        text = s[st:]
        return [tp, sender1, sender2, text]
    elif tp == "action":
        time = w[0][1:-1]
        sender = w[1][1:-1]
        text = s[st:]
        return [tp, time, sender, text]
    else:
        time = w[0][1:-1]
        sp = re.compile('[:]')
        temp = sp.split(s[9:])
        sender = temp[0]
        text = s[st:]
        return [tp, time, sender, text]


Logs = []
index = []
for year in range(year_start, year_end):
    for month in tqdm(range(1, 13)):
        for day in range(1, 32):
            M = '0' + str(month) if month < 10 else str(month)
            D = '0' + str(day) if day < 10 else str(day)
            date = str(year) + '/' + M + '/' + D + '/'
            read_dir = read_root + date
            if os.path.exists(read_dir):
                file_list = os.listdir(read_dir)
                for file_name in file_list:
                    if file_name[-3:] == "txt":
                        try:
                            read_name = read_dir + file_name
                            doc_list += [read_name]
                            with open(read_name, 'r', encoding='utf-8') as FRead:
                                contents = FRead.readlines()
                                for i in range(len(contents)):
                                    line = contents[i]
                                    DocLog = trans(line)[-1]
                                    Logs.append(DocLog)
                                    index.append((DocID, i))
                            DocID += 1
                        except:
                            pass


# store text in one single file for fast posting list generation
write_name = write_root + "data.json"
if not os.path.exists(write_name):
    with open(write_name, 'w', encoding="utf-8") as FWrite:
        t1 = ujson.dumps(Logs)
        FWrite.write(t1)

# convert one global line to [DocId, DocLine]
index_name = write_root + "index.json"
if not os.path.exists(index_name):
    with open(index_name,'w',encoding="utf-8") as IWrite:
        t2 = ujson.dumps(index)
        IWrite.write(t2)

print("Preprocessing costs time: ", time.time()-start)
