#!/bin/bash
sudo screen -ls | grep mininet | awk '{print $1}' | xargs -I{} sudo screen -S {} -X quit 
ps aux | grep python | grep -v grep | awk '{print $2}' | xargs -I{} sudo kill -9 {}
