# coding=utf-8
# /usr/bin/python

import json
import sys
# from tencentinterface import AIInterface
from fuzzywuzzy import fuzz

import pytesseract
#import Image
from PIL import Image
from PIL import ImageEnhance
from PIL import ImageFilter
#import ImageEnhance
#import cv2

def resize(w, h, w_box, h_box, pil_image):
    '''
    resize a pil_image object so it will fit into
    a box of size w_box times h_box, but retain aspect ratio
    '''
    f1 = 1.0*w_box/w  # 1.0 forces float division in Python2
    f2 = 1.0*h_box/h
    factor = min([f1, f2])
    #print(f1, f2, factor)  # test
    # use best down-sizing filter
    width = int(w*factor)
    height = int(h*factor)
    return pil_image.resize((width, height), Image.ANTIALIAS)


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("Need Input Filepath!")
        sys.exit(0)
    print("FileName is:", sys.argv[1])
    # print("check string is:", sys.argv[2])

    for i in range(1, 2):
        img = Image.open(sys.argv[1])#.convert('P')

        w, h = img.size

        # t2 = img  # 转rgb模式
        # for i in range(0, t2.size[0]):
        #     for j in range(0, t2.size[1]):
        #         r = t2.getpixel((i, j))[0]
        #         g = t2.getpixel((i, j))[1]
        #         b = t2.getpixel((i, j))[2]
        #         if b > r and b > g and (r, g < 100) and (b < 210):
        #             r = 255
        #             g = 255
        #             b = 154  # 背景蓝色变黄
        #         elif (r, g, b >= 180):
        #             b = 0  # 白色字变黑
        #             g = 0
        #             r = 0
        #         t2.putpixel((i, j), (r, g, b))
        # img = t2

        #enhancer = ImageEnhance.Contrast(img)
        #enhancer = enhancer.enhance(0)
        #enhancer = ImageEnhance.Brightness(enhancer)
        #enhancer = enhancer.enhance(2)

        #enhancer = ImageEnhance.Brightness(enhancer)
        #enhancer = enhancer.enhance(4)

        #img = img.convert('RGBA')
        enhancer = ImageEnhance.Color(img)
        enhancer = enhancer.enhance(0)
        enhancer = ImageEnhance.Contrast(enhancer)
        enhancer = enhancer.enhance(68.0)
        enhancer = ImageEnhance.Brightness(enhancer)
        enhancer = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Sharpness(enhancer)
        img = enhancer.enhance(72.0)
        #img = img.filter(ImageFilter.SHARPEN)


        #img = resize(w, h, w * 1, h * 1, img)
        img.save("1.png")

        #img = img.point(table,'1')
        #img = cv2.imread(sys.argv[1])
        #img.load()
        code = pytesseract.image_to_string(img, lang='chi_sim')

        # img.close()
        code = code.replace(' ', '').replace('\n', '')
        print code

    reload(sys)
    sys.setdefaultencoding('utf-8')
    ratio = (fuzz.partial_ratio(code, sys.argv[2]))
    print("ratio is:%f"%(ratio))
    if(ratio>=0.1):
        print("ratio >= 0.1")

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




