for file in `cat scripts/common.list`; do
    echo $file
    diff server/ext/debugger/elt/$file adapters/pox/ext/debugger/elt/$file;
done
