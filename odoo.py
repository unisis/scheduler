# This class is a wrapper to easily connect to Odoo
import os
import erppeek
import ConfigParser

class Odoo():

    def __init__(self):
        self.conn = None
        self.logger = None
        # Load database connection details
        config = ConfigParser.ConfigParser()
        config.read('/etc/scheduler.conf')
        self.hostname = config.get('odoo', 'hostname', 'localhost')
        self.username = config.get('odoo', 'username', 'admin')
        self.password = config.get('odoo', 'password', 'admin')
        self.database = config.get('odoo', 'database', 'odoo')
        self.port = config.get('odoo', 'port', '8069')
        self.https = config.get('odoo', 'https', '0')

        # Build url to connect to Odoo
        if self.https == "0":
            schema = 'http://'
        else:
            schema = 'https://'
        self.odoo_url = schema + self.hostname + ":" + self.port

    def connect(self):
        try:
            # Connect to Postgresql database
            self.logger.info("Hostname="+self.hostname)
            self.logger.info("Username="+self.username)
            self.logger.info("Password="+self.password)
            self.logger.info("Database="+self.database)
            self.logger.info("Port="+self.port)
            self.logger.info("Https="+self.https)

            # Create erppeek client
            self.client = erppeek.Client(self.odoo_url, self.database, self.username, self.password)
 
        except:
            message = "Couldn't connect to Odoo!"
            self.logger.error(message)
            raise Exception(message)

    def create_job_tasks(self, model_name, model_id, job_type_id, job_id):
        # See http://erppeek.readthedocs.io/en/latest/api.html
        model_proxy = self.client.model(model_name)
        instance = model_proxy.browse(model_id)
        instance.create_job_tasks(job_type_id, job_id)
        return True

    def execute(self, model_name, model_id, function):
        model_proxy = self.client.model(model_name)
        instance = model_proxy.browse(model_id)
        method = getattr(instance, function)
        try:
            method()
            return True
        except:
            return False
