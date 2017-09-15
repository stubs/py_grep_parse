#!/usr/bin/env python
"""File assumptions: Script will assume that there is a static location where
data wishing to be searched will live.  User will have to hard enter said path
into line 13 of this script."""
import pdb
import csv
import os
import shlex
import sys
from subprocess import check_call, check_output

# TODO: FILL IN CUSTOM ROOT_FILE_DIR
ROOT_FILE_DIR = os.path.join("PATH", "TO", "ROOT DIR")
EXCLUDE_DIRS = sys.argv[1]
INCLUDES = sys.argv[2]
PATTERN = sys.argv[3]
GREP_WHERE = ROOT_FILE_DIR.replace("\\", r"/") + "/" + sys.argv[4]
RAW_GREP_FILE = sys.argv[5]
OUT_FILE, EXTENSION = os.path.splitext(RAW_GREP_FILE)
OUT_FILE += "_PARSED" + EXTENSION
SEPARATOR = [[]]


def call_grep(ex_dirs, incs, patterns, grep_locale=ROOT_FILE_DIR, output="grep_results.csv"):
    """Construct a subprocess egrep call with optional additional
    parameters.

    Keyword arguments:
        ex_dirs -- string pattern of directories to exclude from grep search.
        incs -- string regex pattern of file names to include in grep search. Should begin with alpha-numeric char.
                If more than one regex pattern should be quoted and wrapped in brackets "{}".
        patterns -- string regex pattern. Should be wrapped in quotation marks.
        grep_locale -- subdir of ROOT_FILE_DIR. (Default ROOT_FILE_DIR to search everything)
        output -- name of file to pipe grep results to. (Default "grep_results.csv")
    """
    try:
        command = 'grep -Enri --exclude-dir={0} --include={1} "{2}" "{3}"'.format(ex_dirs, incs, patterns, grep_locale)
        command_args = shlex.split(command)
        grep_out_file = open(output, "wb")
        check_call(command_args, stdout=grep_out_file)
        return True
    except Exception, e:
        print "ERROR PERFORMING GREP SEARCH: {}".format(e)
        return False


def grab_file_headers(in_file):
    """Construct a subprocess call to capture the first row of the input
    CSV file. Returns the captured line sans newlines and carriage returns as a
    python list.

    Keyword arguments:
        in_file -- path to file to pull header row from.
    """
    try:
        command = "head -1 '{}'".format(in_file)
        command_args = shlex.split(command)
        headers = check_output(command_args).replace("\r", "").replace("\n", "").split(",")
        print "Pulled headers for {}.".format(in_file)
        return headers
    except Exception, e:
        print "ERROR COLLECTING HEADER ROWS: {}".format(e)
        return False


def write_row_separators(sep_list):
    """Function takes a list of separators to separate different GREP results
    from each other for easier readability.


    Keyword arguments:
        sep_list -- List of items to separate different chunks of data.
    """
    try:
        for value in sep_list:
            writer.writerow(value)
        return True
    except Exception, e:
        print "ERROR SEPARATING ROWS: {}".format(e)
        return False


def write_file_headers(separators, in_file, first_row_mode=False):
    """Write the file headers pulled by grab_file_headers. Default
    value for first_row_mode dictates that there should be empty lines inserted
    before writing the file headers.

    Keyword arguments:
        separators -- List of times to separate different chunks of data.
        in_file -- Path to file to pull file headers from.
        first_row_mode -- If True, do not insert separators. (Default False)
    """
    try:
        if not first_row_mode:
            write_row_separators(separators)
        file_columns = grab_file_headers(in_file)
        writer.writerow(file_columns)
        return True
    except Exception, e:
        print "ERROR WRITING HEADERS: {}.".format(e)
        return False


if call_grep(EXCLUDE_DIRS, INCLUDES, PATTERN, GREP_WHERE, RAW_GREP_FILE):
    with open(RAW_GREP_FILE, "rU") as infile:
        reader = csv.reader(infile)

        with open(OUT_FILE, "wb") as output:
            writer = csv.writer(output)
            prev_client = ""
            prev_row_len = 0

            for row_num, row in enumerate(reader):
                try:
                    if row[0].find(":") != -1: # check to make sure true match in grep
                        print "PROCESSING ROW {}".format(row_num)
                        path_info, line_no, first_col = row[0].split(":")
                        if line_no != "1": # check to make sure there was no match on header row
                            path_info = path_info.strip().split("/")
                            try:
                                if path_info.index(".") == 0:
                                    path_info = path_info[1:]
                            except:
                                # TODO: replace "ROOT DIR" with actual root directory
                                if path_info.index("ROOT DIR"):
                                    path_info = path_info[path_info.index("ROOT DIR") + 1:]

                            client = path_info[0]
                            file_path = [ROOT_FILE_DIR] + path_info
                            file_path = os.path.join(*file_path)

                            if prev_client == client:
                                if prev_row_len == len(row):
                                    writer.writerow(row)
                                elif prev_row_len != len(row):
                                    write_file_headers(SEPARATOR, file_path)
                                    writer.writerow(row)
                            else:
                                # handle first row of the entire file
                                if row_num == 0:
                                    write_file_headers(SEPARATOR, file_path, True)
                                else:
                                    write_file_headers(SEPARATOR, file_path)
                                writer.writerow(row)

                            prev_client = client
                            prev_row_len = len(row)
                    else:
                        writer.writerow(row)  # still output possible error row
                except Exception, e:
                    print "ERROR WORKING WITH ROW NUMBER {}".format(row_num)
    print "\a"  # audible bell for testing
