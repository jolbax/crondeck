import os
import requests
from functools import wraps
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
URL = os.environ['URL']
AUTHTOKEN = os.environ['AUTHTOKEN']


class RundeckAPICall:

    headers = {'Accept':'application/json;charset=UTF-8'}

    @classmethod
    def _make_payload(cls, authtoken):
        return dict(authtoken=authtoken)

    def __init__(self, authtoken, url, path=None):
        self.url = url
        self.path = path
        self.authtoken = authtoken
        self.payload = self._make_payload(self.authtoken)
        self.headers = RundeckAPICall.headers

    def __str__(self):
        return '(url={}, path={}, authtoken={})'.format(self.url, self.path, self.authtoken)

    def __repr__(self):
        return 'RundeckAPICall(url={}, path={}, authtoken={})'.format(self.url, self.path, self.authtoken)

    def __call__(self, f):
        @wraps(f)
        def wrap(**kwargs):
            try:
                if kwargs['path']:
                    self.path = kwargs['path']
            except KeyError as e:
                e = "No path supply"
            r = requests.get(self.url + self.path, params=self.payload, headers=self.headers, verify=False)
            return r
        return wrap


@RundeckAPICall(AUTHTOKEN, URL)
def custom_call(self, path=None):
    return self


def last_scheduled_executions(project_name):
    """
    Collect all scheduled jobs and find out the last execution state
    :param project_name: String with the name of an existing rundeck project
    :return: A list with the scheduled job information
    """

    results = []

    api_project_path = '/project/' + project_name + '/jobs?scheduledFilter=true'

    jobs = custom_call(path=api_project_path)

    if not jobs.ok:
        raise ValueError('{}'.format(jobs.json()['message']))

    for job in jobs.json():
        scheduled_job = custom_call(path='/job/' + job['id'] + '/executions?max=1')
        results.append(scheduled_job.json()['executions'][0])

    return results


def list_job_executions(job_id, jobs_n):
    """
    Show the last 5 schedules for a specific job
    :param project_name: String with the name of an existing rundeck project
    :return: A list with the scheduled job information
    """

    job_executions = custom_call(path='/job/' + job_id + '/executions?max=' + str(jobs_n))
    results = job_executions.json()['executions']
    return results


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    results = []
    if request.method == 'POST':
        try:
            project_name = request.form['project_name']
            results = last_scheduled_executions(project_name)
        except ValueError as e:
            errors.append(
                "Unable to get the project information - {}".format(e)
            )
        return redirect(url_for('show_lasts_job_status', project_name=project_name))
    return render_template('index.html', errors=errors, results=results)


@app.route('/project/<string:project_name>')
def show_lasts_job_status(project_name):
    errors = []
    results = []
    try:
        results = last_scheduled_executions(project_name)
    except ValueError as e:
        errors.append(
            "Unable to get the project information - {}".format(e)
        )
    return render_template('index.html', errors=errors, results=results)


@app.route('/job/<string:job_id>')
def show_last_executions(job_id):
    errors = []
    results = []
    try:
        results = list_job_executions(job_id, 10)
    except ValueError as e:
        errors.append(
            "Unable to get the project information - {}".format(e)
        )
    return render_template('job.html', errors=errors, results=results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
