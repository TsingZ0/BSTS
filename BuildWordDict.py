import time
import pkg_resources
from symspellpy import SymSpell

dir = "/home/zjq/WSM/"
words_path = dir + "words.txt"
words_dict_path1 = dir + "word_dict1.pkl"
words_dict_path2 = dir + "word_dict2.pkl"

start = time.time()

sym_spell1 = SymSpell() # for our own word dictionary
sym_spell1.create_dictionary(words_path)

sym_spell2 = SymSpell() # for the frequency dictionary online
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell2.load_dictionary(dictionary_path, term_index=0, count_index=1)

sym_spell1.save_pickle(words_dict_path1)
sym_spell2.save_pickle(words_dict_path2)

print("Building dictionary costs time: ", time.time()-start)