# This class is a wrapper to easily connect to Postgresql
import pgdb
import os
import ConfigParser

class Postgresql():

    def __init__(self):
        self.conn = None
        self.logger = None
        # Load database connection details
        config = ConfigParser.ConfigParser()
        config.read('/etc/scheduler.conf')
        self.hostname = config.get('connection', 'hostname', 'localhost')
        self.username = config.get('connection', 'username', 'postgres')
        self.password = config.get('connection', 'password', 'postgres')
        self.database = config.get('connection', 'database', 'odoo')

    def connect(self):
        try:
            # Connect to Postgresql database
            self.logger.info("Hostname="+self.hostname)
            self.logger.info("Username="+self.username)
            self.logger.info("Password="+self.password)
            self.logger.info("Database="+self.database)
            conn = pgdb.connect(host=self.hostname, user=self.username, password=self.password, database=self.database)
            self.conn = conn
        except:
            message = "Couldn't connect to Postgresql"
            self.logger.error(message)
            raise Exception(message)

    def query_scalar(self, query):
        result = self.query_one(query)
        value = result[0]
        return value

    def query_one(self, query):
        result = self.query_all(query)
        if not result:
            return None
        return result[0]

    def query_all(self, query):
        result = self.execute(query)
        records = result.fetchall()
        return records

    def insert(self, query):
        query += " RETURNING id"
        return self.query_scalar(query)

    def execute(self, query):
        cursor = self.conn.cursor()
        result = cursor.execute(query)
        self.conn.commit()
        return result
