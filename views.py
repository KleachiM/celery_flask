import asyncio

import celery
from celery.result import AsyncResult
from flask import request, jsonify, g
from flask.views import MethodView
from flask_httpauth import HTTPBasicAuth
from smtplib import SMTP
from celery import Task, Celery

import errors
from app import app
from validator import validate
from models import User, Advertisement
from schema import USER_CREATE
from mail_sender import start

auth = HTTPBasicAuth()


class UserView(MethodView):

    def get(self, user_id):
        user = User.by_id(user_id)
        return jsonify(user.to_dict())

    @validate('json', USER_CREATE)
    def post(self):
        user = User(**request.json)
        user.set_password(request.json['password'])
        user.add()
        return jsonify(user.to_dict())


class AdvertisementView(MethodView):

    def get(self, adv_id):
        adv = Advertisement.by_id(adv_id)
        return jsonify(adv.to_dict())

    @auth.login_required
    def post(self):
        adv = Advertisement(**request.json)
        adv.add()
        return jsonify(adv.to_dict())

    def patch(self, adv_id):
        adv = Advertisement.query.filter_by(id=adv_id).first()
        if adv.user.username == request.authorization.username:
            for key in request.json.keys():
                setattr(adv, key, request.json.get(key))
                adv.upd()
            return {'status': 'updated'}
        return {'status': 'not updated'}

    def delete(self, adv_id):
        adv = Advertisement.query.filter_by(id=adv_id).first()
        if adv.user.username == request.authorization.username:
            adv.delete()
            return {'status': 'deleted'}
        return {'status': 'not deleted'}


celery = Celery(
    __name__,
    backend='redis://localhost:6379/3',
    broker='redis://localhost:6379/4'
)
celery.conf.update(app.config)


class ContextTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


@celery.task()
def send_mail(*args):
    res = start(*args)
    return res


class ManagementView(MethodView):

    def post(self):
        users = User.query.all()
        mails = [user.email for user in users]
        task = send_mail.delay(*mails)
        return jsonify({'task.id': task.id})

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        return jsonify({'status': task.status, 'result': task.result})


@auth.verify_password
def verify_password(username, password):
    username = User.query.filter_by(username=username).first()
    if not username or not username.check_password(password):
        return False
    g.user = username
    return True


@app.route('/health/', methods=['GET', ])
def health():
    if request.method == 'GET':
        users = User.query.all()
        mails = [user.email for user in users]
        return jsonify({'status': mails})
    return {'status': 'OK'}


app.add_url_rule('/users/<int:user_id>', view_func=UserView.as_view('users_get'), methods=['GET', ])
app.add_url_rule('/users/', view_func=UserView.as_view('users_create'), methods=['POST', ])

app.add_url_rule('/advertisements/<int:adv_id>', view_func=AdvertisementView.as_view('advertisements_get'), methods=['GET', ])
app.add_url_rule('/advertisements/', view_func=AdvertisementView.as_view('advertisements_post'), methods=['POST', ])
app.add_url_rule('/advertisements/upd/<int:adv_id>', view_func=AdvertisementView.as_view('advertisements_patch'), methods=['PATCH', ])
app.add_url_rule('/advertisements/del/<int:adv_id>', view_func=AdvertisementView.as_view('advertisements_delete'), methods=['DELETE', ])

app.add_url_rule('/manage/', view_func=ManagementView.as_view('manage_post'), methods=['POST', ])
app.add_url_rule('/manage/<string:task_id>', view_func=ManagementView.as_view('manage_get'), methods=['GET', ])
