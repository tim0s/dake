import os
import re
import shutil
import argparse
import subprocess
import Levenshtein

class DaCeReducer:
    
    def __init__(self, infile, outfile, threshold, pattern):
        self.infile = infile
        self.outfile = outfile
        self.threshold = threshold
        self.pattern = pattern
        self.shortest = self.infile
        self.workdir = "."
        self.versions_tested = 0
        self.last_stdout, self.last_stderr = self.run_and_capture(self.infile)
    
    def run_and_capture(self, infile, timeout=5):
        # call input file, capture stdout and stderr, save in last
        outs = ""
        errs = ""
        proc = subprocess.Popen(["python3", infile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
        return outs, errs
    

    def get_sloc(self, fname):
        """Find the number of SLOC in a file, assume everything is code except lines starting with a # mark"""
        with open(fname) as f:
            lines = f.readlines()
            counter = 0
            for line in lines:
                if re.match("#", line):
                    continue
                else:
                    counter += 1
            return counter


    def comment_out_sloc(self, n, fname):
        """Comment out the n-th SLOC in a file, assume everything is code except lines starting with a # mark"""
        lines = None
        with open(fname, "r") as f:
            lines = f.readlines()
            sloc_counter = 0
            lines_counter = 0
            for line in lines:
                if re.match("#", line):
                    lines_counter += 1
                else:
                    sloc_counter += 1
                    if sloc_counter == n:
                        lines[lines_counter] = "#" + lines[lines_counter]
                    lines_counter += 1
        with open(fname, "w") as f:
            f.writelines(lines)

    def compare_to_last(self, outs, errs):
        if (self.pattern is not None) and (self.pattern != ""):
            if re.match(self.pattern, outs) or re.match(self.pattern, errs):
                return True
        else:
            s1 = self.last_stdout + self.last_stderr
            s2 = outs + errs
            if self.threshold >= (Levenshtein.ratio(s1, s2) * 100):
                return True
        return False
            



    def reduce(self):
        # create a copy of the shortest existing version
        newfile = self.workdir + "/ver_" + str(self.versions_tested) + ".py"
        shutil.copy(self.shortest, newfile)

        # comment out a random line in the copy
        for line in range(1, self.get_sloc(newfile)):
            self.comment_out_sloc(line, newfile)
            # run copy and compare to last if equal add to version
            outs, errs = self.run_and_capture(newfile)
            if self.compare_to_last(outs, errs):
                # equivalent save new version
                if self.shortest != self.infile:
                    os.remove(self.shortest)
                self.shortest = newfile
            else:
                # not equivalent, delete newfile
                os.remove(newfile)
        # copy shortest version to outfile
        shutil.copy(self.outfile, self.shortest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                prog='DaCeTestReducer',
                description='Try to simplify DaCe Tests without changing their behaviour')
    parser.add_argument('-i', '--infile', help="Python file to reduce")
    parser.add_argument('-o', '--outfile', help="Reduced output file")
    parser.add_argument('-t', '--threshold', default=90, help='String edit distance in percent of output lenght to consider output equivalent.')
    parser.add_argument('-p', '--pattern', default=None, help='String pattern the output needs to match to be considered equivalent. Threshold is ignored if this is given.')
    args = vars(parser.parse_args())

    reducer = DaCeReducer(args['infile'], args['outfile'], args['threshold'], args['pattern'])
    reducer.reduce()


# comment out a random line in a copy of infile
# call copy, capture stdout and stderr
# determine  edit distance to last


