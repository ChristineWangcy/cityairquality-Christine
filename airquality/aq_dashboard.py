'''City Air quality'''

from flask import Flask, render_template, request
import openaq
from flask_sqlalchemy import SQLAlchemy


def create_app():

    APP = Flask(__name__)
    APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    APP.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    DB = SQLAlchemy(APP)

    API = openaq.OpenAQ()

    global results
    results = []

    global latests
    latests = []

    def get_results():
        '''get Los Angeles pm25 records'''
        results1 = []
        body = API.measurements(city='Los Angeles', parameter='pm25')[1]
        for quired_result in body['results']:
            results1.append(
                (quired_result['date']['utc'], quired_result['value']))
        return results1

    class Record(DB.Model):
        ''' build table Record'''
        id = DB.Column(DB.Integer, primary_key=True)
        datetime = DB.Column(DB.String(25))
        value = DB.Column(DB.Float, nullable=False)

        def __repr__(self):
            return f'< Time {self.datetime} --- Value {self.value} >'

    class Latest_Record(DB.Model):
        ''' build table latest record'''
        id = DB.Column(DB.Integer, primary_key=True)
        lastUpdated = DB.Column(DB.String(25))
        location = DB.Column(DB.String(25))
        parameter = DB.Column(DB.String(25))
        value = DB.Column(DB.Float, nullable=False)
        city = DB.Column(DB.String(25))

        def __repr__(self):
            return f'< LastUpdated {self.lastUpdated} --- \
                Location {self.location} --- Value {self.value} ---\
                    Parameter {self.parameter} >'

    @APP.route("/")
    def root():
        '''Retrieve date and airquality value'''
        records = Record.query.filter(Record.value >= 10).all()
        return render_template('base.html', title="home", records=records)

    @APP.route('/record', methods=['POST'])
    def add_record():
        '''add record to database'''
        city_name = request.form.get('city_name')
        global results
        results = []
        body = API.measurements(city=city_name, parameter='pm25')[1]
        for quired_result in body['results']:
            results.append(
                (quired_result['date']['utc'], quired_result['value']))
        return str(results)

    @APP.route('/latest', methods=['POST'])
    def latest_records():
        '''display latest records'''
        city = request.form.get('city')
        global latests
        latests = []
        body = API.latest(city=city)[1]
        if body['results'] != []:
            for quired_result in body['results']:
                latests.append(
                    (quired_result['measurements'][-1]['lastUpdated'],
                        quired_result['location'],
                     quired_result['measurements'][-1]['parameter'],
                     quired_result['measurements'][-1]['value'],
                     quired_result['city']))
            return render_template('latest.html', title="latest records", records=latests)
        else:
            return 'No record.'

    @ APP.route('/refresh')
    def refresh():
        '''Pull fresh data from Open AQ and replace existing data.'''
        DB.drop_all()
        DB.create_all()
        global results
        if results != []:
            for r in results:
                db_record = Record(datetime=str(r[0]), value=float(r[1]))
                DB.session.add(db_record)
        global latests
        if latests != []:
            for l in latests:
                latest_record = Latest_Record(lastUpdated=l[0],
                                              location=l[1], parameter=l[2], value=l[3],
                                              city=l[4])
                DB.session.add(latest_record)
        DB.session.commit()
        return "Data refreshed!"

    return APP
