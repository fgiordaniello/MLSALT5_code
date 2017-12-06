# --------------------------------------------------------------------------------------------------------------
#    run this script as:
#         python graphemicCM.py path/to/queries.xml path/to/decode.ctm path/to/output_queries.xml
# --------------------------------------------------------------------------------------------------------------

import numpy as np
import time
import datetime
import re
import sys
from xml.dom import minidom
import operator
import myetree.ElementTree as ET
from collections import OrderedDict


global CM

if len(sys.argv)<4:
    raise RuntimeError,'\nRun script as:\tpython graphemicCM.py path/to/queries.xml path/to/decode.ctm path/to/output_queries.xml'

''' ------------------------------------ FUNCTIONS ----------------------------------------- '''

# build the confusion matrix basing on grapheme.map
def generate_CM(lines):

    CM = {}
    for l in lines:
        w, sub, n = re.split('\s+', l)[:-1]
        if w not in CM:
            CM[w] = {}
        if sub not in CM[w]:
            CM[w][sub] = []
        CM[w][sub].append(int(n))

    # normalise the no. of occurences over all possible substitution and add
    # this probability (of w being substituted w/ sub) in the confusion matrix
    def normalize_CM(CM):
        for w in CM:
            tot_times = sum([int(CM[w][x][0]) for x in CM[w]])
            for sub in CM[w]:
                CM[w][sub].append(float(CM[w][sub][0])/tot_times)
        return CM

    return normalize_CM(CM)



# list of the iv words basing on dct
def iv_dict(dct):

    with open(dct, 'r') as f:
        lines = f.readlines()[:-1]
        D = []
        for l in lines:
            w = re.split('\s+', l)[4].lower()
            if w not in D and w.strip('\n'):
                D.append(w)
    return D




# return the iv word closest to w
def find_closest_word(IV, w):
    
    best_prob = 0
    best_w = ''
    
    # compute distance with all iv words and keep the best result
    for iv in IV:
        if abs(len(w)-len(iv)) > 4:
            prob = get_distance(w.replace("'",""), iv.replace("'",""))  # handle special chars
            if prob > best_prob:
                best_prob = prob
                best_w = iv

    return best_w, best_prob




# compute the distance between two strings
# function adapted from: http://stackoverflow.com/questions/2460177/edit-distance-in-python
def get_distance(word_1, word_2):

    n = len(word_1) + 1  # counting empty string 
    m = len(word_2) + 1  # counting empty string
 
    # initialize D matrix
    D = np.zeros(shape=(n, m), dtype=np.double)
    D[:,0] = range(n)
    D[0,:] = range(m)

    # update distances for each char
    for i in range(len(word_1)):
        for j in range(len(word_2)):

            if 'sil' in CM[word_1[i-1]]:
                cost_sil = 1 - CM[word_1[i-1]]['sil'][1]
            else:
                cost_sil = 1

            if word_1[i-1] == word_2[j-1]:
                cost = 0
            else:
                if word_2[j-1] in CM[word_1[i-1]]:
                    cost = 1 - CM[word_1[i-1]][word_2[j-1]][1]
                else:
                    cost = cost_sil
            
            # evaluate the cost of del, ins and sub
            deletion = D[i-1, j] + cost_sil
            insertion = D[i, j-1] + cost_sil
            substitution = D[i-1, j-1] + cost
            # assign the minimum cost
            D[i,j] = min(insertion, deletion, substitution)

    return D[i,j]



''' --------------------------------------- MAIN ------------------------------------------- '''

#print 'Starting at ', datetime.datetime.now()
tstart = time.time()


input_queries = sys.argv[1]
ref = sys.argv[2]
output_queries = sys.argv[3]
#print input_queries, ref, output_queries

# generate iv dictionary from the transcription ref
IV = iv_dict(ref)

# load the graphemic mapping and build the grapheme-confusion matrix CM
grph_map = 'lib/kws/grapheme.map'
with open(grph_map, 'r') as f:
    lines_map = f.readlines()
CM = generate_CM(lines_map)

# get all the hits of all the queries from the query file
doc = ET.parse(input_queries)
kws = doc.getroot().findall('kw')

# keep track of an OOV dictionary of the oov words you already encountered
# it will contain, for all the oov words, the closest iv word and the distance
OOV = {}

# for each query in the file
for kw in kws:
    kwtext = re.split('\s+', kw.find('kwtext').text)
    for i in range(len(kwtext)):
        w = kwtext[i]
        # check only the oov
        if w not in IV:
            # if w is already seen in this run we already have the info
            if w in OOV:
                closest, dist = OOV[w][0], OOV[w][1]
            # w unseen: find closest word and add entry in the OOV dict to store the info
            else:
                closest, dist = find_closest_word(IV, kwtext[i])
                OOV[w] = [closest, dist]
            kwtext[i] = closest
    kw.find('kwtext').text = ' '.join(kwtext).lower()
# save in a new file
ET.ElementTree(doc.getroot()).write(output_queries, encoding='utf-8')


#print 'Finishing at ', datetime.datetime.now()
tend = time.time()
print '\tElapsed time: ', tend-tstart, 's (', (tend-tstart)/60, 'min )'



