import os
from pathlib import Path # pathlib is new library as against os.path, so much better functionality
# read https://docs.python.org/3/library/pathlib.html

import logging
#https://www.geeksforgeeks.org/python-program-to-get-the-file-name-from-the-file-path/

modulefilename = __file__
logger = logging.getLogger(__name__)
module_file = __file__
module_name = __name__
logging.basicConfig(filename= "os_module.log", filemode = 'w', level = logging.INFO)

def fn_getpaths_from_pathlib():
    
    print(f"Path.cwd(): {Path.cwd()}")

    # Get the filename from the path without extension split()    
    exepath = 'D:\home\Riot Games\VALORANT\live\VALORANT.exe'
    O_path = Path(exepath)
    O_path1 = Path(__file__)    

    if O_path:
        print(f"O_path.stem: {O_path.stem}")
        print(f"O_path.name: {O_path.name}")
        print(f"O_path.drive: {O_path.drive}")
        print(dir(O_path))

    if O_path1:
        print(f"O_path1.stem: {O_path1.stem}, O_path1.name: {O_path1.name}, O_path1.drive: {O_path1.drive}, O_path1.absolute(): {O_path1.absolute()}, O_path1.parent(): {O_path1.parent} ")
        print(dir(O_path1))
        
        if Path.is_dir(O_path1.parent):
            fn_traverse_dir(O_path1.parent)


def fn_traverse_dir(dir):
    path = Path(dir)
    for item in path.iterdir():
        print(item)    


def fn_getpaths_from_os():
    # Get the filename from the path without extension split()
    exepath = 'D:\home\Riot Games\VALORANT\live\VALORANT.exe'
    logger.info(exepath)
    filename = os.path.basename(exepath) #Get the File Name From the File Path using os.path.basename
    filetuple = os.path.splitext(exepath) #returns a tuple with split at extenstion level

    print(filename)
    print(filetuple)

    #Get the File Name From the File Path Using Pathlib
    print(Path(exepath).stem) # prints filename without extension
    print(Path(exepath).name) # prints full filename with extension

    # curerent wortking dir
    sz_current_working_dir = os.getcwd()
    print(os.path.basename(sz_current_working_dir))

    #check if file exissts in a given dir
    ll = os.listdir(sz_current_working_dir)
    print(f"ll: {ll}")
    if module_file in ll:
        print("exissts")

    print(type(os.walk(sz_current_working_dir)))
    
    for folder, subfolders, files in os.walk(sz_current_working_dir):
        print(folder, subfolders, files)


def main():
    #fn_getpaths_from_os()
    #fn_getpaths_from_pathlib()
    sz_path1 = r'C:\Users\aggar\python_vscode'
    #o_path1 = Path(sz_path1)
    fn_traverse_dir(sz_path1)


if __name__ == '__main__':
    logger.info(f"dir(os) : {dir(os)}")
    logger.info(f"dir(os.path): {dir(os.path)}|")
    logger.info(__file__)
    logger.info(module_name)

    main()