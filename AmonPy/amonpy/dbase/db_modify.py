from __future__ import print_function
from builtins import input
import sys
import getpass
import MySQLdb

def connect():
	print("\n## Please setup your database connection\n")
	db = MySQLdb.connect(
		host = input("                                hostname: "),
		user = input("                                    user: "),
		passwd = getpass.getpass("                          enter password: "),
		db = input("                                      db: ")
		)
	return db.cursor()

def add_row(cur, table):
	print("\n## Please enter information to insert a row into %s\n" % table)
	cur.execute("describe %s;" % table)
	values = {}
	for row in cur.fetchall():
		values[row[0]] = input("%40s: " % ("%s (%s)" % (row[0], row[1])))
	cur.execute("INSERT INTO " + table + " (" + ",".join(list(values.keys())) + ") VALUES (" + ",".join("'%s'" % v for v in list(values.values())) + ")")
