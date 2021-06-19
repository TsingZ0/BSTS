import ujson
import os
import re
import copy
import numpy as np
import gc
import time
import cProfile
from symspellpy import SymSpell, Verbosity
from flask import Flask, render_template, request

app = Flask(__name__)

dir = "/home/zjq/WSM/"
K = 1 # max corrected number of words
MED = 2 # max edit distance
show_doc_nums = 10

posting_root = dir + "postingss/"
doc_root = dir + "trials/"
res_root = dir + "results/"
words_path = dir + "words.txt"
words_dict_path1 = dir + "word_dict1.pkl"
words_dict_path2 = dir + "word_dict2.pkl"

# pre-loading for fuzzy search and spell correction
start = time.time()
print("Loading symspell dictionary ...")
sym_spell1 = SymSpell()
sym_spell2 = SymSpell()
sym_spell1.load_pickle(words_dict_path1)
sym_spell2.load_pickle(words_dict_path2)
print("Loading symspell dictionary costs time: ", time.time()-start)

# input_keys = "seperate /s ( screens /2 monitor )"
# input_keys = "seperate /s monitor"

# operation selection
regex = re.compile(r'&| |%|/(p|s|[0-9])|\+(p|s|[0-9])|\(|\)')

start = time.time()
# load idxes for converting
print("Loading idxes ...")

with open(doc_root + "index.json") as f:
    indexs = ujson.load(f)

with open(doc_root + "docidx.json") as f:
    docidx = ujson.load(f)

print("Loading idxes costs time: ", time.time()-start)


def search(input_keys, sort_item, show_doc_nums):
    start = time.time()

    # keys extraction including words and operation
    input_keys = input_keys.split(" ")
    input_keys.append(None)

    # recover OR(' ')
    input_temp = []
    for idx in range(len(input_keys)-1):
        input_temp.append(input_keys[idx])
        try:
            if regex.search(input_keys[idx]) == None and regex.search(input_keys[idx+1]) == None:
                input_temp.append(' ')
        except TypeError:
            pass
    input_keys = copy.deepcopy(input_temp)
    
    res = main(input_keys, '0_0', sort_item, show_doc_nums)

    print("Total cost time: ", time.time()-start)

    return res


def fuzzy_search_spell_correction(input_keys, sort_item, show_doc_nums):
    has_res = True
    for idx, input_key in enumerate(input_keys):
        if regex.search(input_keys[idx]) == None:
            # Fuzzy search on our own dictionary
            suggestions = sym_spell1.lookup(input_key, Verbosity.ALL,
                                    max_edit_distance=MED, include_unknown=False)
            if len(suggestions) < 1:
                # Spell correction on online frequent dictionary
                suggestions.extend(sym_spell2.lookup(input_key, Verbosity.CLOSEST,
                                    max_edit_distance=MED, include_unknown=False))

            if len(suggestions) < 1:
                has_res = False
                continue
            else:
                has_res = True

            for idx2, suggestion in enumerate(suggestions[:K+1]):
                res = str(suggestion).split(', ')[0]
                if res != input_key:
                    # print(f"Do you mean {res} instead of {input_key} (y or n)?")
                    # judge = input()
                    # if judge == 'n':
                    #     continue

                    input_keys[idx] = res
                    main(input_keys, input_key+'('+str(idx)+')'+'_'+res+'('+str(idx2)+')', sort_item, show_doc_nums, flag="fuzzy")
                    input_keys[idx] = input_key

    if has_res == False:
        return f"Your enter of {input_keys} is wrong, please enter again."
    else:
        return ""


def main(input_keys, tag, sort_item, show_doc_nums=show_doc_nums, flag=""):
    if not os.path.exists(res_root):
        os.mkdir(res_root)
    path = res_root + tag + '.json'

    docdict = main_docdict(input_keys)

    # FileNotFoundError
    if type(docdict) == type(""):
        return docdict
    
    dialogues = []

    # recover DocID and DocLines
    docs = {}
    for line in docdict.keys():
        line = int(line)
        did = str(indexs[line][0])
        if did not in docs:
            docs[did] = set()
        docs[did].add(indexs[line][1])

    # select the most frequent docs
    docs = {k: v for k, v in sorted(docs.items(), key=lambda item: len(item[1]))}
    keys = list(docs.keys())[:show_doc_nums]

    # launch fuzzy_search_spell_correction only when the result is blank
    # $flag prevents running fuzzy recursively
    if len(keys) < 1 and flag != "fuzzy":
        return fuzzy_search_spell_correction(input_keys, sort_item, show_doc_nums)
    else:
        # store results locally
        for doc in keys:
            with open(doc_root + doc + '.json', 'r') as f:
                DocLog, Logs = ujson.load(f)
                
            lines = docs[doc]
            for line in lines:
                line = int(line)
                if Logs[line][0] == 'message':
                    dialogues.append({'type': Logs[line][0], 
                                    'time': DocLog[0] + Logs[line][1], 
                                    'sender': Logs[line][2], 
                                    'receiver': Logs[line][3], 
                                    'text': Logs[line][4], 
                                    'text_length': len(Logs[line][4])})
                elif Logs[line][0] == 'name_change':
                    dialogues.append({'type': Logs[line][0], 
                                    'time': "None", 
                                    'sender': Logs[line][1], 
                                    'receiver': Logs[line][2], 
                                    'text': Logs[line][3], 
                                    'text_length': len(Logs[line][3])})
                else:
                    dialogues.append({'type': Logs[line][0], 
                                    'time': DocLog[0] + Logs[line][1], 
                                    'sender': Logs[line][2], 
                                    'receiver': 'None', 
                                    'text': Logs[line][3], 
                                    'text_length': len(Logs[line][3])})
        
        # sort results according to $sort_item given by the user
        dialogues = sorted(dialogues, key=lambda x: x[sort_item])

        with open(path, 'w+') as f:
            ujson.dump(dialogues, f)

        return ""
    

# return the result posting dict
def main_docdict(input_keys):
    if len(input_keys) == 1:
        word = input_keys[0]
        let = word[:2] if len(word) >=2 else word+'a'
        # let = word[0]
        try:
            with open(posting_root+let+'.json', 'r') as f:
                postings = ujson.load(f)
        except FileNotFoundError:
            return f"Invalid word: {word}! Please re-enter it"

        return postings[word]

    # similar to postfix expression
    docd_stack, op_stack = [], []

    parenthese = 0
    for key in input_keys:
        if key == '(':
            if parenthese == 0:
                input_temp = []
            else:
                input_temp.append('(')
            parenthese += 1
        elif key == ')':
            parenthese -= 1
            if parenthese == 0:
                docd_stack.append(main_docdict(input_temp))
                input_temp = []
            else:
                input_temp.append(')')
        elif regex.search(key) == None and parenthese == 0:
            docd_stack.append(main_docdict([key]))
        elif parenthese == 0:
            op_stack.append(key)
        else:
            input_temp.append(key)

        if len(docd_stack) > 1:
            docd1, docd2 = docd_stack
            docd_stack = []
            op = op_stack.pop()
            if op == '&': # for AND
                docd_stack.append(docdict_and(docd1, docd2))
            elif op == ' ': # for OR
                docd_stack.append(docdict_or(docd1, docd2))
            elif op == '%': # for NOT
                docd_stack.append(docdict_not(docd1, docd2))
            elif op[1] == 'p' or op[1] == 's': # for /p, /s, +p, +s
                docd_stack.append(docdict_ps(docd1, docd2, op))
            else: # for /n, +n
                docd_stack.append(docdict_n(docd1, docd2, op))

    return docd_stack[0]


def key_intersection(docd1, docd2):
    keys1 = set(docd1.keys())
    keys2 = set(docd2.keys())
    keys_ = keys1.intersection(keys2)

    return list(keys_)

def key_union(docd1, docd2):
    keys1 = set(docd1.keys())
    keys2 = set(docd2.keys())
    keys_ = keys1.union(keys2)

    return list(keys_)

# global line id to DocID
def docid_look(lines):
    docids = set()
    for line in lines:
        docids.add(indexs[int(line)][0])

    return docids

def docdict_and(docd1, docd2):
    docid1 = docid_look(list(docd1.keys()))
    docid2 = docid_look(list(docd2.keys()))
    docids = docid1.intersection(docid2)

    keys_ = []
    for did in docids:
        did = str(did)
        keys_.extend(list(range(docidx[did][0], docidx[did][0] + docidx[did][1])))

    docd_temp = dict()
    for key in keys_:
        key = str(key)
        # some keys may not in both docd1 and docd2
        if key in docd1 and key in docd2:
            docd_temp[key] = list(set(docd1[key]).union(set(docd2[key])))
        elif key in docd1:
            docd_temp[key] = docd1[key]
        elif key in docd2:
            docd_temp[key] = docd2[key]

    del docd1, docd2
    # gc.collect()

    return docd_temp

def docdict_or(docd1, docd2):
    docd_temp = docd1

    for k, v in docd2.items():
        if k not in docd_temp:
            docd_temp[k] = []
        docd_temp[k].extend(v)

    del docd1, docd2
    # gc.collect()

    return docd_temp

def docdict_not(docd1, docd2):
    docid1 = docid_look(list(docd1.keys()))
    docid2 = docid_look(list(docd2.keys()))
    docids = docid1.difference(docid2)

    keys_ = []
    for did in docids:
        did = str(did)
        keys_.extend(list(range(docidx[did][0], docidx[did][0] + docidx[did][1])))

    docd_temp = dict()
    for key in keys_:
        key = str(key)
        # some keys may not in both docd1 and docd2
        if key in docd1:
            docd_temp[key] = docd1[key]

    del docd1, docd2
    # gc.collect()

    return docd_temp

def docdict_ps(docd1, docd2, ps):
    keys_ = key_intersection(docd1, docd2)

    docd_temp = dict()
    for key in keys_:
        if ps[0] == '/':
            docd_temp[key] = list(set(docd1[key]).union(set(docd2[key])))
        elif docd1[key][-1] < docd2[key][0]:
            docd_temp[key] = list(set(docd1[key]).union(set(docd2[key])))

    del docd1, docd2
    # gc.collect()

    return docd_temp

def docdict_n(docd1, docd2, n):
    prefix = n[0]
    n = int(n[1:])+1
    keys_ = key_intersection(docd1, docd2)

    docd_temp = dict()
    for key in keys_:
        if prefix == '+':
            # docd1 
            for value in docd1[key]:
                idx = np.searchsorted(docd2[key], value+n)
                if idx < len(docd2[key]) and docd2[key][idx] == value+n:
                    if key not in docd_temp:
                        docd_temp[key] = []
                    docd_temp[key].append(docd2[key][idx])
        else:
            # docd1 
            for value in docd1[key]:
                idx1 = np.searchsorted(docd2[key], value)
                idx2 = np.searchsorted(docd2[key], value+n+1)
                if idx1 != idx2:
                    if key not in docd_temp:
                        docd_temp[key] = []
                    docd_temp[key].extend(docd2[key][idx1: idx2])
            # docd2 
            for value in docd2[key]:
                idx1 = np.searchsorted(docd1[key], value)
                idx2 = np.searchsorted(docd1[key], value+n+1)
                if idx1 != idx2:
                    if key not in docd_temp:
                        docd_temp[key] = []
                    docd_temp[key].extend(docd1[key][idx1: idx2])

    del docd1, docd2
    # gc.collect()

    return docd_temp

# Flask app
@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run/', methods=['GET', 'POST'])
def run():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        input_keys = request.form.get('search_keys')
        sort_item = request.form.get('sort_item')
        show_doc_nums = int(request.form.get('show_doc_nums'))

        os.system('rm -r ../results/')
        info = search(input_keys, sort_item, show_doc_nums)

        res = []
        file_list = os.listdir(res_root)
        for file_name in file_list:
            with open(res_root+file_name) as f:
                res.append(ujson.load(f))

        return render_template('index.html', res=res, info=info)


if __name__ == "__main__":
    # with cProfile.Profile() as pr:
    #     input_keys = "machine % learning"
    #     sort_item = "time"
    #     show_doc_nums = 20
    #     search(input_keys, sort_item, show_doc_nums)
    # pr.print_stats()

    app.run()