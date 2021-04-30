from datetime import datetime
import mysql.connector

class InventoryRepository:
    def initialize(self):
        db = mysql.connector.connect(
            host = "localhost",
            user ="admin",
            passwd = "admin",
            database="inventory_thesis")
        db_cursor = db.cursor()
        return db,db_cursor
    def select(self, idInventory=None, date=None, dateB=None, camera=None, nametable=None):
        if nametable is None:
            return "Please specify tablename"
        (db, db_cursor) = self.initialize()
        query = "SELECT * FROM %s WHERE " 
        attributes = []
        attributes.append(nametable)
        if date is not None:
            query += "datetime >= '%s' AND "
            attributes.append(date)
        if dateB is not None:
            query += "datetime <= '%s' AND "
            attributes.append(dateB)
        if idInventory is not None:
            query += "idInventory = %s AND "
            attributes.append(idInventory)
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
        print(query)
        db_cursor.execute(query)
        results = db_cursor.fetchall()
        db.close()
        # return results
    def insert(self, idInventory=None, date=None, camera=None,nametable=None):
        results = None
        if idInventory is None or date is None or camera is None or nametable is None:
            # return "Error. Please input the id of equipment, date, camera and tablename"
            results = ("Error. Please input the id of equipment, date, camera and tablename", False)
            return results
        (db, db_cursor) = self.initialize()

        query = "INSERT INTO %s (idInventory, datetime, camera) VALUES(%s,'%s',%s)" % (nametable, idInventory, date, camera)
        db_cursor.execute(query)
        db.commit()
        querySelect = "SELECT * FROM %s" % (nametable)
        db_cursor.execute(querySelect)
        results = (db_cursor.fetchall(), True)
        db.close()
        return results
    def update(self,idupdate=None,nametable=None, idInventory=None, date=None, camera=None):
        results = None
        if nametable is None or idupdate is None:
            results = ("Error. Please input tablename and row id needed to be updated",False)
            return results
        if idInventory is None and date is None and camera is None:
            results = ("Please don't call this function if you don't have anything to update",False)
        (db, db_cursor) = self.initialize()
        query = "UPDATE %s SET "
        attributes = []
        idColumnName = None
        attributes.append(nametable)
        if nametable == "borrowed":
            idColumnName = "idborrowed"
        elif nametable == "returned":
            idColumnName = "idreturned"
        if date is not None:
            query += "datetime = '%s', "
            attributes.append(date)
        if idInventory is not None:
            query += "idInventory = %s, "
            attributes.append(idInventory)
        if camera is not None:
            query += "camera = %s, "
            attributes.append(camera)
        query = query.rstrip((', '))      
        query +=" WHERE %s = %s"
        attributes.append(idColumnName)
        attributes.append(idupdate)
        attributes = tuple(attributes)
        query = query % attributes
        print(query)
        db_cursor.execute(query)
        db.commit()
        querySelect = "SELECT * FROM %s" % (nametable)
        db_cursor.execute(querySelect)
        results = (db_cursor.fetchall(),True)
        db.close()
        return results
