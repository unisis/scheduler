# scheduler
UniSis Scheduler

This software is executed as a standalone server on the server where the UniSon module is installed.

It connects directly to the UniSon tables to see if a job should be generated according to job_type table.

If a job should be generated, after insert the record on the job table, it invokes the create_job_tasks function
on the related Odoo model so he can insert the job_task records required to complete the job.

The scheduler launch separated processes to perform the job_task tasks.
