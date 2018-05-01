#!/bin/bash
#
# USAGE: ./create_db.sh <DATABASE> <USER>
#
# You will be prompted for your password
#

mysql -u $2 -h localhost -p -e "CREATE DATABASE $1;" && sed "s@AMON_DATABASE_NAME@$1@g" setup_amon_database.sql |  mysql -u $2 -h localhost -p $1
