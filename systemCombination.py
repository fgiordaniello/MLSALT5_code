import myetree.ElementTree as ET
from collections import OrderedDict
import re
import operator


''' ----------------- FUNCTIONS ----------------- '''

# verify if the two instances overlap
def same_hit(kw1, kw2):
    
    if kw1.get("file")==kw2.get("file") and kw1.get("channel")==kw2.get("channel"):
        
        start1 = float(kw1.get("tbeg"))
        end1 = start1 + float(kw1.get("dur"))
        start2 = float(kw2.get("tbeg"))
        end2 = start2 + float(kw2.get("dur"))

        # check if they overlap 
        if end1 >= start2 and end2 >= start1:
            return True
    
    return False



# indent the xml to be read by the scoring function
# function adapted from: https://norwied.wordpress.com/2013/08/27/307/
def indent(elem, level=0):
    i = "\n"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i



''' ----------------- MAIN ----------------- '''

file1 = sys.argv[1]
file2 = sys.argv[2]
output_file = sys.argv[3]
    
# load file for system2
doc1 = ET.parse(file1)
detected_kwl_1 = doc1.getroot()

# load file for system1
tree2 = ET.parse(file2)
detected_kwl_2 = tree2.getroot()

# get all the queries in system2
queries_2 = detected_kwl_2.findall('detected_kwlist')
kwids=[kw.get('kwid') for kw in queries_2]

# for each query in system1 find the one with same kwid in system2
for query_1 in detected_kwl_1:
        
    kwid = query_1.get("kwid")
    query_2 = []

    # get all the queries with id kwid in system2
    for q in queries_2:
        if q.get('kwid') == kwid:
            query_2.append(q)
        
    if len(query_2) == 1:
        query_2 = query_2[0]

    # compare pairs of hits and update the score if they overlap
    for kw1 in query_1:
        for kw2 in query_2:
                
            if same_hit(kw1, kw2):
                kw1.set( "score", str( float(kw1.get("score")) + float(kw2.get("score")) ) )
                # remove current hit from the list
                query_2.remove(kw2)
                break

            # add the remaining hits of query_2
            for kw2 in query_2:
                query_1.append(kw2)
                query_2.remove(kw2)
            # remove query_2 from the list
            if query_2 in queries_2:
                queries_2.remove(query_2)

# add in system1 the remaining queries from system2
if len(queries_2) > 0:
    for query_2 in queries_2:
        if len(query_2) > 0:
            detected_kwl_1.append(query_2)


root_out = doc1.getroot()
indent(root_out)
out = ET.ElementTree(root_out)
out.write(output_file, encoding='utf-8')

