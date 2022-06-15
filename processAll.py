from ast import arg
import os
import sys
import zipfile
import rarfile
import py7zr
import subprocess
import shutil
import re
import resource
import argparse
library_header_file_names = ["zylib.h",  "zyrandom.c", "dynarray.c"]
library_c_file_names = ["zylib.c", "zyrandom.h", "dynarray.h"]
library_o_file_names = ["./zylib/zylib.o", "./zylib/zyrandom.o", "./zylib/dynarray.o"]
re_zylib = re.compile(" *#include *\".*zylib.[ch]\"\n")
re_zyrandom = re.compile(" *#include *\".*zyrandom.[ch]\"\n")
re_zydynarry = re.compile(" *#include *\".*dynarray.[ch]\"\n")
zy_libs_path = "./zylib" # where is all zylib file

tmp_folder = "/tmp/judge"
tmp_compile_name =  os.path.join(tmp_folder, "compile")
run_output_name =  os.path.join(tmp_folder, "run_output")
run_error_name = os.path.join(tmp_folder, "run_error")
run_all_res_name = os.path.join(tmp_folder, "all_res")
in_files = []
out_files = []
format_header = "============result of file============\n============%s============\n=====AC %d, RE %d, WA %d, total %d=====\n"
case_header = "============result of case %d============\n============%s============\n"
cur_c_libs = [0] * 3
cur_h_libs = [0] * 3   

## all sample should be put in samples folder
## each problem should own a folder to place all test samples
## each test samples should be named as %d.in and %d.out for sort
def append_input(f, input_f):
    f.write("##### input:\n")
    fin = open(input_f, 'r')
    f.writelines(fin.readlines())
    fin.close()
    f.write("#####\n")

def load_test_sample(sample_path):
    problem_dirs = os.listdir(sample_path)
    problem_dirs.sort()
    idx = 0
    for cur_pro in problem_dirs:

        cur_pro_path = os.path.join(sample_path, cur_pro)
        if not os.path.isdir(cur_pro_path):
            continue

        in_files.append([])
        out_files.append([])
        cur_pro_all_out = cur_pro_path + "_all.out"
        all_out = open(cur_pro_all_out, "w")
        
        inouts = os.listdir(cur_pro_path)
        inouts.sort()
        for case_id, name in enumerate(inouts):
            if ".in" in name:
                cur_in = os.path.join(cur_pro_path, name)
                # index = int(name[:-3])
                in_files[idx].append(cur_in)
                cors_out = cur_in[:-2] + 'out'
                if not os.path.exists(cors_out):
                    print("samples not right originzed, in out mismatch on", cur_in, "and", cors_out)
                    exit(1)
                out_files[idx].append(cors_out)

                all_out.write(case_header % (case_id//2, "AC"))
                append_input(all_out, cur_in)
                fin = open(cors_out, 'r')
                all_out.writelines(fin.readlines())
                fin.close()
                all_out.write("\n\n\n")
        all_out.write(format_header % (name, len(in_files[idx]), 0 ,0 , len(in_files[idx])))
        all_out.close()
        idx += 1

def process_lines(lines):
    #remove \n
    for idx in range(len(lines)):
        lines[idx] = lines[idx].strip("\n").strip("\r").strip("\x00")
    
    #remove empty lines at end of file
    while(len(lines) >= 1 and len(lines[-1]) == 0):
            lines = lines[:-1]
    
    # remove space at end of lines
    for idx in range(len(lines)):
        while(len(lines[idx]) > 0 and lines[idx][-1] == " "):
            lines[idx] = lines[idx][:-1]
    return lines

def testOnOne(tarf_name, output_prefix, cases_in, cases_out, dump_error = False):
    print("\texecute", tarf_name)



    run_res = []
    num_AC = 0
    num_RE = 0
    num_WA = 0
    if dump_error:
        all_res_f = open(run_all_res_name, 'w')
    for case_idx, (in_f, out_f) in enumerate(zip(cases_in, cases_out)):
        
        std_output_f = open(out_f, 'r')
        
        # run_output_f = open(run_output_name, 'w')
        if os.path.exists(run_error_name):
            os.remove(run_error_name)
        if os.path.exists(run_output_name):
            os.remove(run_output_name)

        run_error_f = open(run_error_name, 'w')
        run_cmds = ['"'+tarf_name+'"'+"<"+in_f+">"+run_output_name]
        MAX_VIRTUAL_MEMORY = 512 * 1024 * 1024 # 10 MB
        try:
            def limit_virtual_memory():
                resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, resource.RLIM_INFINITY))
            run_code = subprocess.call(run_cmds, timeout=3, stderr=run_error_f, shell=True, preexec_fn=limit_virtual_memory)
        except:
            run_code = -1
        run_error_f.close()
        # run_output_f.close()

        if run_code !=0:
            run_res.append(-1)
            num_RE+=1
            if dump_error:
                all_res_f.write(case_header % (case_idx, "RE"))
                append_input(all_res_f, in_f)
                all_res_f.write(" ".join(run_cmds)+"\n\n")
                run_error_f = open(run_error_name, 'r')
                run_error_lines = run_error_f.readlines()
                all_res_f.writelines(run_error_lines)
                all_res_f.write("\n\n\n")
                
                run_error_f.close()
            continue
        try:
            run_output_f = open(run_output_name, 'r')
            run_output = run_output_f.readlines()
        except:
            run_output_f = open(run_output_name, 'r', encoding="gbk")
            run_output = run_output_f.readlines()
        run_output = process_lines(run_output)
        std_output = std_output_f.readlines()
        std_output = process_lines(std_output)
        std_output_f.close()
        run_output_f.close()

        correct = True
        #move empty line at last
        
        
        if(len(run_output) != len(std_output)):
            correct = False
        else:
            for (std_l, run_l) in zip(std_output, run_output):
                if std_l != run_l:
                    correct = False
                    break
        if correct:
            run_res.append(0)
            num_AC+=1
        else:
            run_res.append(1)
            num_WA+=1
        
        if dump_error:
            all_res_f.write(case_header % (case_idx, "AC" if correct else "WA"))
            all_res_f.write(" ".join(run_cmds)+"\n")
            append_input(all_res_f, in_f)
            all_res_f.write("\n".join(run_output))
            all_res_f.write("\n\n\n")


    # if dump_error and  == false:
    if dump_error:
        all_res_f.write(format_header % (output_prefix.split("/")[-1], num_AC, num_RE, num_WA, len(cases_in)))
        all_res_f.close()
        shutil.copy(run_all_res_name, output_prefix + "_error")
    return run_res
        


def process_library(target_file):
    target_path = "/".join(target_file.split("/")[:-1])
    rel_path = os.path.relpath(zy_libs_path, target_path)
    try:
        c_file = open(target_file, 'r')
        lines = c_file.readlines()
    except:
        c_file = open(target_file, 'r', encoding="gbk")
        lines = c_file.readlines()
    for idx,line in enumerate(lines):
        if re_zylib.match(line):
            lines[idx] = f"#include \"{rel_path}/zylib.h\"\n"
            cur_c_libs[0] = library_o_file_names[0]
        elif re_zyrandom.match(line):
            lines[idx] = f"#include \"{rel_path}/zyrandom.h\"\n"
            cur_c_libs[1] = library_o_file_names[1]
        elif re_zydynarry.match(line):
            cur_c_libs[2] = library_o_file_names[2]
            lines[idx] = f"#include \"{rel_path}/dynarray.h\"\n"
        # lines[idx] = lines[idx].encode("UTF-8")
        elif "scanf_s" in line:
            line.replace("scanf_s", "scanf")
    with open(target_file[:-2]+"_.c", 'w', encoding="utf-8") as f:
        f.writelines(lines)
    return target_file[:-2]+"_.c"



def compile_file(librarys, headers, target_file, output_prefix):
    # get compile cmd
    print("    compile", target_file)
    cmd = ["gcc", "-g"]
    for idx,lib in enumerate(librarys):
        if lib != 0:
            # cmd += [os.path.relpath(lib, target_file)]
            cmd += [library_o_file_names[idx]]
    tmp_file = open(tmp_compile_name, 'w')
    # os.chdir(compile_path)
    tarf_name = target_file[:-2]
    cur_cmd =cmd + [target_file, "-o", tarf_name]

    try:
        return_code = subprocess.call(cur_cmd, stdout=tmp_file, stderr=tmp_file)
    except:
        return_code = 1
    
    if return_code != 0:
        tmp_file.write("\n\n\n###Compile cmd:\n" + " ".join(cur_cmd))
        tmp_file.close()
        shutil.copy(tmp_compile_name, output_prefix + "_compile_fail")
        return False
    tmp_file.close()
    return True



def extralFiles(zipf, force_extract = False):
    compres = None
    if zipf.endswith(".zip"):
        compres = zipfile.ZipFile(zipf)
        cur_path = zipf[:-4]
    elif zipf.endswith(".rar"):
        compres = rarfile.RarFile(zipf, mode='r')
        cur_path = zipf[:-4]
        
    elif zipf.endswith(".7z"):
        cur_path = zipf[:-3]
        compres = py7zr.SevenZipFile(zipf, mode='r')
        
    if compres is not None:
        if not os.path.isdir(cur_path) or force_extract:
            compres.extractall(cur_path)
            return cur_path
    return None

def judgeFolder(cur_path):
    print("procsss in", cur_path)
    for i in range(3):
        cur_c_libs[i] = 0
        cur_h_libs[i] = 0 
    #remove existing results
    for fpathe,dirs,fs in os.walk(cur_path):
        for f in fs:
            if f.endswith("_compile_fail") or f.endswith("_correct") or f.endswith("_error"):
                os.remove(os.path.join(fpathe, f))

    #process all file

    target_files = [ ]
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
    for fpathe,dirs,fs in os.walk(cur_path):
        for cur_f in fs:
            target_file_path = os.path.join(fpathe, cur_f)
            if is_binary_string(open(target_file_path, "rb").read(1024)):
                continue
            if cur_f.endswith(".cpp"):
                shutil.move(target_file_path, target_file_path[:-2])
                target_file_path = target_file_path[:-2]
                cur_f = cur_f[:-2]
            if cur_f.endswith(".c") and (target_file_path[:-2]+"_.c") not in target_files:
                if cur_f in library_header_file_names:
                    idx = library_header_file_names.index(cur_f)
                    cur_h_libs[idx] = target_file_path
                elif cur_f in library_c_file_names:
                    idx = library_c_file_names.index(cur_f)
                    cur_c_libs[idx] = target_file_path
                elif not cur_f.endswith("_.c"):
                    target_file_path = process_library(target_file_path)
                    target_files.append(target_file_path)
    
    ## process all c file
    target_files.sort()
    if len(target_files) > len(in_files):
        return
    for tar_idx, tarF in enumerate(target_files):
        # build one file    
        tarf_name = tarF[:-2]
        splits = tarf_name.split("/")
        output_prefix = os.path.join(cur_path, f"{tar_idx}_" + splits[-1])
        compile_res = compile_file(cur_c_libs, cur_h_libs, tarF, output_prefix)
        if compile_res is False:
            continue
        # flag = False
        # for pro_idx, (cases_in, cases_out) in enumerate(zip(in_files, out_files)):
        res = testOnOne(tarf_name, output_prefix, in_files[tar_idx], out_files[tar_idx], dump_error=True)
        if -1 not in res and 1 not in res:
            filename = output_prefix + "_correct"
            with open(filename, 'w') as f:
                f.write("success\n")
                f.close()



def processAll(targetFolder):
    if not os.path.isdir(targetFolder):
        print("target folder is not valid")
        exit(1)
    

    zipFiles = os.listdir(targetFolder)
    zipFiles.sort()
    
    for zipf in zipFiles:
        #unzip
        zipf = os.path.join(targetFolder, zipf)
        cur_path = extralFiles(zipf)
        if cur_path is None:
            continue

        judgeFolder(cur_path)
        


def processSingle(targetPath):
    if os.path.isdir(targetPath):
        pass
    elif os.path.isfile(targetPath) and targetPath[-3:] in ["rar", ".7z", "zip"]:
        targetPath = extralFiles(targetPath, force_extract=True)
    else:
        print("target folder is not valid")
        exit(1)
    if targetPath is not None:
        judgeFolder(targetPath)
        

if __name__ == "__main__":

    targetFolder = sys.argv[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", '-a', action="store_true", help="process all compression files")
    parser.add_argument("--section_path", "-s", required=False, type=str, help="target section path", default="")
    parser.add_argument("--project_path", "-p", required=False, type=str, help="target project path", default="")
    parser.add_argument("--test_cases", "-t", required=True, type=str, help="test cases path")
    parser.add_argument("--tmp_folder", required=False)
    args = parser.parse_args()
    if args.all:
        assert args.section_path != "", "please provide the target section path"
    else:
        assert args.project_path != "", "please provide the project section path"



    
    if not os.path.isdir('/tmp/judge'):
        os.mkdir('/tmp/judge')

    load_test_sample(args.test_cases)

    if args.all:
        processAll(args.section_path)
    else:
        processSingle(args.project_path)



