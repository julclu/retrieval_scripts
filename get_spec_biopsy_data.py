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

def getting_bnum_tnum_list(bnum_tnum_csv): 
    ########### Get bnum_tnum list: 
    savedir = os.getcwd()
    os.chdir(csv_dir)
    bnum_tnum_df = pd.read_csv(bnum_tnum_csv, header = None)
    bnum_tnum_df.columns = ['bnum', 'tnum', 'DUMMY']
    os.chdir(savedir)
    return bnum_tnum_df

def get_spec_data(measure = "median"):
    os.chdir(recgli_path_root+"/"+bnum+"/"+tnum)
    if len(glob.glob('svk_roi_analysis/*empcsahl_normxs_sinc.csv'))>0:
        ## read in data
        spec_data_file = pd.read_csv(glob.glob('svk_roi_analysis/*empcsahl_normxs_sinc.csv')[0])
        if len(vial_files)>0: 
            ## shorten vial names
            vial_names = [vial.replace(".", "_").split("_")[2] for vial in vial_files]
            ## shorten the spectroscopic data down to only the biopsies of interest: 
            spec_data_biopsy_file = spec_data_file[spec_data_file['roi-label'].isin(vial_names)]
            ## find only the measure of interest: 
            spec_data_biopsy_file_measure = spec_data_biopsy_file[spec_data_biopsy_file['measure']==measure]
        else: 
            vial_names = []
            print("ERROR! No biopsies.")
    else: 
        print('ERROR! No spectroscopic data present.')
    return spec_data_biopsy_file_measure


if __name__ == '__main__':

    #####################################
    # EXAMPLE: get_spec_biopsy_data.py --csv_name /home/sf6735452/DataWrangling/GetMergeData/Oct2018/ajnr_
    #            --cohort_name REC_HGG
    #            --output_file REC_HGG_perf_biopsies.csv --output_dir ./
    #####################################

    parser = argparse.ArgumentParser(description='Create a systematic logger of whether biopsies are valid or not through visual inspection')
    parser.add_argument("--csv_name",        required=True,    help='Precise name of the csv file that contains the perfusion files of interest.')
    parser.add_argument("--csv_dir",         required=True,    help='Precise path of the csv file that contains the perfusion files of interest.')
    parser.add_argument("--cohort_name",     required=True,    help='Precise cohort name of the scans of interest (e.g. "po1_preop_recur" or "REC_HGG")')
    parser.add_argument("--output_file",     required=True,    help="Name of the output file csv")
    parser.add_argument("--output_dir",      required=True,    help="Path where output files get written ")
    parser.add_argument("--measure",         required=False,   help='Measurement that you desire for the spectroscopic imaging (e.g. median, mean, max, etc.)', default = "median")
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
    measure         = args.measure

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
    #   Instantiate the total spectroscopic dataframe
    #####################################

    spec_total_df = pd.DataFrame()
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
        if "roi_analysis" in os.listdir(): 
            os.chdir('roi_analysis')
            vial_files = glob.glob('*_t1ca_*.idf')
        else: 
            vial_files = []
            print('ERROR! No biopsies.')
            error_log_line['biopsies']='error'
        #####################################
        #   Change back into the correct directory
        #####################################
        os.chdir(recgli_path_root+"/"+bnum+"/"+tnum)

        #####################################
        #   Gather the data if available: 
        #####################################

        ## If there exists an spectroscopic data file: 
        if len(glob.glob('svk_roi_analysis/*empcsahl_normxs_sinc.csv'))>0: 
            print('Spectroscopic csv file found')         
            ## If there exists biopsy masks in roi_analysis: 
            if len(vial_files)>0: 
                print('vialIDs found in roi_analysis')
                ## Set the vial_file_status = 1 so that we know they exist 
                vial_files_status = 1

                ## Instanstiate the tnum_spec_df
                tnum_spec_df  = pd.DataFrame()
                
                ## Get the data: 
                tnum_spec_df = get_spec_data()

                ## Add these data to the overall dataFrame: 
                spec_total_df = spec_total_df.append(tnum_spec_df, ignore_index= True)
            else:
                print('No vial IDs found! No biopsies.')

        else: 
            print("------------------------------------------")
            print('No height sinc.csv file! run sarahs processing scripts!')
            print('------------------------------------------')
            error_log_line['data_sinc_file']='error' 

        error_log = error_log.append(error_log_line, ignore_index = True)
    #####################################
    #   Rearrange the data: 
    #####################################
    
    cols = ['t-num', 'roi-label', 'cni', 'ccri', 'crni', 'ncho', 'ncre', 'nnaa', 'nlac', 'nlip']
    spec_total_df = spec_total_df[cols]
    spec_total_df.columns = ['tnum', 'roi.label', 'cni', 'ccri', 'crni', 'ncho', 'ncre', 'nnaa', 'nlac', 'nlip' ]
    out_file = output_dir+output_file
    spec_total_df.to_csv(out_file, index=False)
    log_out_file = output_dir+cohort_name+'_spec_error_log.csv'
    error_log.to_csv(log_out_file)
