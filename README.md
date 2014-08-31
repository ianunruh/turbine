# Turbine

Scoring engine for cyber defense competitions

Consists of two primary components:

* Flask application that acts as a REST API and service check executor
* Backbone.js application that provides a simple interface for reviewing check results

Requires an SQL database (PostgreSQL, MySQL, etc.) for persistence

## Development

Start by editing `competition.yml` to your needs. It contains the data that the scoring engine will use for service checks.

Then use the included Vagrantfile for easy development.

```bash
vagrant up
vagrant ssh

sudo -i
cd /vagrant
python turbine.py syncdb
python turbine.py runserver -h 0.0.0.0
```

At this point, the REST API will be available on [localhost:5000](http://localhost:5000).

## To-do

* Prevent multiple check results in the same time slice (1 minute)
* Calculate the overall score for a team
* Document how to develop the Backbone.js app
