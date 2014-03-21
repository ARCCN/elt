#!/bin/bash

for file in `ls graphs/*.dot`; do
    ./make_graph.sh $file;
done
