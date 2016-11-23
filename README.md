# scheduler
UniSis Scheduler

This software is executed as a standalone server on the server where the UniSon module is installed.

It connects directly to the UniSon tables to see if a job should be generated according to job_type table.

If a job should be generated, after insert the record on the job table, it invokes the create_job_tasks function
on the related Odoo model so he can insert the job_task records required to complete the job.

The scheduler launch separated processes to perform the job_task tasks.

## Requirements

- sudo pip install python-daemon
- sudo pip install pygresql

## Installation

- mkdir /var/run/scheduler

- mkdir /var/log/scheduler

- nano /etc/scheduler.conf and create the connection info:

  [general]
  models=/home/leandro/Code/unison/unison/models

  [connection]
  hostname=localhost
  username=postgres
  password=postgres
  database=odoo


## Use (run in a screen)

- python scheduler.py

If you want run this software as a service, edit scheduler.py and put self.run_as_daemon=true. Then you can use:
- python scheduler.py start
- python scheduler.py restart
- python scheduler.py stop
  NOTE: Support for "status" should be provided on the LSB script
