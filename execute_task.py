import os
import sys
import time
import logging

from pgsql import Pgsql
from odoo import Odoo

# Configure Logger
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/var/log/scheduler.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Pgsql service
pgsql = Pgsql()
pgsql.logger = logger
pgsql.connect()
logger.info("Connected to Pgsql!")

# Initialize Odoo service
odoo = Odoo()
odoo.logger = logger
odoo.connect()
logger.info("Connected to Odoo!")

# Get job_task_id passed via command line
job_task_id = sys.argv[1]

# Load information from database
job_task = pgsql.query_one("SELECT * FROM unison_job_task WHERE id = " + str(job_task_id))
job = pgsql.query_one("SELECT * FROM unison_job WHERE id = " + str(job_task.job_id))
job_type = pgsql.query_one("SELECT * FROM unison_job_type WHERE id = " + str(job.job_type_id))

# Execute job task (date_start was marked on execute_job.py script)
logger.info("Executing task '" + job_task.name + "' (calling to " + job_task.model_name + "." + job_task.function + "on id " + str(job_task.model_id) + ")...")
success = odoo.execute(job_task.model_name, job_task.model_id, job_task.function)
if success:
    result = "True"
else:
    result = "False"

pgsql.execute("UPDATE unison_job_task SET date_end = current_timestamp, success = " + result + " WHERE id = " + str(job_task.id))
