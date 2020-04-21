#!/usr/bin/env python

'''
    util.py

    Objective: Utility functions for reading and writing data.

    Methods:    write_outfile(filename, results, subjectLine=None, append_write)
                write_json(filename, your_dict, append_write)
                load_json(src)
                quick_write(filename, results, subjectLine=None, append_write)
                pretty_print_json(filename)
                read_hp_cannons()
                remove_stop_words(text)
                remove_punctuation(text)
                tokenize_text(text)
                get_hp_datasets(chapters)
                pickle_dump(data, dest)
                pickle_load(src)

    Folders:    code/
                data/
                out/
                vectors/

    Usage:   
'''

import csv          
import re
import os, sys
import tarfile
import json
import pickle as pkl
import pytz
from datetime import datetime
import string
from string import punctuation


import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.data import load
from nltk.tokenize.casual import TweetTokenizer
from nltk.tokenize import word_tokenize
nltk.download('stopwords')

stop_words = stopwords.words('english')

dateTimeObj = datetime.now(pytz.timezone("America/New_York"))

baseDir = '/nlp/data/irebecca/IFaTG/Final_Project/'
outDir = '/nlp/data/irebecca/IFaTG/Final_Project/out/'
dataDir = '/nlp/data/irebecca/IFaTG/Final_Project/data/'
outDir = '/nlp/data/irebecca/IFaTG/Final_Project/out_small/'

# baseDir = '/Users/rebeccaflores/Documents/GitHub/IFaTG/Final_Project/'
# outDir = '/Users/rebeccaflores/Documents/GitHub/IFaTG/Final_Project/out/'
# dataDir = '/Users/rebeccaflores/Documents/GitHub/IFaTG/Final_Project/data/'
# outDir = '/Users/rebeccaflores/Documents/GitHub/IFaTG/Final_Project/out/'

## len of small data results
# In [3]: len(data)                                                                                                     
# Out[3]: 271

## len of the large data results
# In [3]: len(data)                                                                                                     
# Out[3]: 22719

'''
    File Organization:  code/
                        data/
                        out/
                        vectors/
'''

###################################################
# Functions for reading and writing files
###################################################


def write_outfile(results, filename, append_write, subjectLine=None, ):
    '''
    Input: A results list ['this is an', 'example'] or [45,67,23,0,1]
    Output: write each item of the list on a new line
    '''

    with open(outDir + filename, append_write) as f:
        f.write('*** New File ' + str(dateTimeObj) + '***\n\n')
        if subjectLine is not None:
            f.write('subjectLine: ' + subjectLine + '\n\n')
        for item in results:
            f.write(str(item) + '\n')
        f.write('\n\n')

    f.close()


def write_json(your_dict, filename):
    '''
    Input: A your_dict dict {}
    Output: A string if your dictionary written to a file
    '''

    with open(outDir + filename, 'w') as f:
        f.write(json.dumps(your_dict))

    f.close()

def load_json(filename):
    '''
        Input: source path of where your json object it
        Output: python dictionary object
    '''

    with open(outDir + filename, 'r') as fin:
        print('File Path: ', outDir + filename)
        data = json.load(fin)

    return data


def quick_write(results, filename, append_write, subjectLine=None, ):
    '''
    Input: A results string 'this is an example' or '5678'
    Output: writes the whole string to a line
    '''

    with open(outDir + filename,append_write) as f:
        f.write('*** New File ' + str(dateTimeObj) + '***\n\n')
        if subjectLine is not None:
            f.write('subjectLine: ' + subjectLine + '\n\n')

        f.write(str(results) + '\n')
        f.write('\n')

    f.close()

def pretty_print_json(filename):

    counter = 0
    max_num = 10
    json_filename = sys.argv[1]
    if len(sys.argv) >2: 
        max_num = sys.argv[2]

    with open(json_filename) as json_file:
        for line in json_file:
            story = json.loads(line)
            print(json.dumps(story, indent=4))

def read_hp_cannons():
  '''
    Reads in the Harry Potter dataset of original cannons, and breaks it up into a list of strings

    Returns:
        chapter_text, a list of strings, where each item in the list is one chapter from hp cannons
  '''
  chapters = []
  aliases = []
  chapter_text = ''
  harry_potter_files = [baseDir + 'data/Harry Potter 1 - Sorcerer\'s Stone.txt',
                        baseDir + 'data/Harry Potter 2 - Chamber of Secrets.txt',
                        baseDir + 'data/Harry Potter 3 - The Prisoner Of Azkaban.txt', 
                        baseDir + 'data/Harry Potter 4 - The Goblet Of Fire.txt', 
                        baseDir + 'data/Harry Potter 5 - Order of the Phoenix.txt', 
                        baseDir + 'data/Harry Potter 6 - The Half Blood Prince.txt', 
                        baseDir + 'data/Harry Potter 7 - Deathly Hollows.txt'] 

  for filename in harry_potter_files:                       
    with open(filename, "r",encoding='utf-8', errors='ignore') as f:
        for line in f.readlines():
            line = line.strip()
            toy = tokenize_text(line)
            for token in toy:
                if token == 'Professor':
                    check = toy.index(token) + 1
                    if check >= len(toy):
                        continue
                    else:
                        aliases.append(token + " " + toy[check])
            if re.findall("^Chapter",line,re.IGNORECASE):
                chapters.append(chapter_text)
                chapter_text = ''
            else:
                ## As long as chapter not in the line, append the line to chapter_text
                chapter_text += (' ' + line)
  
  ## Each element in chapters[] is a whole string chapter out of the harry potter books  
  return chapters, aliases

def write_hp_cannons(chapters):

    with open(dataDir + 'aggregated_hpcannon.txt', 'w') as hp:
        for chapter_string in chapters:
            hp.write(chapter_string + '\n')

    hp.close()


###################################################
# Functions to Clean Data
################################################### 

def remove_stop_words(text):
    lowered_words = [t.lower() for t in text]
    filtered_words = [t for t in lowered_words if t not in stop_words]
    return filtered_words

def remove_punctuation(text):
    ## remove punctuation

    filtered_words = [word for word in text if word not in string.punctuation]
    # filtered_words = [word for word in filtered_words if word not in doubles]
    
    return filtered_words

def tokenize_text(text):
    tknzr = TweetTokenizer()
    return tknzr.tokenize(text)



###################################################
# Functions for loading and extracting data
###################################################

def get_hp_datasets(chapters):
    '''
        Splits text processing into test set, val set, and train set
        Return: No return.  Immediately write's to file

        Usage:
            chapters = read_hp_cannons()
            get_hp_datasets(chapters)
    '''
    train_set = ''
    test_set = ''
    val_set = ''

    random.seed(5)
    for chapter in chapters:
        r = random.random()
        if r < 0.9:
            train_set += '[CHAPTER] ' + chapter
        elif r < 0.95:
            print("You made it!")
            val_set += '[CHAPTER] ' + chapter
        else:
            test_set += '[CHAPTER] ' + chapter  

    ## Write Files
    datasets = [train_set, val_set, test_set]
    output_files = ['hp_train_set.txt', 'hp_val_set.txt', 'hp_test_set.txt']
    for dataset, filename in zip(datasets, output_files):
        write_outfile(filename,dataset) 


###################################################
# Functions for loading and saving using pickle
###################################################

def pickle_dump(data, dest):
    with open(outDir + dest, 'wb') as fout:
        pkl.dump(data, fout)

def pickle_load(filename):
    with open(outDir + filename, 'rb') as fin:
        print('filepath: ', outDir + source)
        data = pkl.load(fin)
    ## order = len(list(data.keys())[0])
    return data ##, order
    
