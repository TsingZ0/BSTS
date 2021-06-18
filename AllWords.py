import ujson
import os

dir = "/home/zjq/WSM/"
posting_root = dir + "postings/"
words_path = dir + "words.txt"

docs = os.listdir(posting_root)

words = ""

# Collect all the words in total files
for doc in docs:
    doc_path = posting_root + doc
    with open(doc_path, 'r') as f:
        posting = ujson.load(f)
    
    for key in posting.keys():
        words += key + ' '

print(words)
with open(words_path, 'w+') as f:
    ujson.dump(words, f)