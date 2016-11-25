import os
import sys
import time
import logging
import subprocess

from pgsql import Pgsql
from odoo import Odoo

def execute_task(job_task):
    # Mark task as started and launch new process on background to execute that task (date_end will be marked on execute_task.py)
    pgsql.execute("UPDATE unison_job_task SET date_start = current_timestamp WHERE id = " + str(job_task.id))
    script = sys.path[0] + "/execute_task.py"
    subprocess.Popen(["python", script, str(job_task.id)])
    time.sleep(1)
    return True

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

# Get job_id passed via command line
job_id = sys.argv[1]
job = pgsql.query_one("SELECT * FROM unison_job WHERE id = " + str(job_id))
job_type = pgsql.query_one("SELECT * FROM unison_job_type WHERE id = " + str(job.job_type_id))
logger.info("Processing job '" + job.name + "' for model " + job_type.model_name + " (id " + str(job.model_id) + ")")

finished = False
while not finished:
    # Get the first task which is not in execution yet
    query = "SELECT * FROM unison_job_task WHERE job_id = " + str(job_id) + " AND date_start IS NULL ORDER BY sequence LIMIT 1"
    next_task = pgsql.query_one(query)
    if next_task != None:
        print next_task.name
        base_query = "SELECT COUNT(*) FROM unison_job_task WHERE job_id = " + str(job_id)
        if next_task.parallel:
            # This task is parallel (can be executed at the same time of the first previous non-parallel task)
            # So, it can be started if it doesn't have a previous non-parallel task not started yet
            pending_previous_tasks = pgsql.query_scalar(base_query + " AND parallel = False AND date_start IS NULL AND sequence < " + str(next_task.sequence))
            if pending_previous_tasks == 0:
                execute_task(next_task)
        else:
            # This task is sequential, therefore can only be executed if we don't find any previous tasks (parallel or not) not finished yet
            pending_previous_tasks = pgsql.query_scalar(base_query + " AND date_end IS NULL AND sequence < " + str(next_task.sequence))
            if pending_previous_tasks == 0:
                execute_task(next_task)

    # Check if all tasks were completed
    pending_tasks = pgsql.query_scalar(base_query + " AND date_end IS NULL")
    if pending_tasks == 0:
        pgsql.execute("UPDATE unison_job SET date_end = current_timestamp, success = True WHERE id = " + str(job_id))
        finished = True

    # Check if a task has failed (cancelling the entire job)
    failed_tasks = pgsql.query_scalar(base_query + " AND date_end IS NOT NULL AND success = False")
    if failed_tasks > 0:
        pgsql.execute("UPDATE unison_job SET date_end = current_timestamp, success = False WHERE id = " + str(job_id))
        finished = True

    # Wait before read again
    logger.info("Waiting " + str(1) + " seconds ...")
    time.sleep(float(int(1)))
