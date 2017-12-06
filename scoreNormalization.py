# --------------------------------------------------------------------------------------------------------------
#	run this script as:
# 		python scoreNormalization.py path_to/input_file.xml path_to/output_file.xml [gamma]
# --------------------------------------------------------------------------------------------------------------

import re
import sys
from xml.dom import minidom
import re
import operator
import myetree.ElementTree as ET
from collections import OrderedDict



if len(sys.argv)<3:
	raise RuntimeError,'Run script as:\n\tpython scoreNormalization.py path_to/input_file.xml path_to/output_file.xml [gamma]'

# gamma can be tuned
gamma = 1

input_file = sys.argv[1]
output_file = sys.argv[2]
if len(sys.argv)>3:
	gamma = float(sys.argv[3])


# sum over all hits of a query:
# open input file with original scores
doc = ET.parse(input_file)
detected_kwlists = doc.getroot().findall('detected_kwlist')
# for each query detected in the file
for dkw in detected_kwlists:
	# get all the hits and sum of all their scores
	kws = dkw.findall('kw')
	sum_scores = sum([pow(float(kw.get('score')),gamma) for kw in kws])
	# for each hit update the score by dividing by the sum of the scores
	for kw in kws:
		att['file'] = kw.attrib['file']
		att['channel'] = kw.attrib['channel']
		att['tbeg'] = kw.attrib['tbeg']
		att['dur'] = kw.attrib['dur']
		att['score'] = new_score
		new_score = str(pow(float(kw.attrib['score']),gamma)/sum_scores)
		att['decision'] = kw.attrib['decision']
		kw.attrib = att

# write new file
ET.ElementTree(doc.getroot()).write(output_file, encoding='utf-8')


