from Ossetic import app
from flask import render_template, request, url_for, session, redirect, send_file, make_response, jsonify
from Ossetic.supplement import Emails, Amend, Check
from Ossetic.models import db, Tasks, Users, Glosses, Label_names, Entry_logs, Form_labels, Meaning_labels,\
    Unit_labels, Example_labels, Forms, Units, Topological_labels, Taxonomic_labels, Grammar_labels, Mereological_labels, \
    Parts_of_speech, Messages, Task_logs, Languages, Language_assignment, Unit_links
from itsdangerous import URLSafeSerializer
from os.path import join, dirname, realpath
from re import compile, sub


@app.route('/languages', methods=['GET'])
@app.route('/languages/<int:page>', methods=['GET'])
def languages(page=1):
    Check.update()
    if request.method == 'GET':
        page_of_langs = Languages.query.order_by(Languages.lang_ru.asc()).paginate(page, 20)
        langs = page_of_langs.items
        return render_template('languages.html',
                               langs=langs,
                               items=page_of_langs,
                               Amend=Amend,
                               Check=Check,
                               Language_assignment=Language_assignment,
                               Languages=Languages
                               )

@app.route('/language/<string:lang_id>', methods=['GET'])
@app.route('/language/<string:lang_id>/<int:page>', methods=['GET'])
def language(lang_id, page=1):
    Check.update()
    if request.method == 'GET':
        try:
            lang_id = int(lang_id)
        except:
            if Languages.query.filter_by(ISO=lang_id).first():
                lang_id = Languages.query.filter_by(ISO=lang_id).first().lang_id
            else:
                return Amend.flash('Языка не найдено.', 'danger', url_for('search'))
        page_of_units = Units.query.join(Forms, Units.unit_id==Forms.unit_id).filter(Forms.gloss_id==0).join(Language_assignment, Forms.unit_id==Language_assignment.unit_id).filter(Language_assignment.lang_id==lang_id).order_by(Forms.latin.asc()).paginate(page, 100)
        units = page_of_units.items
        return render_template('language.html',
                               units=units,
                               items=page_of_units,
                               Amend=Amend,
                               Check=Check,
                               lang_id=lang_id,
                               Unit_links=Unit_links,
                               Languages=Languages
                               )


@app.route('/')
def index():
    return redirect(url_for('search'))

@app.route('/about')
def about():
    return redirect(url_for('search'))
    return render_template("about.html")

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    if request.method == 'GET':
        return render_template('contact.html')
    elif request.method == 'POST':
        if request.form.get('question') not in ['три', '3']:
            return Amend.flash(
                'Извините, мы не принимаем сообщений от роботов. Попробуйте стать человеком и напишите снова.',
                'warning',
                url_for('contact')
            )
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        Emails.send('Форма обратной связи: новое сообщение',
                    f'''
                    Сайт: {url_for('index', _external=True)}
                    <p>Отправитель: {name} ({email})</p>
                    {Amend.md(message, delete_p=False)}
                    ''',
                    ['yura@pamiri.online'],
                    reply_to=(name, email))
        return Amend.flash('Сообщение получено. Спасибо!', 'success', url_for('contact'))

@app.route('/tasks', methods=['POST', 'GET'])
def tasks():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        return render_template('tasks.html',
                               Tasks=Tasks,
                               Forms=Forms,
                               Check=Check,
                               Amend=Amend,
                               Task_logs=Task_logs,
                               user_id=str(user_id))

    elif request.method == 'POST':
        Tasks.query.filter_by(task_id=request.form.get('complete')).update({
            'status': 2
        })
        db.session.commit()
        Check.update()
        return Amend.flash('Задача отмечена выполненной.', 'success', url_for('tasks'))

"""@app.route('/task/<int:task_id>/change', methods=['POST'])
def change_task(task_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    if Tasks.query.get(task_id).assignees and user_id not in Tasks.query.get(task_id).assignees.split(',') and Users.query.get(user_id).role_id not in [3]:
        return Check.status()
"""

@app.route('/task/<int:task_id>', methods=['POST', 'GET'])
def task(task_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    #if Tasks.query.get(task_id).assignees and user_id not in Tasks.query.get(task_id).assignees.split(',') and Users.query.get(user_id).role_id not in [3]:
        #return Check.status()

    if request.method == 'GET':
        return render_template('task.html',
                               Tasks=Tasks,
                               Forms=Forms,
                               Check=Check,
                               Amend=Amend,
                               Task_logs=Task_logs,
                               Messages=Messages,
                               task_id=task_id,
                               user_id=user_id,
                               Users=Users)

    elif request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        if request.form.get('new_status'):
            if request.form.get('new_status') == 1 and Users.query.get(user_id).role_id not in [3]:
                return Check.status()
            Tasks.query.filter_by(task_id=task_id).update({
                'status': request.form.get('new_status')
            })
            db.session.add(
                Task_logs(
                    user_id=user_id,
                    task_id=task_id,
                    event=request.form.get('new_status'),
                    datetime=Check.time()
                )
            )
            db.session.commit()
            return Amend.flash('Статус изменён.', 'success', url_for('task', task_id=task_id))
        elif request.form.get('new_assignees') or request.form.get('new_assignees', 1) == '':
            value = ','.join({uid for uid in request.form.to_dict(flat=False).get('new_assignees')})
            if Tasks.query.filter_by(task_id=task_id).first().assignees:
                previous_assignees = Tasks.query.filter_by(task_id=task_id).first().assignees.split(',')
            else:
                previous_assignees = []
            Tasks.query.filter_by(task_id=task_id).update({
                'assignees': value
            })
            db.session.add(
                Task_logs(
                    user_id=user_id,
                    task_id=task_id,
                    target_id=Tasks.query.filter_by(task_id=task_id).first().assignees,
                    event=5,
                    datetime=Check.time()
                )
            )
            db.session.commit()
            if value and [Users.query.get(int(u)).email for u in Tasks.query.filter_by(task_id=task_id).first().assignees.split(',') if u and u not in previous_assignees]:
                Emails.send('Новая задача на сайте pamiri.online',
                            f'''<p>Здравствуйте. Вам назначена 
                            <a href="{url_for("task", task_id=task_id, _external=True)}">новая задача</a>:</p>
                            {Amend.md(Tasks.query.get(task_id).comments, html=True, delete_br=False)}
                            <p>Пожалуйста, изучите эту задачу и измените ее статус на подходящий. Если вы приняли задачу
                            к исполнению, отметьте это.</p>
                            <p>По выполнении задачи отметьте ее соответствующим образом на сайте.</p>
                            <p>Сообщение сгенерировано автоматически.</p>
                            ''', [Users.query.get(int(u)).email for u in Tasks.query.filter_by(task_id=task_id).first().assignees.split(',') if u and u not in previous_assignees])
            return Amend.flash('Исполнители изменены.', 'success', url_for('task', task_id=task_id))

        elif request.form.get('new_unit_ids') or request.form.get('new_unit_ids', 1) == '':
            value = sub('[^0-9,]', '', no_spaces_at_edges.sub('', request.form.get('new_unit_ids')))
            Tasks.query.filter_by(task_id=task_id).update({
                'unit_ids': ','.join({no_spaces_at_edges.sub('', i) for i in value.split(',') if i and Units.query.filter_by(unit_id=int(i)).first()})
            })
            db.session.add(
                Task_logs(
                    user_id=user_id,
                    task_id=task_id,
                    target_id=Tasks.query.filter_by(task_id=task_id).first().unit_ids,
                    event=6,
                    datetime=Check.time()
                )
            )
            db.session.commit()
            return Amend.flash('Целевые статьи изменены.', 'success', url_for('task', task_id=task_id))
        elif request.form.get('new_message'):
            db.session.add(
                Messages(
                    message=no_spaces_at_edges.sub('', request.form.get('new_message')),
                    datetime=Check.time(),
                    user_id=user_id,
                    task_id=task_id
                )
            )
            db.session.commit()
            recipients = [Users.query.get(int(u)).email for u in
                          Tasks.query.filter_by(task_id=task_id).first().assignees.split(',') if
                          request.form.get('notify_assignees') and int(u) != user_id]
            if request.form.get('notify_creator') and Task_logs.query.filter_by(task_id=task_id, event=1).first().user_id:
                recipients.append(Users.query.get(Task_logs.query.filter_by(task_id=task_id, event=1).first().user_id).email)
            recipients.extend([Users.query.filter_by(username=sub('''[!\(\)\[\]\{\};\?@#$%:'"\\,\.&/^\*]''', '', u)).first().email for u in no_spaces_at_edges.sub('', request.form.get('new_message')).split() if u.startswith('@') and Users.query.filter_by(username=sub('''[!\(\)\[\]\{\};\?@#$%:'"\\,\.&/^\*]''', '', u)).first()])
            recipients = list(set(recipients))
            if recipients:
                Emails.send('Новое сообщение на сайте pamiri.online',
                            f'''<p>Здравствуйте. В рамках дискуссии по поводу
                                <a href="{url_for("task", task_id=task_id, _external=True)}">задачи № {task_id}</a>
                                добавлено новое сообщение от редактора {Amend.username(user_id, link=False)}:</p>
                                {Amend.md(no_spaces_at_edges.sub('', request.form.get('new_message')), html=True, delete_br=False)}
                                <p>Сообщение сгенерировано автоматически.</p>
                                ''', recipients)
            return Amend.flash('Сообщение добавлено.', 'success', url_for('task', task_id=task_id))

        return Amend.flash('Произошла ошибка.', 'danger', url_for('task', task_id=task_id))

@app.route('/task/add', methods=['POST', 'GET'])
def new_task():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        return render_template('new_task.html',
                               Check=Check,
                               Amend=Amend,
                               user_id=user_id,
                               Users=Users)

    elif request.method == 'POST':
        if not request.form.get('task'):
            return Amend.flash('Введите сообщение.', 'danger', url_for('new_task'))
        no_spaces_at_edges = compile(r'( +$|^ +)')
        if not session.get('user'):
            return Check.login()
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
        if Users.query.get(user_id).role_id not in [2, 3]:
            return Check.status()
        task = Tasks(
            unit_ids=','.join({no_spaces_at_edges.sub('', i) for i in request.form.get('unit_ids').split(',') if
                               i and Units.query.filter_by(unit_id=int(i)).first()}),
            datetime=Check.time(),
            comments=request.form.get('task'),
            assignees=','.join({uid for uid in request.form.to_dict(flat=False).get('who', [])}),
            type=2
        )
        db.session.add(task)
        db.session.commit()
        db.session.add(
            Task_logs(
                task_id=task.task_id,
                user_id=user_id,
                event=1,
                datetime=Check.time()
            )
        )
        if Tasks.query.filter_by(task_id=task.task_id).first().assignees:
            db.session.add(
                Task_logs(
                    task_id=task.task_id,
                    user_id=user_id,
                    target_id=Tasks.query.filter_by(task_id=task.task_id).first().assignees,
                    event=5,
                    datetime=Check.time()
                )
            )
        if Tasks.query.filter_by(task_id=task.task_id).first().unit_ids:
            db.session.add(
                Task_logs(
                    task_id=task.task_id,
                    user_id=user_id,
                    target_id=Tasks.query.filter_by(task_id=task.task_id).first().unit_ids,
                    event=6,
                    datetime=Check.time()
                )
            )
        if Tasks.query.filter_by(task_id=task.task_id).first().assignees and [Users.query.get(int(u)).email for u in
                                                                              Tasks.query.filter_by(
                                                                                      task_id=task.task_id).first().assignees.split(
                                                                                      ',')]:
            text = f"<p><b>Задача</b>: {Amend.md(request.form.get('task'))}</p>"
            Emails.send('Новая задача на сайте pamiri.online',
                        f'''<p>Здравствуйте. Вам назначена 
                                <a href="{url_for("task", task_id=task.task_id, _external=True)}">новая задача</a>:</p>
                                {text}
                                <p>Пожалуйста, изучите эту задачу и измените ее статус на подходящий. Если вы приняли задачу
                                к исполнению, отметьте это.</p>
                                <p>По выполнении задачи отметьте ее соответствующим образом на сайте.</p>
                                <p>Сообщение сгенерировано автоматически.</p>
                                ''', [Users.query.get(int(u)).email for u in
                                      Tasks.query.filter_by(task_id=task.task_id).first().assignees.split(',')])
        db.session.commit()
        return Amend.flash('Задача добавлена.', 'success', url_for('task', task_id=task.task_id))

@app.route('/task_archive', methods=['POST', 'GET'])
def task_archive():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [3]:
        return Check.status()

    if request.method == 'GET':
        return render_template('task_archive.html',
                               Task_logs=Task_logs,
                               Tasks=Tasks,
                               Check=Check,
                               Amend=Amend)

    elif request.method == 'POST':
        type, last, user_id = (request.get_json().get('type'), request.get_json().get('last'), request.get_json().get('user_id'))
        response = []
        if type == 'mistakes':
            for i in Tasks.query.order_by(Tasks.datetime.desc()).filter(Tasks.status.in_([1, 2, 3, 4]),
                                                                        Tasks.task_id < last).filter_by(type=1).limit(
                    30).all():
                assignees = ['<div class="row align-items-center justify-content-evenly">']
                if Tasks.query.filter_by(task_id=i.task_id).first().assignees:
                    for t in Tasks.query.filter_by(task_id=i.task_id).first().assignees.split(','):
                        if t:
                            assignees.append(f'<div class="col-auto">{Amend.username(int(t))}</div>')
                if len(assignees) == 1:
                    assignees = [
                        '<div class="row align-items-center justify-content-evenly"><div class="col-auto">—</div></div>']
                else:
                    assignees.append('</div>')
                response.append(
                    [i.task_id, Amend.datetime(i.datetime), ''.join(assignees), Amend.task_status(i.status)])
            return make_response(jsonify(response), 200)
        elif type == 'editorial':
            for i in Tasks.query.order_by(Tasks.datetime.desc()).filter(Tasks.status.in_([1, 2, 3, 4]), Tasks.task_id < last).filter_by(type=2).limit(30).all():
                assignees = ['<div class="row align-items-center justify-content-evenly">']
                if Tasks.query.filter_by(task_id=i.task_id).first().assignees:
                    for t in Tasks.query.filter_by(task_id=i.task_id).first().assignees.split(','):
                        if t:
                            assignees.append(f'<div class="col-auto">{Amend.username(int(t))}</div>')
                if len(assignees) == 1:
                    assignees = ['<div class="row align-items-center justify-content-evenly"><div class="col-auto">—</div></div>']
                else:
                    assignees.append('</div>')
                response.append([i.task_id, Amend.datetime(i.datetime), ''.join(assignees), Amend.task_status(i.status)])
            return make_response(jsonify(response), 200)


@app.route('/settings', methods=['POST', 'GET'])
def settings():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id != 3:
        return Check.status()

    if request.method == 'GET':
        with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'r', encoding='UTF-8') as m:
            status = int(m.readlines()[0])
        return render_template('settings.html',
                               Glosses=Glosses,
                               Check=Check,
                               Amend=Amend,
                               maintenance=status,
                               Label_names=Label_names,
                               Parts_of_speech=Parts_of_speech)

    elif request.method == 'POST':
        new_pos = [i for i in request.form if i.startswith('new_l_pos_') and request.form.get(i)]
        new_l_ids = {}
        for p in new_pos:
            new_l_ids.update({p.split('_')[-1]: None})
        for l in new_l_ids:
            new_l_ids.update({l: ','.join([request.form.get(i) for i in request.form
                                                  if i.startswith('new_l_pos_') and i.endswith(f'_{l}')
                                                  and request.form.get(i)])})
        existent_pos = [i for i in request.form if i.startswith('l_pos_') and request.form.get(i)]
        existent_l_ids = {}
        for p in existent_pos:
            existent_l_ids.update({p.split('_')[-1]: None})
        for l in existent_l_ids:
            Label_names.query.filter_by(label_id=l).update({
                'pos_id': ','.join([request.form.get(i) for i in request.form
                                    if i.startswith('l_pos_') and i.endswith(f'_{l}')
                                    and request.form.get(i)])
            })
            db.session.commit()

        for u in request.form:
            name = u.split('_')
            value = request.form.get(u)
            if len(name) == 3:
                if name[0] == 'gl':
                    if (name[1] == 'gloss' and value) or (name[1] != 'gloss'):
                        Glosses.query.filter_by(gloss_id=int(name[-1])).update({
                            f'{name[1]}': value
                        })
                    elif (name[1] == 'gloss') and (not value):
                        if Forms.query.filter_by(gloss_id=int(name[-1])).first():
                            return Amend.flash('Данная глосса используется.', 'danger', url_for('settings'))
                        else:
                            db.session.delete(Glosses.query.get(int(name[-1])))
                elif name[0] == 'l':
                    if (name[1] == 'label' and value) or (name[1] not in ['label', 'pos']):
                        Label_names.query.filter_by(label_id=int(name[-1])).update({
                            f'{name[1]}': value
                        })
                    elif (name[1] == 'label') and (not value):
                        if Form_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Unit_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Example_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Meaning_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Grammar_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Taxonomic_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Topological_labels.query.filter_by(label_id=int(name[-1])).first() or\
                                Mereological_labels.query.filter_by(label_id=int(name[-1])).first():
                            return Amend.flash('Данная помета используется.', 'danger', url_for('settings'))
                        else:
                            db.session.delete(Label_names.query.get(int(name[-1])))
            elif len(name) == 4 and 'name' in name:
                if name[2] == 'name' and name[1] == 'gl':
                    name[2] == 'gloss'
                elif name[2] == 'name' and name[1] == 'l':
                    name[2] == 'label'
                if value:
                    if name[1] == 'gl':
                        db.session.add(
                            Glosses(
                                gloss=value,
                                decode=request.form.get(f'new_gl_decode_{name[-1]}'),
                                rank=request.form.get(f'new_gl_rank_{name[-1]}')
                            )
                        )
                        db.session.commit()
                    elif name[1] == 'l':
                        db.session.add(
                            Label_names(
                                label=value,
                                decode=request.form.get(f'new_l_decode_{name[-1]}'),
                                rank=request.form.get(f'new_l_rank_{name[-1]}'),
                                type=request.form.get(f'new_l_type_{name[-1]}'),
                                pos_id=new_l_ids.get(name[-1])
                            )
                        )
                        db.session.commit()
            db.session.commit()
        return Amend.flash('Изменения сохранены.', 'success', url_for('settings'))

@app.route('/sabr')
def maintenance():
    with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'r', encoding='UTF-8') as m:
        status = int(m.readlines()[0])
    if session.get('user'):
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
        if Users.query.get(user_id).role_id == 3:
            with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'w', encoding='UTF-8') as m:
                if status:
                    m.write('0')
                else:
                    m.write('1')
            return redirect(url_for('settings'))
        else:
            if status:
                return render_template('maintenance.html')
            else:
                return redirect(url_for('index'))
    else:
        if status:
            return render_template('maintenance.html')
        else:
            return redirect(url_for('index'))

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id != 3:
        return Check.status()

    if request.method == 'GET':
        with open(join(dirname(realpath(__file__)), 'static/maintenance.txt'), 'r', encoding='UTF-8') as m:
            status = int(m.readlines()[0])
        recent_logs = Entry_logs.query.order_by(Entry_logs.datetime.desc()).all()[:10]
        editors = {}
        for user in Users.query.all():
            unique_edits = list()
            included_unit_ids = []
            for l in Entry_logs.query.filter(Entry_logs.user_id == user.user_id, Entry_logs.event != 3).order_by(
                    Entry_logs.datetime.desc()).all():
                if l.unit_id not in included_unit_ids:
                    unique_edits.append(l)
                    included_unit_ids.append(l.unit_id)
            editors.update({user.user_id: len(unique_edits)})
        top_editors = {k: editors[k] for k in sorted(editors, key=editors.get, reverse=True)}
        return render_template('dashboard.html',
                               Entry_logs=Entry_logs,
                               Check=Check,
                               Amend=Amend,
                               top_editors=top_editors,
                               recent_logs=recent_logs,
                               Users=Users,
                               Units=Units,
                               maintenance=status,
                               Label_names=Label_names)

    elif request.method == 'POST':

        return Amend.flash('Изменения сохранены.', 'success', url_for('settings'))

@app.route('/download_db', methods=['GET', 'POST'])
def download_db():
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id != 3:
        return Check.status()
    return send_file('database3.0.db', as_attachment=True)