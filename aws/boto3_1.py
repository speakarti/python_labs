import boto3
# pip install boto3
# fresh water dolphin native to the Amazon river
from pathlib import Path

MYFILE = "C:\scripts\test.txt"

def fn_s3fileupload(filename):
    if filename:
        with open(filename, "r") as f:
            filecontents  = f.readlines()
            print(filecontents)


def main():
    fpath = Path("C:\scripts\test.txt")
    fn_s3fileupload(fpath)
    # ensure to install & configure aws cli on the machine
    #print(dir(boto3))
    #s3 = boto3.client('s3')
    #s3.upload_file(r"c:\scripts\test.txt",'san02','test.txt')


if __name__ == '__main__':
    main()