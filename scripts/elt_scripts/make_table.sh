file='table_log.txt'
for i in no proxy 0.0 0.01 0.1 0.5; do
    python log_to_data.py $1 $i >> $file
    echo '' >> $file
done

python data_to_table.py $file >> table.txt
