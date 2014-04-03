file='table_log.txt'
for i in no 0.0 0.1 0.5; do
    python log_to_table.py ../stress_test.log $i >> $file
    echo '' >> $file
done
