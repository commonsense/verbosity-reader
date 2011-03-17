import psycopg2

fisle = open("verbosity.txt", 'w')

vdb = psycopg2.connect("dbname='verbosity' user='openmind' host='csc-sql.media.mit.edu' password='uataimec'")
cur = vdb.cursor()

cur.execute("SELECT * from relations")
verbosity = cur.fetchall()
for row in verbosity:  
    stuff =  [str(x) for x in row]
    aline = "\t".join(stuff)
    fisle.write(aline + '\n')
#    print aline
fisle.close()
