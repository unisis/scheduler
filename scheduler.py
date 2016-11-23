# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python scheduler.py start

# Standard python libs
import logging
import time
import os
import ConfigParser
import imp

# Third party libs
from daemon import runner
from pgsql import Postgresql

class App():
   
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/var/run/scheduler/scheduler.pid'
        self.pidfile_timeout = 5
        self.run_as_daemon = False # False = Run on Foreground
        self.logger = None
        self.idle_wait_secs = os.environ.get('IDLE_WAIT_SECS', 1)
           
    def run(self):
        logger.info("Starting Scheduler service")

        # Initialize Postgresql
        pgsql = Postgresql()
        pgsql.logger = self.logger
        pgsql.connect()
        logger.info("Connected to Postgresql")

        # Load location of models
        config = ConfigParser.ConfigParser()
        config.read('/etc/scheduler.conf')
        self.models = config.get('general', 'models', '')
        logger.info("Location of models is " + self.models)

        logger.info("UniSon Scheduler initialized")

        stop = False
        while not stop:
            # If a job doesn't have a trigger event or a trigger frequency, 
            # it's a job type which is only manually executed
            job_types = pgsql.query_all("SELECT * FROM unison_job_type WHERE coalesce(trigger_event, '') <> '' OR coalesce(trigger_frequency, 0) > 0")
            for job_type in job_types:
                logger.info("Processing job '" + job_type.name + "'")
                # Check all instances of the model related to the job_type
                table_name = job_type.table_name
                records = pgsql.query_all("SELECT id, name, write_date, active FROM " + table_name)
                for record in records:
                    create_job = False
                    if record.active and job_type.trigger_frequency > 0:
                        # Check if last execution for this job type was executed before the configured frequency number of minutes
                        query = "SELECT DATE_PART('minute', current_timestamp - coalesce(create_date, current_timestamp)) AS minutes FROM unison_job "
                        query+= "WHERE job_type_id = " + str(job_type.id) + " AND model_id = " + str(record.id) + " ORDER BY create_date DESC LIMIT 1"
                        result = pgsql.query_one(query)
                        if result == None or result.minutes >= job_type.trigger_frequency:
                            logger.info("Creating job for '" + job_type.name + "' for instance " + table_name + " (id " + str(record.id) + ") since last job was created more than " + str(job_type.trigger_frequency) + " minutes ago")
                            create_job = True
                    else:
                        # Check if we already created the job for the event related to this job type (if this event has occurred)
                        # For 'insert' and 'delete' events -since they occurs just once during the model lifetime- we just check if a job exists.
                        # But for 'update' events -since they can occur many times during the model lifetime- we check for a job created after the last update
                        # However, if the event is 'delete' and the record is still active, we will not perform any check (the trigger event was not fired yet)
                        if not (record.active and job_type.trigger_event == "delete"):
                            # Check if there are a job created for the insert event or for the delete event (record was deleted)
                            query = "SELECT COUNT(*) FROM unison_job WHERE job_type_id = " + str(job_type.id) + " AND model_id = " + str(record.id) + " AND (success = True OR date_end IS NULL)"
                            if job_type.trigger_event == "update":
                                # This is an 'update' event which can occurs many times, also check that job was created after the last update date of the model instance
                                query += " AND write_date > " + record.update_date

                            job_exists = pgsql.query_scalar(query)
                            if job_exists == 0:
                                logger.info("Creating job for '" + job_type.name + "' for instance " + table_name + " (id " + str(record.id) + ") since an event of type '" + job_type.trigger_event + "' was detected")
                                create_job = True

                    if create_job:
                        # Insert new job
                        job_name = job_type.name + " - " + record.name + " (id " + str(record.id) + ")"
                        query = "INSERT INTO unison_job (name, job_type_id, model_id, create_date) VALUES "
                        query+= "('" + job_name + "', " + str(job_type.id) + ", " + str(record.id) + ", current_timestamp)"
                        job_id = pgsql.insert(query)
                        logger.info("Generated Job with id " + str(job_id))

                        # Request to model insert the tasks related to this job
                        model_path = self.models + "/" + job_type.model_file
                        logger.info("Requesting tasks to model on file " + model_path)
                        model = imp.load_source("unison." + job_type.model_name, model_path)
                        model.create_job_tasks(job_id)
           
            # Wait before read again
            self.logger.info("Waiting " + str(self.idle_wait_secs) + " seconds ...")
            time.sleep(float(int(self.idle_wait_secs)))

# Configure Logger
logger = logging.getLogger("DaemonLog")
debug_mode = os.environ.get('DEBUG_MODE', 0)
if (debug_mode == 0):
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.DEBUG)

# Configure Application
app = App()
if app.run_as_daemon:
    handler = logging.FileHandler("/var/log/scheduler.log")
else:
    handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
app.logger = logger

# Set run mode (foreground or background)
if app.run_as_daemon:
    # Run in background as daemon
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.daemon_context.files_preserve=[handler.stream]
    daemon_runner.do_action()
else:
    # Run on foreground (Docker-Way)
    app.run()
