from keras.preprocessing.text import Tokenizer
import ujson
import os
import time
from tqdm import tqdm
import cProfile
import copy
import gc
from multiprocessing import Pool, Manager
from threading import Thread

gc.enable()
dir = "/home/zjq/WSM/"

read_root = dir + "trials/"
write_root = dir + "postingss/"
words_path = dir + 'words.json'
logs_path = dir + 'logs.json'

if not os.path.exists(write_root):
    os.makedirs(write_root)
doc_num = len(os.listdir(read_root))
posting_list = dict()
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
           'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
           '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '\'', '_']

# split into 38 x 38 tiny posting lists
pre = []
for i in letters:
    for j in letters:
        pre.append(i + j)

start_time = time.time()

words, Logs = None, None
if os.path.exists(words_path):
    print("loading words ...")
    with open(words_path) as f:
        words = ujson.load(f)
if os.path.exists(logs_path):
    print("loading logs ...")
    with open(logs_path) as f:
        Logs = ujson.load(f)

if words == None or Logs == None:
    file_name = read_root + "data.json"
    with open(file_name) as f:
        Logs = ujson.load(f)
    tokenizer = Tokenizer(filters='!"#$%&()*+,-./:;<=>?@[\\]^`{|}~\t\n')
    lenL = len(Logs)
    tokenizer.fit_on_texts(Logs)
    words = list(tokenizer.word_index.keys())
    Logs = tokenizer.texts_to_sequences(Logs)

# gc.collect()

if not os.path.exists(words_path):
    with open(words_path, 'w+') as f:
        ujson.dump(words, f)
if not os.path.exists(logs_path):
    with open(logs_path, 'w+') as f:
        ujson.dump(Logs, f)

print('Tokenizer costs time: ', time.time() - start_time)


# def f(let, words, Logs):
def f(let): 
    posting_list = [dict() for i in range(len(letters))]

    # print(len(Logs))
    for i in tqdm(range(len(Logs))):

        for idx in range(len(Logs[i])):
            sti = str(i)
            word = words[Logs[i][idx] - 1]
            if word[0] == let:
                secletter = 0
                if len(word) > 1 and word[1] in letters:
                    secletter = letters.index(word[1])
                if word not in posting_list[secletter]:
                    posting_list[secletter][word] = dict()
                if sti not in posting_list[secletter][word]:
                    posting_list[secletter][word][sti] = []
                    posting_list[secletter][word][sti].append(idx)
    for j in range(len(posting_list)):
        with open(write_root + let + letters[j] + '.json', 'w+') as f:
            ujson.dump(posting_list[j], f)

    del posting_list
    # gc.collect()


def run_parallel(words, Logs):
    # using shared memory
    manager = Manager()

    words_ = manager.list(words)
    del words
    Logs_ = manager.list(Logs)
    del Logs

    # gc.collect()

    # parallel without memeory keeping increasing
    with Pool(processes=len(letters)) as pool:
        pros = [pool.apply_async(f, (let, words_, Logs_)) for let in letters]
        [pro.get() for pro in pros]


if __name__ == '__main__':
    start_time = time.time()
    # run_parallel(words, Logs)

    for let in letters:
        f(let)

    # threads = [Thread(target=f, args=(p, words, Logs)) for p in pre]
    # [t.start() for t in threads]
    # [t.join() for t in threads]

    print('Posting list processing costs time: ', time.time() - start_time)
