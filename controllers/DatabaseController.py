import sqlite3
from datetime import datetime

class InventoryRepository:
	db_cursor = None
	def __init__(self):
		conn = sqlite3.connect('inventory_thesis.db')
		self.db_cursor = conn.cursor()        
	# SELECT borrowed-returned tables
	def select_br(self, itemName=None, date=None, dateB=None, camera=None, nametable=None):
		if nametable is None:
			return "Please specify tablename"
		nt_alias = None
		if nametable == "borrowed":
			nt_alias = "b"
		elif nametable=="returned":
			nt_alias = "r"
		db_cursor = self.db_cursor
		query = "SELECT i.item_name, datetime, %s.idInventory, camera FROM %s AS %s LEFT JOIN inventory AS i ON %s.idInventory = i.idInventory WHERE " 
		attributes = []
		attributes.append(nt_alias)
		attributes.append(nametable)
		attributes.append(nt_alias)
		attributes.append(nt_alias)
		if date is not None:
			query += "datetime >= '%s' AND "
			attributes.append(date)
		if dateB is not None:
			query += "datetime <= '%s' AND "
			attributes.append(dateB)
		if itemName is not None:
			query += "i.item_name = '%s' AND "
			attributes.append(itemName)
		if camera is not None:
			query += "camera = %s AND "
			attributes.append(camera)        
		if query.split()[-1] == "WHERE":
			print(query.rsplit('WHERE', 1)[0])
			query = query.rsplit('WHERE', 1)[0]
		elif query.split()[-1] == "AND":
			query = query.rsplit('AND', 1)[0]               
		attributes = tuple(attributes)
		query = query % attributes
		# print(query)
		db_cursor.execute(query)
		results = db_cursor.fetchall()
		return results
	def select_in():
		# SELECT i.item_name, i.item_description, s.totalStockIn, 
		# DO SOME CALCULATION REGARDING HOW TO STORE DATA
		# SAY, IF ONLY CAMERA 1 DETECTS IN, BUT CAMERA 2 DOESN'T FOR 2 SECONDS, ALERT
		# APP TO GO AND SCAN ITEM AGAIN
		test = None