# --------------------------------------------------------------------------------------------------------------
#	run this script as:
# 		python morphoDecomposition.py path_to/input_file.{ctm, xml} path_to/dict_file.dct path_to/output_file.{ctm, xml}
# --------------------------------------------------------------------------------------------------------------


from xml.dom import minidom
import re
import sys
from pprint import pprint
from xml.dom import minidom
import operator
import myetree.ElementTree as ET
from collections import OrderedDict


''' ------------------------------------- FUNCTIONS ------------------------------------- '''

# create dictionary from the morphologic dictionary file
def make_dict(lines):

	D = {}
	for l in lines:
		words = re.split('\s+', l)[:-1]
		# first word is the key...
		key = words[0].lower()
		# ...the rest is a list (and value in the dictionary)
		others = [w.lower() for w in words[1:]]
		# add new entry
		D[key] = others
	return D




# get new tbegs, durs and scores for each new word
def split_tds(D, info):

	t = d = s = []

	# decompose word
	w_decomp = D[info[4]]
	
	# assign same duration to each new w, creating a list of len(w_decomp) equal elements
	d = [round(float(info[3]) / len(w_decomp), 2)] * (len(w_decomp) - 1)
	# ...actually we adjust the last elem duration in order to 'fit' the duration of the original word
	d.append( float(info[3]) - sum(d) )
	
	# assign same score as original to each new w, creating a list of len(w_decomp) equal elements
	s = [float(info[5])] * len(w_decomp)

	# initial timestamp
	t.append(float(info[2]))
	for i in range(1,len(w_decomp)):
		t.append(t[i-1]+d[i-1])		# start when the previous w ends

	return t, d, w_decomp, s



''' ------------------------------------- MAIN ------------------------------------- '''



if len(sys.argv)!=4:
	raise RuntimeError,'Run script as:\n\tpython morpoDecomposition.py path_to/input_file.{ctm, xml} path_to/dict_file.dct path_to/output_file.{ctm, xml}'

input_f = sys.argv[1]
dct = sys.argv[2]
output_f = sys.argv[3]


error = False
# if names given without extension error
if not input_f.lower().endswith(('.xml')) and not input_f.lower().endswith(('.ctm')):
	error = True
if not dct.lower().endswith(('.dct')):
	error = True
if not output_f.lower().endswith(('.xml')) and not output_f.lower().endswith(('.ctm')):
	error = True

if error:
	raise RuntimeError,'Run script as:\n\tpython morpoDecomposition.py path_to/input_file.{ctm, xml} path_to/dict_file.dct path_to/output_file.{ctm, xml}'


# read morpological file and build dictionary
d = open(dct)
dct_lines = d.readlines()
d.close()
D = make_dict(dct_lines)

extension = input_f.split('.')[-1]

if extension=='xml':
	# ---- file xml: it's the query.xml
	# open query file and get all hits for all queries
	doc = ET.parse(input_f)
	kws = doc.getroot().findall('kw')

	# for each hit in the file
	for kw in kws:
		kwtext = re.split('\s+', kw.find('kwtext').text)
		text = ''
		# split each word
		for w in kwtext:
			# get decomposition for w from morphological dictionary D
			decomposition = D[w]
			# update text of the tree node
			for s in decomposition:
				text += s+' '
		# remove (eventual) last space
		if text[-1]==' ':
			text = text[:-1]
		kw.find('kwtext').text = text[:].lower()
	# write resulting xml in output file
	ET.ElementTree(doc.getroot()).write(output_f, encoding='utf-8')


if extension=='ctm':
 	# ------------------  file ctm: it's the decode.ctm
 	with open(output_f,'w') as f:
	
		# open input file
 		i = open(input_f)
 		input_lines = i.readlines()
 		i.close()
		
		if input_lines[-1]:
			input_lines = input_lines[:-2]

 		# read each line
 		for l in input_lines:
 			# splid words, take care of timestamps and scores
			info = re.split('\s+', l)[:-1]
			# set tbegs, split duration and scores
			tbegs, durs, words, scores = split_tds(D, info)
			for i in range(len(words)):
				line = ' '.join([info[0], info[1], str(tbegs[i]), str(durs[i]), words[i].lower(), str(scores[i])])
				f.write(line+'\n')


