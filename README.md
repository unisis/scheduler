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

  [pgsql]
  hostname=localhost
  username=postgres
  password=postgres
  database=odoo

  [odoo]
  hostname=localhost
  username=admin   
  password=admin
  database=odoo
  port=8069
  https=0

## Execution

- python scheduler.py start
- cat /var/log/scheduler.log

NOTE: "restart" and "stop" operations are also available (but not "status")

TIP: During development, we can use "print" to show the output on the console (logger sends the events to the file /var/log/scheduler.log)
