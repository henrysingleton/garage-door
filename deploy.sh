#!/bin/bash

scp -r src/garage_door/. garagedoor:~/garage-door/src/garage_door/
scp -r static/. garagedoor:~/garage-door/static/
ssh garagedoor -t 'sudo systemctl restart garagedoor'