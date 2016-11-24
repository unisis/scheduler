            # Start task #1 on jobs not started yet
            query = "SELECT * FROM unison_job WHERE date_start IS NULL"
            new_jobs = pgsql.query_all(query)
            for new_job in new_jobs:
                pgsql.execute("UPDATE unison_job SET date_start = current_timestamp WHERE id = " + new_job.id)
                first_task = pgsql.query_one("SELECT * FROM unison_job_task WHERE job_id = " + new_job.id + " AND sequence = 1")
                self.execute_task(first_task, new_job.model_id)

            # Now, check if some tasks on running (in execution) jobs can be executed
            query = "SELECT * FROM unison_job WHERE date_start IS NOT NULL AND end_date IS NULL"
            running_jobs = pgsql.query_all(query)
            for running_job in running_jobs:
                # Get the first task which is not in execution yet
                query = "SELECT * FROM unison_job_task WHERE job_id = " + str(running_job.id) + " AND start_date IS NULL ORDER BY sequence DESC LIMIT 1"
                next_task = pgsql.query_one(query)
                if next_task != None:
                    base_query = "SELECT COUNT(*) FROM unison_job_task WHERE job_id = " + str(running_job.id)
                    if next_task.parallel:
                        # This task is parallel (can be executed at the same time of the first previous non-parallel task)
                        # So, it can be started if it doesn't have a previous non-parallel task not started yet
                        pending_previous_tasks = pgsql.query_scalar(base_query + " AND parallel = False AND start_date IS NULL AND sequence < " + next_task.sequence)
                        if pending_prev_tasks == 0:
                            self.execute_task(next_task, running_job.model_id)
                    else:
                        # This task is sequential, therefore can only be executed if we don't find any previous tasks (parallel or not) not finished yet
                        pending_previous_tasks = pgsql.query_scalar(base_query + " AND end_date IS NULL AND sequence < " + next_task.sequence)
                        if pending_prev_tasks == 0:
                            self.execute_taks(next_task, running_job.model_id)

    def launch_task(job_task, model_id):
        pgsql.execute("UPDATE unison_job_task SET date_start = current_timestamp WHERE id = " + str(job_task.id))
        odoo.execute(task.model, model_id, task.function, task.parallel)
        pgsql.execute("UPDATE unison_job_task SET date_end = current_timestamp WHERE id = " + str(job_task.id))
        return True


