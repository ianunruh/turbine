# Turbine

Scoring engine for cyber defense competitions

Consists of two primary components:

* Flask application that acts as a REST API and service check executor
* Backbone.js application that provides a simple interface for reviewing check results

Requires an SQL database (PostgreSQL, MySQL, etc.) for persistence

## API

### Get latest check results

`GET /check-results`

#### Response

`HTTP/1.1 200 OK`

```json
{
  "teams": [
    {
      "id": 1,
      "name": "L33t hax0rs"
    }
  ],
  "services": [
    {
      "id": 1,
      "name": "Web server (HTTP)"
    }
  ],
  "check_results": [
    {
      "id": 1,
      "service_id": 1,
      "team_id": 1,
      "checked_at": "2014-08-31T23:32:20Z",
      "elapsed": 0.066838,
      "passed": true,
      "output": null
    }
  ]
}
```

### Get historical check results

`GET /check-results/<team_id>/<service_id>`

#### Response

`HTTP/1.1 200 OK`

```json
{
  "team": {
    "id": 1,
    "name": "L33t hax0rs"
  },
  "service": {
    "id": 1,
    "name": "Web server (HTTP)"
  },
  "check_results": [
    {
      "id": 1,
      "service_id": 1,
      "team_id": 1,
      "checked_at": "2014-08-31T23:32:20Z",
      "elapsed": 0.066838,
      "passed": true,
      "output": null
    }
  ]
}
```

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
