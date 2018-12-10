#!/bin/csh -f

set dir = $1
set suffix = $2
set tnum = `pwd | cut -d"/" -f5`

if (-d $dir) then
    echo "folder $dir exists, changing into directory"
    cd $dir
    echo "changed into $dir directory"

    ## here we are going to count the number of .tab files 
    @ tabnum = `ls *{$suffix} | wc -l`
    echo $tabnum
    ## here we are initializing a new variable 
    @ k = 1
    ## here I am creating a file called tablist.txt that indexes the .tab files 
    ls *$suffix > tablist.txt

    while ($k <= $tabnum)
        set tablist_k = `awk 'NR=='$k'' tablist.txt | cut -d"." -f1`
        tab_to_csv -r $tablist_k
        echo "tab_to_csv $k completed"
        mv summary.csv ${tablist_k}.csv
        echo "summary file $k renamed"
        @ k = $k + 1
    end

else
    echo "no $dir folder, will skip"

endif

