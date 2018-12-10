#!/usr/bin/env python

import os
import glob
import argparse 
import subprocess as sub
import shlex 
from subprocess import PIPE, Popen
import pandas as pd
import logging
import re
import datetime
import sys



## This is how to create the bnum_tnum_df that we are interested in: 
def getting_bnum_tnum_list(bnum_tnum_csv): 
    ########### Get bnum_tnum list: 
    savedir = os.getcwd()
    os.chdir(csv_dir)
    bnum_tnum_df = pd.read_csv(bnum_tnum_csv, header = None)
    bnum_tnum_df.columns = ['bnum', 'tnum', 'DUMMY']
    os.chdir(savedir)
    return bnum_tnum_df


## This is a quick way to change to the tnum folder we're lookgng for depending on the root: 
def change_path(pathname_root):
    pathname = pathname_root+bnum+'/'+tnum
    os.chdir(pathname)

def get_nonlin_data():
    os.chdir(recgli_path_root+"/"+bnum+"/"+tnum+'/perf_biopsy')
    nonlin_curve_files = glob.glob('*ave_curve_nonlin*')
    nonlin_curve_df = pd.DataFrame()
    for nonlin_curve_file in nonlin_curve_files: 
        nonlin_curve_data = pd.read_table(nonlin_curve_file, header = None)
        ## we want to extract the exact vial ID as well as the nonlin 
        ## data of interest. 
        vial_name = nonlin_curve_file.split('_')[1]
        nonlin_curve_data = nonlin_curve_data.transpose()
        nonlin_curve_data.columns = nonlin_curve_data.iloc[0]    
        ## ok now we want to create a dataframe from this data that has vialID info and the rest of the information: 
        nonlin_data_vial = {'bnum': bnum, 
                            'tnum': tnum, 
                            'vialid': vial_name, 
                            'phn_nlin': nonlin_curve_data['phn '][1], 
                            'cbvn_nlin': nonlin_curve_data['cbvn '][1], 
                            'recov_nlin': nonlin_curve_data['recov '][1]}
        nonlin_curve_df = nonlin_curve_df.append(nonlin_data_vial, ignore_index = True)
    return nonlin_curve_df

def get_nonpar_data():
    os.chdir(recgli_path_root+"/"+bnum+"/"+tnum+'/perf_biopsy')
    nonpar_curve_files = glob.glob('*ave_curve_nonparam*')
    nonpar_curve_df = pd.DataFrame()
    for nonpar_curve_file in nonpar_curve_files: 
        nonpar_curve_data = pd.read_table(nonpar_curve_file, header = None)
        ## we want to extract the exact vial ID as well as the nonpar 
        ## data of interest. 
        vial_name = nonpar_curve_file.split('_')[1]
        nonpar_curve_data = nonpar_curve_data.transpose()
        nonpar_curve_data.columns = nonpar_curve_data.iloc[0]    
        ## ok now we want to create a dataframe from this data that has vialID info and the rest of the information: 
        nonpar_data_vial = {'bnum': bnum, 
                            'tnum': tnum, 
                            'vialid': vial_name, 
                            'phn_npar': nonpar_curve_data['phn '][1],  
                            'recov_npar': nonpar_curve_data['recov '][1], 
                            'recovn_npar': nonpar_curve_data['recovn '][1] 
                           }
        nonpar_curve_df = nonpar_curve_df.append(nonpar_data_vial, ignore_index = True)
    return nonpar_curve_df

if __name__ == '__main__':

    #####################################
    # EXAMPLE: get_perf_biopsy_data.dev.py --csv_name /home/sf6735452/DataWrangling/GetMergeData/Oct2018/ajnr_
    #            --cohort_name REC_HGG
    #            --output_file REC_HGG_perf_biopsies.csv --output_dir ./
    #####################################

    parser = argparse.ArgumentParser(description='Create a systematic logger of whether biopsies are valid or not through visual inspection')
    parser.add_argument("--csv_name",        required=True,    help='Precise name of the csv file that contains the perfusion files of interest.')
    parser.add_argument("--csv_dir",         required=True,    help='Precise path of the csv file that contains the perfusion files of interest.')
    parser.add_argument("--cohort_name",     required=True,    help='Precise cohort name of the scans of interest (e.g. "po1_preop_recur" or "REC_HGG")')
    parser.add_argument("--output_file",     required=False,   help="Name of the output file csv", default = "perf_valid_file.csv")
    parser.add_argument("--output_dir",      required=True,    help="Path where output files get written ")
    parser.add_argument("-v", "--verbose",                     help = "verbose output", action='store_true', default=False,   required=False)

    args = parser.parse_args()
    #####################################
    #   Create strings of the arguments for 
    #   navigating to correct directory
    #####################################
    cohort_name     = args.cohort_name
    csv_name        = args.csv_name
    csv_dir         = args.csv_dir
    output_file     = args.output_file
    output_dir      = args.output_dir

    print("===============================================")
    print("scan list dir:     ", csv_dir)
    print("scan list name:    ", csv_name)
    print("cohort name:       ", cohort_name) 
    print("output file name:  ", output_file) 
    print("output dir:        ", output_dir)
    print("===============================================")

    #   Write cmd to Logfile 
    cmd_string = ' '.join(sys.argv)
    with open("Logfile", "a") as logfile:
        logfile.write( cmd_string )
        logfile.write( '\n' )

    #####################################
    #   Reading in the csv_name
    #   as the scan listls
    #####################################

    bnum_tnum_df = getting_bnum_tnum_list(csv_name)

    #####################################
    #   Setting the roots of the data 
    #   based on the cohort name
    #####################################

    if cohort_name == 'po1_preop_recur': 
        recgli_path_root = '/data/RECglioma/archived/'
    elif cohort_name == 'REC_HGG': 
        recgli_path_root = '/data/RECglioma/'
    else: 
        print('Please use a valid cohort name, REC_HGG or po1_preop_recur.')
        exit(1)


    #####################################
    #   Instantiate the nonlinear and nonpar DFs
    #####################################

    nonlin_total_df = pd.DataFrame()
    nonpar_total_df = pd.DataFrame()
    error_log = pd.DataFrame()

    #####################################
    #   Iterating through scans, grabbing the data of interest: 
    #####################################

    for index, row in bnum_tnum_df.iterrows():
        bnum = row['bnum']
        tnum = row['tnum']
        error_log_line = {'bnum': bnum, 'tnum': tnum}

        print(bnum)
        print(tnum)

        #####################################
        #   Change into the correct directory
        #####################################
        os.chdir(recgli_path_root+"/"+bnum+"/"+tnum)

        #####################################
        #   Gather the vialIDs 
        #####################################
        tnum_dirs = os.listdir()
        if "roi_analysis" in tnum_dirs: 
            os.chdir('roi_analysis')
            vial_files = glob.glob('*_t1ca_*.idf')
        else: 
            vial_files = []
            error_log_line['biopsies']='error'

        #####################################
        #   Change back into the correct directory
        #####################################
        os.chdir(recgli_path_root+"/"+bnum+"/"+tnum)

        #####################################
        #   Gather the data if available: 
        #####################################

        ## If there exists a perf_biopsy folder: 
        if len(glob.glob('perf_biopsy'))>0: 
            print("------------------------------------------")
            print('perf_biopsy folder found')
            print('There should be '+str(len(vial_files))+' biopsies for this scan.')
            print('------------------------------------------')
            
            ## Set the perf_biopsy_status to 1 so that we know that it exists
            perf_biopsy_status = 1
            
            ## If there exists biopsy masks in roi_analysis: 
            if len(vial_files)>0: 
                print('-------------------------------')
                print('vialIDs found in roi_analysis')
                print('-------------------------------')

                ## Set the vial_file_status = 1 so that we know they exist 
                vial_files_status = 1

                ## Instanstiate the nonlin_curve_df and nonpar_curve_df dataframes
                nonlin_curve_df = pd.DataFrame()
                nonpar_curve_df = pd.DataFrame()
                
                ## Get the nonlin_curve_df for this bnum/tnum
                nonlin_data = get_nonlin_data()
                nonpar_data = get_nonpar_data()

                ## Add these data to the overall dataFrame: 
                nonlin_total_df = nonlin_total_df.append(nonlin_data, ignore_index= True)
                nonpar_total_df = nonpar_total_df.append(nonpar_data, ignore_index= True)

            else: 
                print('----------------------------')
                print('ERROR! No vial IDs found! No biopsies or run biopsy_make_masks')
                print('----------------------------')
                
                ## Set the vial_file_status = 1 so that we know they exist 
                vial_files_status = 0
                error_log_line['biopsies']='error' 

        else: 
            print("------------------------------------------")
            print('No perf_biopsy folder found!! Run perf_biopsy.')
            print('------------------------------------------')

            perf_biopsy_status = 1 
            error_log_line['perf_biopsy_folder']='error' 

        error_log = error_log.append(error_log_line, ignore_index = True)

nonlin_total_df.index = nonlin_total_df['vialid']
nonpar_total_df.index = nonpar_total_df['vialid']
total_df = nonlin_total_df.join(nonpar_total_df, lsuffix = "_npar")
cols = ['bnum', 'tnum', 'vialid', 'phn_nlin', 'cbvn_nlin', 'recov_nlin', 
                   'phn_npar', 'recov_npar', 'recovn_npar']
total_df = total_df[cols]
total_df = total_df.reset_index(drop = True)
out_file = output_dir+output_file
total_df.to_csv(out_file, index = False)
log_out_file = output_dir+cohort_name+'_perf_error_log.csv'
error_log.to_csv(log_out_file)
