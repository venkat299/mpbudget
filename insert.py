# script.py
import argparse
import pyexcel as pe
import configparser 
import os
import sys
import sqlite3
import my_connection as connection

DB_URL = None
global conn
conn = None
sheet = None

desg_ls=None
unit_ls=None
sect_ls=None

def load_tables():
	# conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute("select dscd from desg")
	global desg_ls
	desg_ls = [ x[0] for x in c.fetchall()]

	c.execute("select code from unit")
	global unit_ls
	unit_ls = [ x[0] for x in c.fetchall()]

	c.execute("select code from section")
	global sect_ls
	sect_ls = [ x[0] for x in c.fetchall()]

	c.execute("select eis from employee")
	global eis_ls
	eis_ls = [ x[0] for x in c.fetchall()]

eis_list = []

def validate_row(row):
	err = []
	if row['DSCD'] not in desg_ls:
		err.append(" dscd("+row['DSCD']+")")
	if row['SECTION_CD'] not in sect_ls:
		err.append(" sect("+row['SECTION_CD']+")")
	if row['WORKING UNIT'] not in unit_ls:
		err.append(" unit("+row['WORKING UNIT']+")")
	if row['ONROLL_UNIT'] not in unit_ls:
		err.append(" roll_unit("+row['ONROLL_UNIT']+")")

	global eis_list

	if row['EIS'] in eis_list:
		err.append(" eis_repeat("+str(row['EIS'])+")")
	else:
		eis_list.append(row['EIS'])

	try:
		if int(row['EIS']) in eis_ls:
			err.append(" eis_dup_db("+str(row['EIS'])+")")
	except ValueError as e:
		err.append(" eis_err("+str(row['EIS'])+")")
		
	if not err:
		return None
	else:
		return err

def read_file(xls_path, sheet_name, upload):
	# book = pe.get_book(file_name=os.path.normpath(xls_path))
	# sheets = book.to_dict()
	# for name in sheets.keys():
	# 	print(name)

	try:
		sheet = pe.get_sheet(file_name=os.path.normpath(xls_path), sheet_name=sheet_name, name_columns_by_row=0)

	except ValueError as e:
		print("Sheet name not in excel file: {0}".format(e))
		sys.exit()
	except AttributeError as e:
		print("Sheet name not in excel file: {0}".format(e))
		sys.exit()
		#raise e
	except NotImplementedError as e:
		print("File not found or File not in proper format: {0}".format(e))
		sys.exit()
		#raise e

	records = sheet.get_records()
	error_ls = []

	for idx, record in enumerate(records):
		err_row = validate_row(record)

		if err_row:
			error_ls.append(err_row)
			print('ERR @ ROW {} => {}'.format(idx+2,validate_row(record)))
	if error_ls:
		print('correct the above error and upload')
	else:
		print('{0} rows will be inserted. add "-u" to upload'.format(len(records)))
		if upload:
			ls=[]
			for idx, r in enumerate(records):
				#sno	AREA	UNIT	MINE_TYPE	ONROLL_UNIT	WORKING UNIT	SECTION_TYPE	CADRE	SECTION	SECTION_CD	DESIG	DSCD	EIS	NAME	GENDER	DOB	Comments
				ls.append(('N','W',None,r['SECTION_CD'],r['WORKING UNIT'],r['ONROLL_UNIT'],r['DESIG'],r['GENDER'],r['DOB'],r['NAME'],r['EIS'],r['Comments']))
			c = conn.cursor()
			c.executemany('''insert into employee (emp_type,working,o_dcd,sect,ucde,roll_ucde,desg,gend,dob,name,eis,comments)
				values(?,?,?,?,?,  ?,?,?,?,?, ?,?)''',ls)
			conn.commit()
			print('--->{0} records inserted sucessfully'.format(len(ls)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     'filename', metavar='int', type=int, choices=range(10),
    #      nargs='+', help='give a file name')
    parser.add_argument('filename',  help='give file name')
    parser.add_argument('table',  help='e for inserting employee; s for inserting sanction')
    parser.add_argument("-sh",'--sheetname',  help='give sheet name; type * to include all sheets')
    parser.add_argument("-u", "--upload", action="store_true", help="to update/commit changes into database")

    args = parser.parse_args()
    print(args)
    #read_config()
    conn = connection.get_connection()

    if args.table == 'e':
        load_tables()
        read_file(args.filename, args.sheetname, args.upload)
    else:
    	print('supplied argument  or order of argument is wrong')
    	sys.exit()

  