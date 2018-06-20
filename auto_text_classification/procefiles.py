# coding=utf-8
import os
import sys
import gzip
import argparse
import json

import sys
reload(sys)
sys.setdefaultencoding('utf8')

#读取目录中的文件,并过滤空格保存
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required arguments: input file.
    parser.add_argument(
        "-p", "--path",
        help="dir for the processed files",
        required=True
    )

    parser.add_argument(
        "-o", "--output",
        help="output file",
        default="output.out"
    )

    args = parser.parse_args()
    assert os.path.exists(args.path), "The path not exist."

    outfile = open(os.path.join(args.path, args.output), "w")
    for file in os.listdir(args.path):
        (shortname, ext) = os.path.splitext(file)
        print("extension is:", ext)
        if(not (ext==".txt" or ext==".output") ):
            continue

        sourceFile = os.path.join(args.path, file)
        with open(sourceFile, "r") as f:
            for line in f:
                line_split = line.strip().split("\t")
                if (len(line_split) <= 1):
                    continue
                flag = (0 if (line_split[0]=='normal') else 1)
                doc = line_split[1].replace(' ', '')
                outfile.write("%d\t%s\n"%(flag, doc))