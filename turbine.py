#!/usr/bin/env python
from datetime import datetime
import json
import logging
import sys
from threading import Thread

import arrow
from flask import Flask, Response, request
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from marshmallow import Serializer, fields
import yaml

import checks

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

app = Flask(__name__)
app.config.from_object('settings')

def create_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', DATE_FORMAT))

    logger = logging.getLogger('turbine')
    logger.addHandler(handler)
    
    if app.debug:
        logger.setLevel(logging.DEBUG)

    return logger

logger = create_logger()

db = SQLAlchemy(app)
manager = Manager(app)

def is_cors_preflight(req):
    return (req.method == 'OPTIONS' and
            req.headers.get('Origin') and
            req.headers.get('Access-Control-Request-Method'))

@app.before_request
def handle_cors_preflight_request(*args, **kwargs):
    if not is_cors_preflight(request):
        return

    headers = {
        'Access-Control-Allow-Methods': 'DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT',
        'Access-Control-Allow-Headers': 'X-Requested-With',
    }

    if app.debug:
        headers['Access-Control-Max-Age'] = 1

    return Response(headers=headers, content_type='text/plain')

@app.after_request
def add_cors_headers(response):
    if not request.headers.get('Origin'):
        return response

    if not is_cors_preflight(request):
        response.headers['Access-Control-Expose-Headers'] = 'ETag'

    response.headers['Access-Control-Allow-Origin'] = '*'

    return response

@app.after_request
def add_headers(response):
    response.cache_control.max_age = 30
    return response

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255))
    name = db.Column(db.String(255))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255))
    name = db.Column(db.String(255))
    active = db.Column(db.Boolean)

class CheckResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    service = db.relationship('Service')

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team')

    passed = db.Column(db.Boolean)
    output = db.Column(db.Text)
    elapsed = db.Column(db.Float)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeamSerializer(Serializer):
    id = fields.Integer()
    name = fields.String()
    
class ServiceSerializer(Serializer):
    id = fields.Integer()
    name = fields.String()

class CheckResultSerializer(Serializer):
    id = fields.Integer()

    team_id = fields.Integer()
    service_id = fields.Integer()

    passed = fields.Boolean()
    output = fields.String()
    elapsed = fields.Float()
    checked_at = fields.DateTime(format=DATE_FORMAT)

@app.route('/check-results', methods=['GET'])
def list_check_results():
    services = db.session.query(Service).filter_by(active=True)
    teams = db.session.query(Team)

    check_results = []

    for service in services:
        for team in teams:
            cr = db.session.query(CheckResult).filter_by(team_id=team.id, service_id=service.id).order_by(CheckResult.checked_at.desc()).first()
            if cr:
                check_results.append(cr)
                
    data = {
        'check_results': CheckResultSerializer(check_results, many=True).data,
        'services': ServiceSerializer(services, many=True).data,
        'teams': TeamSerializer(teams, many=True).data
    }

    body = json.dumps(data, indent=2)
    return Response(body, content_type='application/json')

@app.route('/check-results/<int:team_id>/<int:service_id>', methods=['GET'])
def list_check_results_history(team_id, service_id):
    team = db.session.query(Team).filter_by(id=team_id).first()
    service = db.session.query(Service).filter_by(id=service_id).first()

    check_results = db.session.query(CheckResult).filter_by(team_id=team_id, service_id=service_id).order_by(CheckResult.checked_at.desc()).limit(30)

    data = {
        'check_results': CheckResultSerializer(check_results, many=True).data,
        'service': ServiceSerializer(service).data,
        'team': TeamSerializer(team).data
    }

    body = json.dumps(data, indent=2)
    return Response(body, content_type='application/json')

def load_data(path):
    with open('competition.yml', 'r') as fp:
        return yaml.load(fp)

@manager.command
def syncdb(path='competition.yml'):
    db.create_all()

    data = load_data(path)

    for slug, options in data['services'].iteritems():
        service = db.session.query(Service).filter_by(slug=slug).first()
        if not service:
            service = Service(slug=slug)
            db.session.add(service)
        service.name = options['name']
        service.active = options['active']

    for slug, options in data['teams'].iteritems():
        team = db.session.query(Team).filter_by(slug=slug).first()
        if not team:
            team = Team(slug=slug)
            db.session.add(team)
        team.name = options['name']

    db.session.commit()

def in_check_phase(phases):
    now = arrow.utcnow()

    for phase in phases:
        start = arrow.get(phase[0])
        end = arrow.get(phase[1])

        if start <= now <= end:
            return True

    return False

def do_service_check(check_type, check_options):
    try:
        getattr(checks, check_type)(**check_options)
        return None, True
    except Exception as ex:
        return str(ex), False

def check_team_service(team_slug, service_slug, data):
    team_options = data['teams'][team_slug]
    service_options = data['services'][service_slug]

    # Build check options
    check_type = service_options['check_type']
    check_options = service_options['check_options']

    opts = {}

    for k, v in check_options['default'].iteritems():
        opts[k] = v

    if team_slug in check_options:
        for k, v in check_options[team_slug].iteritems():
            opts[k] = v

    for k, v in opts.iteritems():
        opts[k] = v.format(**team_options)

    logger.info('Starting check [%s] [%s]', team_slug, service_slug)

    # Do the check
    start = datetime.now()
    output, passed = do_service_check(check_type, opts)
    elapsed = datetime.now() - start

    # Insert result into database    
    team = db.session.query(Team).filter_by(slug=team_slug).first()
    service = db.session.query(Service).filter_by(slug=service_slug).first()

    check_result = CheckResult(
        team=team,
        service=service,
        passed=passed,
        output=output,
        elapsed=elapsed.total_seconds()
    )

    logger.info('Recording check [%s] [%s] => %s [%s]', team_slug, service_slug, passed, output)

    db.session.add(check_result)
    db.session.commit()

@manager.command
def runchecks(path='competition.yml', force=False):
    data = load_data(path)

    if not force and not in_check_phase(data['check_phases']):
        logger.info('Not in check phase, skipping')
        return

    logger.debug('In check phase')

    threads = list()
    for team in data['teams']:
        for service in data['services']:
            if not data['services'][service]['active']:
                continue
            
            t = Thread(
                target=check_team_service,
                args=(team, service, data)
            )
            t.start()

            threads.append(t)

    logger.debug('Waiting for checks to complete')

    for t in threads:
        t.join()

    logger.debug('All checks completed')

if __name__ == '__main__':
    manager.run()
