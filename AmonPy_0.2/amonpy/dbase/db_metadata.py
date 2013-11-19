#!/usr/bin/env python

import MySQLdb as mdb
import sys
import MySQLdb
"""@package db_metadata
This module access various metadata of a given database (e.g. table names,
column names, column types, column comments etc.).
Under development. 
"""


#host = sys.argv[1] 
#user = sys.argv[2] 
#passwd = sys.argv[3]
#db = sys.argv[4]

#try:
#    con = mdb.connect(host, user, passwd)
#    cur = con.cursor()
#    statement = "USE %s" %(db)
#    cur.execute(statement)
   
#except mdb.Error, e:
#    print """There was a problem in accessing the database %s. The error is
#     below.\n\n%s""" %(db, e)

#con = mdb.connect(host_name, user_name, passw_name, db_name)    
#cur = con.cursor()

class DBMetadata:
    def __init__(self):
        """A class for DB metadata"""
        self.database = []
   
    def general_query(self, cur, statement):
        "General executions of a input statement"
        try:
           runit = cur.execute(statement)
           results = cur.fetchall()
        except mdb.Error, e:
            results = "The query failed: %s" %(e)
        return results

    def tables(self, cursor):
        "Returns a list of tables in DB"
        statement = "SHOW TABLES"
        header = ("Tables")
        results = self.general_query(cursor, statement)
        return header, results
        
    def table_describe(self, tablename, cursor):
        "Returns the column info from a given table"
        header = ("Field", "Type", "Null", " Key", "Default", "Extra")
        statement = "SHOW COLUMNS FROM %s" %(tablename)
        results = self.general_query(cursor,statement)
        return header, results  
        
    def table_status(self, cursor):
         "Returns the results of table status"
         header = ("Name", "Engine", "Version", "Row_format", "Rows", "Avg_row_length", 
         "Data_length", "Max_data_length", "Index_length", "Data_free", "Auto_increment",
         "Create_time", "Update_time", "Check_time", "Collation", "Checksum", 
         "Create_options", "Comment")
         statement = "SHOW TABLE STATUS"
         results = self.general_query(cursor, statement)
         return header, results 
         
def resproc(finput):
    "Compiles the headers and results into a report"
    header = finput[0]
    results = finput[1]
    output = {}
    c = 0
    for r in xrange(0, len(results)):
        record = results[r]
        outrecord = {}
        for column in xrange(0, len(header)):
            outrecord[header[column]] = record[column]
        output[str(c)] = outrecord
        c += 1  
    orecord = ""
    
    for record in xrange(0, len(results)):
        record = str(record)
        item = output[record]
    for k in header:
        outline = "%s : %s\n" %(k, item[k])
        orecord = orecord + outline
        orecord = orecord + '\n\n'
    return orecord 
               
def main():
    host = sys.argv[1] 
    user = sys.argv[2] 
    passwd = sys.argv[3] 
    db = sys.argv[4]
    
    try:
        con = mdb.connect(host, user, passwd)
        cur = con.cursor()
        statement = "USE %s" %(db)
        cur.execute(statement)
    except mdb.Error, e:
        print """There was a problem in accessing the database %s.\ 
                 The error is printed below.\n\n%s""" %(db, e)


    mydb = DBMetadata()             
    print mydb.tables(cur)
    print mydb.table_status(cur)
    for i in mydb.tables(cur)[1]:
        print
        print mydb.table_describe(i, cur)
        
    tables = mydb.tables(cur)
    print
    print "TABLES OF %s:" %(db)
    print
    for c in xrange(0, len(tables[1])):
        print tables[1][c][0]
        print '\n\n' 
    tablestats = mydb.table_status(cur)
    print
    print "TABLE STATUS:"
    print
    print resproc(tablestats)
    print '\n\n' 
    r=mydb.table_describe('event', cur) 
    print r[1][0][0] 
      
if __name__ == '__main__':
    main()          