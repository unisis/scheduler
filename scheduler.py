# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python scheduler.py start

# Standard python libs
import logging
import time
import os

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

        logger.info("UniSon Scheduler initialized")

        stop = False
        while not stop:
            job_types = pgsql.query_all("SELECT * FROM unison_job_type")
            for job_type in job_types:
                print job_type.name
           
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
