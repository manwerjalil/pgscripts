#!/usr/bin/python3
############################### HAtester.py #####################################
#     Version 2.2    Muhammad Anwar, Tech Support Pakistan (2012-2022)
#
# Program to test reads and writes in a PostgreSQL HA Cluster, including
# connection retry on connection failure to test load-balancing capabilities
# using HAProxy as a load balancer.

# PREREQUISITES
# 1) PostgreSQL Python connector python3-psycopg2
#
# sudo apt install -y postgresql-client python3-psycopg2
#
# 2) Target table HATEST must have been created in advance:
#
# psql -h your_db_server -p 5432 -U postgres -c "CREATE TABLE HATEST (TM TIMESTAMP);"
# psql -h your_bd_server -p 5432 -U postgres -c "CREATE UNIQUE INDEX idx_hatext ON hatest (tm desc);"
#
# 3) Monitor replication using:
#
# psql -h your_db_server -p 5432 -c "SELECT tm FROM hatest ORDER BY tm DESC LIMIT 1;"

import sys

# CONNECTION DETAILS
host = "your_db_server_name_or_ip"
dbname = "postgres"
user = "postgres"
password = "replace_with_postgres_password"
connect_timeout = 5
# Port number can be optionally provided as first argument
if len(sys.argv)>1 and int(sys.argv[1]):
  port = int(sys.argv[1])
else:
  port = 5432

# Connection string
connectionString = "host=%s port=%i dbname=%s user=%s password=%s connect_timeout=%i" % (host, port, dbname, user, password, connect_timeout)

# Execute Insert statement against table if doDML is true.
# create a table in advance: 
doDML = True

# USAGE 
#
# - Execution for writes:
#    ./HAtester.py 5000
#
# - Execution for reads:
#    ./HAtester.py 5001
#
# - Reconnection:
#    Ctrl+C will trigger a new connection to test load balancing.
#
# - Stop execution:
#    Ctrl+Z to pause the job, then terminate it with: kill %<job_id>
#
###############################################################################

import sys,time,psycopg2
def create_conn():
   try:
      conn = psycopg2.connect(connectionString)
   except psycopg2.Error as e:
      print("Unable to connect to database :")
      print(e)
      sys.exit(1)
   return conn

if __name__ == "__main__":
   conn = create_conn()
   if conn is not None:
      cur = conn.cursor()
      while True:
         try:
            time.sleep(1)
            if conn is not None:
               cur = conn.cursor()
            else:
               raise Exception("Connection not ready")
            #Check connected to master or Slave
            cur.execute("select pg_is_in_recovery(),inet_server_addr()")
            rows = cur.fetchone()
            if (rows[0] == False):
               print (" Working with:   MASTER - %s" % rows[1]),
               if doDML:
                  cur.execute("INSERT INTO HATEST VALUES(CURRENT_TIMESTAMP) RETURNING TM")
                  if cur.rowcount == 1 :
                     conn.commit()
                     tmrow = str(cur.fetchone()[0])
                     print ('     Inserted: %s\n' % tmrow)
               else:
                  print ("No Attempt to insert data")
            else:
               print (" Working with:    REPLICA - %s" % rows[1]),
               if doDML:
                  cur.execute("SELECT MAX(TM) FROM HATEST")
                  row = cur.fetchone()
                  print ("     Retrived: %s\n" % str(row[0]))
               else:
                  print ("No Attempt to retrive data")

         except:
            print ("Trying to connect")
            if conn is not None:
               conn.close()
            conn = create_conn()
            if conn is not None:
                 cur = conn.cursor()

   conn.close()
