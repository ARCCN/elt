for file in `cat scripts/common.list`; do
    diff server/ext/debugger/elt/$file adapters/pox/ext/debugger/elt/$file;
done
