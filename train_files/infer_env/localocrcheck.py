# coding=utf-8
# /usr/bin/python

import json
import sys
#from tencentinterface import AIInterface
from fuzzywuzzy import fuzz

import pytesseract
from PIL import Image
    
if __name__ == "__main__":
    if(len(sys.argv)<2):
        print("Need Input Filepath!")
        sys.exit(0)
    print("FileName is:",sys.argv[1])
    #print("check string is:", sys.argv[2])

    img = Image.open(sys.argv[1])
    code = pytesseract.image_to_string(img,lang='chi_sim')
    code = code.replace(' ','').replace('\n','')
    print code

    reload(sys)
    sys.setdefaultencoding('utf-8')
    print(fuzz.partial_ratio(code, sys.argv[2]))

    # #interf = AIInterface()
    # #print(interf.generalocr(sys.argv[1]))
    # #result = interf.generalocr(sys.argv[1])
    # rjson = json.loads(result)
    #
    # reload(sys)
    # sys.setdefaultencoding('utf-8')
    # #print(rjson)
    # if(rjson["ret"]==0):
    #     items = rjson["data"]["item_list"]
    #
    #     itemsstr = ""
    #     for item in items:
    #         itemsstr=itemsstr+item["itemstring"]
    #
    #     print(itemsstr)
    #     print(fuzz.partial_ratio(itemsstr, sys.argv[2]))
        
                  
        
        
    