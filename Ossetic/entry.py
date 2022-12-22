from Ossetic import app
from flask import render_template, request, url_for, Markup, session, redirect, jsonify, make_response, Response
from Ossetic.models import db, Units, Forms, Glosses, Users, Label_names, Meanings, Examples, Example_labels, \
    Form_labels, Entry_logs, Tasks, Meaning_labels, Unit_labels, Unit_comments, Unit_pictures, Pictures, Parts_of_speech,\
    Grammar_labels, Taxonomic_labels, Topological_labels, Mereological_labels, Task_logs, Languages, Language_assignment,\
    Unit_links
from itsdangerous import URLSafeSerializer
from Ossetic.supplement import Check, Amend, BackUp, Emails
from re import compile, sub, search, IGNORECASE
import os, sqlite3, folium
from folium.plugins import MarkerCluster

@app.route('/dict/entry/<string:unit_id>', methods=['GET', 'POST'])
@app.route('/<string:en>/dict/entry/<string:unit_id>', methods=['GET', 'POST'])
def entry(unit_id, en=''):
    Check.update()
    if request.method == 'GET':
        original_unit_id = unit_id
        unit_id = int(URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id))
        if not Units.query.get(unit_id):
            return Check.page(url_for('search'))
        if Entry_logs.query.filter_by(unit_id=unit_id).order_by(Entry_logs.datetime.desc()).first():
            editor = Entry_logs.query.filter_by(unit_id=unit_id).order_by(Entry_logs.datetime.desc()).first().user_id
        else:
            editor = None
        tasks = [t.task_id for t in Tasks.query.all() if t.unit_ids and str(unit_id) in t.unit_ids.split(',')]
        first = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:abv="http://ossetic-studies.org/ns/abaevdict" xmlns:xi="http://www.w3.org/2001/XInclude">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Abaev Dictionary: entry <hi rendition="#rend_italic">ældar</hi></title>
            </titleStmt>
            <publicationStmt xml:base="../pubstmt.xml"><p>Translated from Russian in 2020 by Oleg Belyaev (ed.), Irina Khomchenkova, Julia
    Sinitsyna and Vadim Dyachkov.</p></publicationStmt>
            <sourceDesc>
                <bibl xml:lang="ru"><author>Абаев, Василий Иванович</author>.
                        <title>Историко-этимологический словарь осетинского языка</title>. Т.
                        <biblScope unit="volume">I</biblScope>. A–Kʼ. <pubPlace>М.–Л.</pubPlace>:
                        <publisher>Наука</publisher>, <date>1958</date>. С. <biblScope unit="page">??–??</biblScope>.</bibl>
            </sourceDesc>
        </fileDesc>
        <encodingDesc xml:base="../encodingdesc.xml">
    <tagsDecl>
        <rendition xml:id="rend_italic" scheme="css">font-variant: italic;</rendition>
        <rendition xml:id="rend_smallcaps" scheme="css">font-variant: small-caps;</rendition>
        <rendition xml:id="rend_singlequotes" scheme="css" scope="q">quotes: "‘" "’";</rendition>
        <rendition xml:id="rend_doublequotes" scheme="css" scope="q">quotes: "«" "»";</rendition>
    </tagsDecl>
</encodingDesc>
    </teiHeader>
    <text>
        <body>
        """
        last = """
        </body>
    </text>
</TEI>"""
        if en == 'en':
            return render_template('entry_en.html',
                               unit_id=unit_id,
                               original_unit_id=original_unit_id,
                               Markup=Markup,
                               Check=Check,
                               Amend=Amend,
                               Glosses=Glosses,
                               Units=Units,
                               Users=Users,
                               Forms=Forms,
                               editor=editor,
                               Examples=Examples,
                               Meanings=Meanings,
                               Grammar_labels=Grammar_labels,
                               Label_names=Label_names,
                               Parts_of_speech=Parts_of_speech,
                               Unit_labels=Unit_labels,
                               Languages=Languages,
                               Taxonomic_labels=Taxonomic_labels,
                               Mereological_labels=Mereological_labels,
                               Topological_labels=Topological_labels,
                               Language_assignment=Language_assignment,
                               Unit_comments=Unit_comments,
                               log_sources=[l.source for l in Entry_logs.query.filter_by(unit_id=unit_id).all()],
                               tasks=tasks,
                               first=first,
                               last=last
                               )
        else:
            return render_template('entry.html',
                                   unit_id=unit_id,
                                   original_unit_id=original_unit_id,
                                   Markup=Markup,
                                   Check=Check,
                                   Amend=Amend,
                                   Glosses=Glosses,
                                   Units=Units,
                                   Users=Users,
                                   Forms=Forms,
                                   editor=editor,
                                   Examples=Examples,
                                   Meanings=Meanings,
                                   Grammar_labels=Grammar_labels,
                                   Label_names=Label_names,
                                   Parts_of_speech=Parts_of_speech,
                                   Unit_labels=Unit_labels,
                                   Languages=Languages,
                                   Taxonomic_labels=Taxonomic_labels,
                                   Mereological_labels=Mereological_labels,
                                   Topological_labels=Topological_labels,
                                   Language_assignment=Language_assignment,
                                   Unit_comments=Unit_comments,
                                   log_sources=[l.source for l in Entry_logs.query.filter_by(unit_id=unit_id).all()],
                                   tasks=tasks,
                                   first=first,
                                   last=last
                                   )

    elif request.method == 'POST':
        original_unit_id = unit_id
        unit_id = int(URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id))
        if not request.form.get('task'):
            return Amend.flash('Введите сообщение.', 'danger', url_for('entry', unit_id=original_unit_id, ortho='po'))
        no_spaces_at_edges = compile(r'( +$|^ +)')
        if session.get('user'):
            user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
            if Users.query.get(user_id).role_id in [2, 3]:
                task = Tasks(
                        unit_ids=','.join({no_spaces_at_edges.sub('', i) for i in request.form.get('unit_ids').split(',') if i and Units.query.filter_by(unit_id=int(i)).first()}),
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
            if Tasks.query.filter_by(task_id=task.task_id).first().assignees and [Users.query.get(int(u)).email for u in Tasks.query.filter_by(task_id=task.task_id).first().assignees.split(',')]:
                text = f"<p><b>Задача</b>: {Amend.md(request.form.get('task'))}</p>"
                Emails.send('Новая задача на сайте pamiri.online',
                            f'''<p>Здравствуйте. Вам назначена 
                            <a href="{url_for("task", task_id=task.task_id, _external=True)}">новая задача</a>:</p>
                            {text}
                            <p>Пожалуйста, изучите эту задачу и измените ее статус на подходящий. Если вы приняли задачу
                            к исполнению, отметьте это.</p>
                            <p>По выполнении задачи отметьте ее соответствующим образом на сайте.</p>
                            <p>Сообщение сгенерировано автоматически.</p>
                            ''', [Users.query.get(int(u)).email for u in Tasks.query.filter_by(task_id=task.task_id).first().assignees.split(',')])
        else:
            if Entry_logs.query.filter_by(unit_id=unit_id).order_by(Entry_logs.datetime.desc()).first():
                editor = Entry_logs.query.filter_by(unit_id=unit_id).order_by(
                    Entry_logs.datetime.desc()).first().user_id
            else:
                editor = None
            task = Tasks(
                unit_ids=unit_id,
                datetime=Check.time(),
                comments=request.form.get('comments'),
                assignees=editor,
                type=2
            )
            db.session.add(task)
            db.session.commit()
            db.session.add(
                Task_logs(
                    task_id=task.task_id,
                    event=1,
                    datetime=Check.time()
                )
            )
            if editor:
                db.session.add(
                    Task_logs(
                        task_id=task.task_id,
                        target_id=editor,
                        event=5,
                        datetime=Check.time()
                    )
                )
            db.session.add(
                Task_logs(
                    task_id=task.task_id,
                    target_id=unit_id,
                    event=6,
                    datetime=Check.time()
                )
            )
            if editor:
                text = f"<p><b>Задача</b>: {Amend.md(request.form.get('task'))}</p>"
                Emails.send('Новая задача на сайте pamiri.online',
                            f'''<p>Здравствуйте. Вам назначена 
                            <a href="{url_for("task", task_id=task.task_id, _external=True)}">новая задача</a>:</p>
                            {text}
                            <p>Пожалуйста, изучите эту задачу и измените ее статус на подходящий. Если вы приняли задачу
                            к исполнению, отметьте это.</p>
                            <p>По выполнении задачи отметьте ее соответствующим образом на сайте.</p>
                            <p>Сообщение сгенерировано автоматически.</p>
                            ''', [Users.query.get(editor).email])
        db.session.commit()
        return Amend.flash('Спасибо за ваш комментарий!', 'success', url_for('entry', unit_id=original_unit_id))

@app.route('/dict/<string:unit_id>/edit', methods=['GET', 'POST'])
def edit_entry(unit_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        """for u in Units.query.all():
            if u.full_entry:
                u.full_entry = u.full_entry.replace('Г̌', 'Ɣ̌').replace('г̌', 'ɣ̌')
        for f in Forms.query.all():
            f.cyrillic = f.cyrillic.replace('Г̌', 'Ɣ̌').replace('г̌', 'ɣ̌')
        for e in Examples.query.all():
            e.example = e.example.replace('Г̌', 'Ɣ̌').replace('г̌', 'ɣ̌')
        db.session.commit()"""

        original_unit_id = unit_id
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
        if not Units.query.get(unit_id):
            return Check.page(url_for('search'))
        return render_template('editing_entry.html',
                               unit_id=unit_id,
                               original_unit_id=original_unit_id,
                               Markup=Markup,
                               Glosses=Glosses,
                               Units=Units,
                               Label_names=Label_names,
                               Form_labels=Form_labels,
                               Meanings=Meanings,
                               Meaning_labels=Meaning_labels,
                               Pictures=Pictures,
                               Languages=Languages,
                               Parts_of_speech=Parts_of_speech,
                               Unit_comments=Unit_comments,
                               Grammar_labels=Grammar_labels,
                               Entry_logs=Entry_logs,
                               Unit_labels=Unit_labels,
                               Unit_links=Unit_links,
                               Language_assignment=Language_assignment,
                               Taxonomic_labels=Taxonomic_labels,
                               Mereological_labels=Mereological_labels,
                               Topological_labels=Topological_labels,
                               Amend=Amend,
                               Forms=Forms,
                               Check=Check,
                               log_sources=[l.source for l in Entry_logs.query.filter_by(unit_id=unit_id).all()]
                               )

    if request.method == 'POST':
        cypher = unit_id
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
        no_spaces_at_edges = compile(r'( +$|^ +)')
        if request.form.get('altered'):
            source = 1
        else:
            source = Units.query.get(unit_id).source
        semantics = no_spaces_at_edges.sub('', request.form.get(f'sem_{unit_id}'))
        etymology = no_spaces_at_edges.sub('', request.form.get(f'etym_{unit_id}'))
        comments = no_spaces_at_edges.sub('', request.form.get(f'comments_{unit_id}'))
        gloss = request.form.get('gloss')
        post = dict(request.form)
        if request.form.get('root'):
            not_root = 1
        else:
            not_root = None
        if request.form.get('hidden'):
            is_shown = 0
        else:
            is_shown = 1
        for i in post:
            post.update({i: Amend.spaces(post.get(i))})

        """Changing the full text"""
        Units.query.filter_by(unit_id=unit_id).update({'full_entry': post.get('entry_text')})

        """Changing the meta and other parameters of the full entry"""
        Units.query.filter_by(unit_id=unit_id).update({'gloss': gloss,
                                                       'status': is_shown,
                                                       'not_root': not_root,
                                                       'source': request.form.get('source')
                                                       })

        Unit_labels.query.filter_by(unit_id=unit_id).delete()
        Taxonomic_labels.query.filter_by(unit_id=unit_id).delete()
        Topological_labels.query.filter_by(unit_id=unit_id).delete()
        Mereological_labels.query.filter_by(unit_id=unit_id).delete()
        db.session.commit()
        unit_labels = [l for l in post if l.startswith('l_u')]
        unit_taxonomic_labels = [l for l in post if l.startswith('l_tax_u')]
        unit_topological_labels = [l for l in post if l.startswith('l_top_u')]
        unit_mereological_labels = [l for l in post if l.startswith('l_mer_u')]
        for l in unit_labels:
            db.session.add(
                Unit_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()
        for l in unit_taxonomic_labels:
            db.session.add(
                Taxonomic_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()

        for l in unit_topological_labels:
            db.session.add(
                Topological_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()

        for l in unit_mereological_labels:
            db.session.add(
                Mereological_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()

        if Unit_comments.query.filter_by(unit_id=unit_id, type=1).first():
            Unit_comments.query.filter_by(unit_id=unit_id, type=1).update({'comment': semantics})
        else:
            db.session.add(
                Unit_comments(
                    unit_id=unit_id,
                    type=1,
                    comment=semantics
                )
            )

        if Unit_comments.query.filter_by(unit_id=unit_id, type=4).first():
            Unit_comments.query.filter_by(unit_id=unit_id, type=4).update({'comment': etymology})
        else:
            db.session.add(
                Unit_comments(
                    unit_id=unit_id,
                    type=4,
                    comment=etymology
                )
            )
        if Unit_comments.query.filter_by(unit_id=unit_id, type=5).first():
            Unit_comments.query.filter_by(unit_id=unit_id, type=5).update({'comment': no_spaces_at_edges.sub('', request.form.get(f'notes_{unit_id}'))})
        else:
            db.session.add(
                Unit_comments(
                    unit_id=unit_id,
                    type=5,
                    comment=request.form.get(f'notes_{unit_id}')
                )
            )
        if Unit_comments.query.filter_by(unit_id=unit_id, type=3).first():
            Unit_comments.query.filter_by(unit_id=unit_id, type=3).update({'comment': comments})
        else:
            db.session.add(
                Unit_comments(
                    unit_id=unit_id,
                    type=3,
                    comment=comments
                )
            )

        for l in Unit_links.query.filter_by(unit_id=unit_id).all():
            Unit_links.query.filter_by(unit_id=l.unit_id, target_id=l.target_id, type=l.type).delete()
            db.session.commit()
        for l in [i for i in post if i.startswith('link_id_') and sub('[^0-9,]', '', post.get(i))]:
            if Units.query.filter_by(unit_id=post.get(l), parent_id=None).first():
                db.session.add(
                    Unit_links(
                        unit_id=unit_id,
                        target_id=post.get(l),
                        rank=post.get(f'link_rank_{l.split("_")[-1]}', None),
                        type=post.get(f'link_type_{l.split("_")[-1]}')
                    )
                )
                db.session.commit()
        for p in Unit_pictures.query.filter_by(unit_id=unit_id).all():
            Unit_pictures.query.filter_by(unit_id=p.unit_id, picture_id=p.picture_id).delete()
            db.session.commit()
        if request.form.to_dict(flat=False).get('pictures'):
            for p in request.form.to_dict(flat=False).get('pictures'):
                db.session.add(
                    Unit_pictures(
                        unit_id=unit_id,
                        picture_id=p
                    )
                )
        for l in Language_assignment.query.filter_by(unit_id=unit_id).all():
            Language_assignment.query.filter_by(unit_id=l.unit_id, lang_id=l.lang_id).delete()
            db.session.commit()
        if request.form.to_dict(flat=False).get('langs'):
            for l in request.form.to_dict(flat=False).get('langs'):
                db.session.add(
                    Language_assignment(
                        unit_id=unit_id,
                        lang_id=l
                    )
                )
            db.session.commit()

        """Deleting"""
        for d in [d for d in post if d.startswith('delete')]:
            name = d.split('_')
            if 'm' in name:
                Amend.delete('m', post.get(d))
            elif 'f' in name:
                Amend.delete('f', post.get(d))
            elif 'u' in name:
                Amend.delete('u', post.get(d))
            elif 'g' in name:
                for f in Forms.query.filter_by(unit_id=unit_id,
                                               gloss_id=post.get(d)).all():
                    Amend.delete('f', f.form_id)


        """Processing all meanings of the lexeme"""
        for m in [m for m in post if 'lex_m' in m]:
            name = m.split('_')
            value = post.get(m)
            if len(name) > 5:
                if value and 'value' in name:
                    meaning = Meanings(
                            unit_id=unit_id,
                            meaning=value,
                            pos_id=post.get(f'existent_lex_m_pos_{name[-2]}_{name[-1]}'),
                            rank=post.get(f'existent_lex_m_rank_{name[-2]}_{name[-1]}'),
                            source=source
                        )
                    db.session.add(meaning)
                    db.session.commit()
                    for l in [l for l in post if
                              l.startswith(f'existent_lex_m_l_') and l.endswith(f'{name[-2]}_{name[-1]}')]:
                        db.session.add(
                            Meaning_labels(
                                meaning_id=meaning.meaning_id,
                                label_id=post.get(l),
                                source=source
                            )
                        )
                        db.session.commit()
                    for l in request.form.to_dict(flat=False).get(f'existent_lex_m_grammar_{name[-2]}_{name[-1]}', []):
                        db.session.add(
                            Grammar_labels(
                                meaning_id=meaning.meaning_id,
                                label_id=l
                            )
                        )
                        db.session.commit()
            else:
                if value and 'value' in name:
                    Meanings.query.filter_by(meaning_id=int(name[-1])).update({'meaning': value,
                                                                               'pos_id': post.get(f'existent_lex_m_pos_{name[-1]}'),
                                                                               'rank': post.get(f'existent_lex_m_rank_{name[-1]}')})
                elif 'value' in name and not value:
                    Amend.delete('m', int(name[-1]))
                labels = [l for l in post if l.startswith('existent_lex_m_l_') and l.endswith(f'_{name[-1]}')]
                Meaning_labels.query.filter_by(meaning_id=int(name[-1])).delete()
                db.session.commit()
                for l in labels:
                    db.session.add(
                        Meaning_labels(
                            meaning_id=int(name[-1]),
                            label_id=post.get(l),
                            source=source
                        )
                    )
                    db.session.commit()
                Grammar_labels.query.filter_by(meaning_id=int(name[-1])).delete()
                for l in request.form.to_dict(flat=False).get(f'existent_lex_m_grammar_{name[-1]}', []):
                    db.session.add(
                        Grammar_labels(
                            meaning_id=int(name[-1]),
                            label_id=l
                        )
                    )
                    db.session.commit()
            db.session.commit()

        """Processing all new forms of the lexeme"""
        skip = []
        for f in [f for f in post if '_lex_f_f' in f]:
            if f in skip:
                continue
            name = f.split('_')
            value = post.get(f)
            if not value:
                continue
            if len(name) > 6:
                if 'fl' in name:
                    if post.get(f'{name[0]}_lex_f_fc_{name[-3]}_{name[-2]}_{name[-1]}'):
                        cyrillic = post.get(f'{name[0]}_lex_f_fc_{name[-3]}_{name[-2]}_{name[-1]}')
                    else:
                        cyrillic = fullconvert(value, to_Ossetic=True, for_dict=True)[-1]
                    form = Forms(
                        latin=value,
                        cyrillic=cyrillic,
                        gloss_id=int(name[-2]),
                        unit_id=unit_id,
                        source=source
                    )
                    db.session.add(form)
                    db.session.commit()
                    skip.append(f'{name[0]}_lex_f_fc_{name[-3]}_{name[-2]}_{name[-1]}')
                    for l in [l for l in post if
                              l.startswith(f'{name[0]}_lex_f_l_') and l.endswith(f'{name[-3]}_{name[-2]}_{name[-1]}')]:
                        db.session.add(
                            Form_labels(
                                form_id=form.form_id,
                                label_id=post.get(l),
                                source=source
                            )
                        )
                        db.session.commit()
                elif 'fc' in name:
                    if post.get(f'{name[0]}_lex_f_fl_{name[-3]}_{name[-2]}_{name[-1]}'):
                        latin = post.get(f'{name[0]}_lex_f_fl_{name[-3]}_{name[-2]}_{name[-1]}')
                    else:
                        latin = fullconvert(value, to_Ossetic=False, for_dict=True)[-1]
                    form = Forms(
                        latin=latin,
                        cyrillic=value,
                        gloss_id=int(name[-2]),
                        unit_id=unit_id,
                        source=source
                    )
                    db.session.add(form)
                    db.session.commit()
                    skip.append(f'{name[0]}_lex_f_fl_{name[-3]}_{name[-2]}_{name[-1]}')
                    for l in [l for l in post if
                              l.startswith(f'{name[0]}_lex_f_l_') and l.endswith(f'{name[-3]}_{name[-2]}_{name[-1]}')]:
                        db.session.add(
                            Form_labels(
                                form_id=form.form_id,
                                label_id=post.get(l),
                                source=source
                            )
                        )
                        db.session.commit()
            else:
                if 'fl' in name:
                    if post.get(f'existent_lex_f_fc_{name[-2]}_{name[-1]}'):
                        cyrillic = post.get(f'existent_lex_f_fc_{name[-2]}_{name[-1]}')
                    else:
                        cyrillic = fullconvert(value, to_Ossetic=True)[-1]
                    latin = value
                    skip.append(f'existent_lex_f_fc_{name[-2]}_{name[-1]}')
                elif 'fc' in name:
                    if post.get(f'existent_lex_f_fl_{name[-2]}_{name[-1]}'):
                        latin = post.get(f'existent_lex_f_fl_{name[-2]}_{name[-1]}')
                    else:
                        latin = fullconvert(value, to_Ossetic=False)[-1]
                    cyrillic = value
                    skip.append(f'existent_lex_f_fl_{name[-2]}_{name[-1]}')
                Forms.query.filter_by(form_id=int(name[-1])).update({'latin': latin,
                                                                     'cyrillic': cyrillic})
                Form_labels.query.filter_by(form_id=int(name[-1])).delete()
                for l in [l for l in post if
                          l.startswith(f'existent_lex_f_l_') and l.endswith(f'_{name[-1]}')]:
                    db.session.add(
                        Form_labels(
                            form_id=int(name[-1]),
                            label_id=post.get(l),
                            source=source
                        )
                    )
                    db.session.commit()
            db.session.commit()

        """Processing idioms and cvs"""
        for type in ['i', 'cv']:
            if type == 'i':
                gloss_id = 5
            elif type == 'cv':
                gloss_id = 22
            all_units = [i for i in post if f'_{type}_m_value' in i]
            unique_units = set()
            all_unit_ids = set()
            for u in all_units:
                if u.split('_')[-1] not in all_unit_ids:
                    unique_units.add(u)
                    all_unit_ids.add(u.split('_')[-1])
            skip = list()
            for uu in unique_units:
                prefix = uu.split('_')[0]
                uu_id = uu.split('_')[-1]
                if len(uu.split('_')) > 5 and not uu.startswith('existent_'):
                    forms = [f for f in post if f'{type}_f_f' in f and f.endswith(f'_{uu_id}')]
                    if forms:
                        unit = Units(
                            parent_id=unit_id,
                            type=type,
                            source=source
                        )
                        db.session.add(unit)
                        db.session.commit()
                    else:
                        continue
                    for f in forms:
                        name = f.split('_')
                        value = post.get(f)
                        if not value:
                            continue
                        if 'fl' in name:
                            if post.get(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}'):
                                cyrillic = post.get(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}')
                            else:
                                cyrillic = fullconvert(value, to_Ossetic=True)[-1]
                            skip.append(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}')
                            form = Forms(
                                latin=value,
                                cyrillic=cyrillic,
                                gloss_id=gloss_id,
                                unit_id=unit.unit_id,
                                source=source
                            )
                            db.session.add(form)
                            db.session.commit()
                        elif 'fc' in name:
                            if post.get(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}'):
                                latin = post.get(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}')
                            else:
                                latin = fullconvert(value, to_Ossetic=False)[-1]
                            skip.append(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}')
                            form = Forms(
                                latin=latin,
                                cyrillic=value,
                                gloss_id=gloss_id,
                                unit_id=unit.unit_id,
                                source=source
                            )
                            db.session.add(form)
                            db.session.commit()
                        for l in [l for l in post if l.startswith(f'{prefix}_{type}_f_l_') and l.endswith(f'_{name[-2]}_{name[-1]}')]:
                            db.session.add(
                                Form_labels(
                                    form_id=form.form_id,
                                    label_id=post.get(l),
                                    source=source
                                )
                            )
                            db.session.commit()
                    meanings = [m for m in post if f'{prefix}_{type}_m_value_' in m and m.endswith(f'_{uu_id}')]
                    for m in meanings:
                        name = m.split('_')
                        value = post.get(m)
                        if not value:
                            continue
                        meaning = Meanings(
                                unit_id=unit.unit_id,
                                meaning=value,
                                rank=post.get(f'{prefix}_{type}_m_rank_{name[-2]}_{uu_id}'),
                                pos_id=post.get(f'{prefix}_{type}_m_pos_{name[-2]}_{name[-1]}'),
                                source=source
                            )
                        db.session.add(meaning)
                        db.session.commit()
                        for l in [l for l in post if
                                  l.startswith(f'{prefix}_{type}_m_l_') and l.endswith(f'_{name[-2]}_{uu_id}')]:
                            db.session.add(
                                Meaning_labels(
                                    meaning_id=meaning.meaning_id,
                                    label_id=post.get(l),
                                    source=source
                                )
                            )
                            db.session.commit()
                        for l in request.form.to_dict(flat=False).get(f'{prefix}_{type}_m_grammar_{name[-2]}_{name[-1]}',
                                                                      []):
                            db.session.add(
                                Grammar_labels(
                                    meaning_id=meaning.meaning_id,
                                    label_id=l
                                )
                            )
                            db.session.commit()
                elif uu.startswith('existent_'):
                    forms = [f for f in post if f.startswith(f'existent_{type}_f_f') and f.endswith(f'_{uu_id}')]
                    for f in forms:
                        name = f.split('_')
                        value = post.get(f)
                        if not value:
                            continue
                        if len(f.split('_')) < 7:
                            if 'fl' in name:
                                if post.get(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}'):
                                    cyrillic = post.get(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}')
                                else:
                                    cyrillic = fullconvert(value, to_Ossetic=True)[-1]
                                skip.append(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}')
                                form = Forms(
                                    latin=value,
                                    cyrillic=cyrillic,
                                    gloss_id=gloss_id,
                                    unit_id=int(name[-1]),
                                    source=source
                                )
                                db.session.add(form)
                                db.session.commit()
                            elif 'fc' in name:
                                if post.get(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}'):
                                    latin = post.get(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}')
                                else:
                                    latin = fullconvert(value, to_Ossetic=False)[-1]
                                skip.append(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}')
                                form = Forms(
                                    latin=latin,
                                    cyrillic=value,
                                    gloss_id=gloss_id,
                                    unit_id=int(name[-1]),
                                    source=source
                                )
                                db.session.add(form)
                                db.session.commit()
                            for l in [l for l in post if
                                      l.startswith(f'{prefix}_{type}_f_l_') and l.endswith(f'_{name[-2]}_{name[-1]}')]:
                                db.session.add(
                                    Form_labels(
                                        form_id=form.form_id,
                                        label_id=post.get(l),
                                        source=source
                                    )
                                )
                                db.session.commit()
                        else:
                            if 'fl' in name:
                                if post.get(f'{name[0]}_{type}_f_fc_{name[-3]}_{name[-2]}_{name[-1]}'):
                                    cyrillic = post.get(f'{name[0]}_{type}_f_fc_{name[-3]}_{name[-2]}_{name[-1]}')
                                else:
                                    cyrillic = fullconvert(value, to_Ossetic=True)[-1]
                                skip.append(f'{name[0]}_{type}_f_fc_{name[-3]}_{name[-2]}_{name[-1]}')
                                Forms.query.filter_by(form_id=int(name[-2])).update(
                                    {
                                        'latin': value,
                                        'cyrillic': cyrillic,
                                        'source': source
                                    }
                                )
                                db.session.commit()
                            elif 'fc' in name:
                                if post.get(f'{name[0]}_{type}_f_fl_{name[-3]}_{name[-2]}_{name[-1]}'):
                                    latin = post.get(f'{name[0]}_{type}_f_fl_{name[-3]}_{name[-2]}_{name[-1]}')
                                else:
                                    latin = fullconvert(value, to_Ossetic=False)[-1]
                                skip.append(f'{name[0]}_{type}_f_fl_{name[-3]}_{name[-2]}_{name[-1]}')
                                Forms.query.filter_by(form_id=int(name[-2])).update(
                                    {
                                        'latin': latin,
                                        'cyrillic': value,
                                        'source': source
                                    }
                                )
                                db.session.commit()
                            Form_labels.query.filter_by(form_id=int(name[-2])).delete()
                            db.session.commit()
                            for l in [l for l in post if
                                      l.startswith(f'{prefix}_{type}_f_l_') and l.endswith(
                                          f'_{name[-2]}')]:
                                db.session.add(
                                    Form_labels(
                                        form_id=int(name[-2]),
                                        label_id=post.get(l),
                                        source=source
                                    )
                                )
                                db.session.commit()
                    meanings = [m for m in post if f'{prefix}_{type}_m_value_' in m and m.endswith(f'_{uu_id}')]
                    for m in meanings:
                        name = m.split('_')
                        value = post.get(m)
                        if not value:
                            continue
                        if len(m.split('_')) < 7:
                            meaning = Meanings(
                                unit_id=uu_id,
                                meaning=value,
                                rank=post.get(f'{prefix}_{type}_m_rank_{name[-2]}_{uu_id}'),
                                pos_id=post.get(f'{prefix}_{type}_m_pos_{name[-2]}_{uu_id}'),
                                source=source
                            )
                            db.session.add(meaning)
                            db.session.commit()
                            for l in [l for l in post if
                                      l.startswith(f'{prefix}_{type}_m_l_') and l.endswith(f'_{name[-2]}_{uu_id}')]:
                                db.session.add(
                                    Meaning_labels(
                                        meaning_id=meaning.meaning_id,
                                        label_id=post.get(l),
                                        source=source
                                    )
                                )
                                db.session.commit()
                            for l in request.form.to_dict(flat=False).get(
                                    f'{prefix}_{type}_m_grammar_{name[-2]}_{name[-1]}',
                                    []):
                                db.session.add(
                                    Grammar_labels(
                                        meaning_id=meaning.meaning_id,
                                        label_id=l
                                    )
                                )
                                db.session.commit()
                        else:
                            Meanings.query.filter_by(meaning_id=int(name[-2])).update(
                                {
                                    'meaning': value,
                                    'rank': post.get(f'{prefix}_{type}_m_rank_{int(name[-2])}'),
                                    'pos_id': post.get(f'{prefix}_{type}_m_pos_{int(name[-2])}'),
                                    'source': source
                                }
                            )
                            Meaning_labels.query.filter_by(meaning_id=int(name[-2])).delete()
                            Grammar_labels.query.filter_by(meaning_id=int(name[-2])).delete()
                            db.session.commit()
                            for l in [l for l in post if
                                      l.startswith(f'{prefix}_{type}_m_l_') and l.endswith(f'_{name[-2]}')]:
                                db.session.add(
                                    Meaning_labels(
                                        meaning_id=int(name[-2]),
                                        label_id=post.get(l),
                                        source=source
                                    )
                                )
                                db.session.commit()
                            for l in request.form.to_dict(flat=False).get(
                                    f'{prefix}_{type}_m_grammar_{name[-2]}',
                                    []):
                                db.session.add(
                                    Grammar_labels(
                                        meaning_id=int(name[-2]),
                                        label_id=l
                                    )
                                )
                                db.session.commit()
            update_stems(unit_id)
        db.session.commit()
        if len(Meanings.query.filter_by(unit_id=unit_id).all()) == 1 and Meaning_labels.query.filter_by(
                meaning_id=Meanings.query.filter_by(unit_id=unit_id).first().meaning_id).first():
            for l in Meaning_labels.query.filter_by(
                    meaning_id=Meanings.query.filter_by(unit_id=unit_id).first().meaning_id).all():
                if not Unit_labels.query.filter_by(unit_id=unit_id, label_id=l.label_id).first():
                    db.session.add(
                        Unit_labels(
                            unit_id=unit_id,
                            label_id=l.label_id
                        )
                    )
                Meaning_labels.query.filter_by(meaning_id=Meanings.query.filter_by(unit_id=unit_id).first().meaning_id,
                                               label_id=l.label_id).delete()
        BackUp.add_dump(unit_id, user_id=user_id, event=1, source=source)
        db.session.commit()
        return Amend.flash('Изменения сохранены.', 'success', url_for('edit_entry', unit_id=cypher))

@app.route('/dict/<string:unit_id>/edit/examples', methods=['GET', 'POST'])
def examples(unit_id):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        cypher = unit_id
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
        if not Units.query.get(unit_id):
            return Check.page(url_for('search'))
        form_ids = [f[0] for f in Forms.query.filter_by(unit_id=unit_id).with_entities(Forms.gloss_id)]
        form_ids = list(dict.fromkeys(form_ids))
        free_glosses = [g[0] for g in Glosses.query.with_entities(Glosses.gloss_id) if Glosses.query.get(g[0]).decode and g[0] not in form_ids]
        return render_template('examples.html',
                               unit_id=unit_id,
                               original_unit_id=cypher,
                               free_glosses=free_glosses,
                               Markup=Markup,
                               Glosses=Glosses,
                               Units=Units,
                               Label_names=Label_names,
                               Meanings=Meanings,
                               Example_labels=Example_labels,
                               Entry_logs=Entry_logs,
                               Amend=Amend,
                               Forms=Forms,
                               Check=Check,
                               Examples=Examples,
                               log_sources=[l.source for l in Entry_logs.query.filter_by(unit_id=unit_id).all()]
                               )

    if request.method == 'POST':
        cypher = unit_id
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
        if request.form.get('altered'):
            source = 1
        else:
            source = Units.query.get(unit_id).source
        post = dict(request.form)
        Units.query.filter_by(unit_id=unit_id).update({'full_entry': post.get('entry_text')})
        for i in post:
            post.update({i: Amend.spaces(post.get(i))})
        #print(post)
        m_ids = list(set([ident.split('_')[-1] for ident in post]))
        for ident in m_ids:
            parts = [i for i in post if i.split('_')[-1] == ident and 'e_' in i]
            for part in parts:
                if 'new' in part:
                    name = part.split('_')
                    value = post.get(part)
                    if value:
                        example = Examples(
                            meaning_id=int(name[-1]),
                            example=value,
                            translation=post.get(f'tr_new_{name[-2]}_{name[-1]}'),
                            source=source
                        )
                        db.session.add(example)
                        db.session.commit()
                        for l in [i for i in post if len(i.split('_')) > 2 and i.split('_')[-2] == name[-2] and 'l_new' in i and i.split('_')[-1] == name[-1]]:
                            db.session.add(
                                Example_labels(
                                    example_id=int(example.example_id),
                                    label_id=int(post.get(l)),
                                    source=source
                                )
                            )
                            db.session.commit()
                elif 'd_whole' in part:
                    name = part.split('_')
                    Amend.delete('e', int(name[-1]))
                else:
                    name = part.split('_')
                    value = post.get(part)
                    if value:
                        Examples.query.filter_by(example_id=int(name[-1])).update({'example': value,
                                                                                   'translation': post.get(f'tr_{name[-1]}')})
                        Example_labels.query.filter_by(example_id=int(name[-1])).delete()
                        db.session.commit()
                        for l in [i for i in post if i.split('_')[-1] == ident and 'l_' in i and 'new' not in i]:
                            db.session.add(
                                Example_labels(
                                    example_id=int(name[-1]),
                                    label_id=int(post.get(l)),
                                    source=source
                                )
                            )
                            db.session.commit()
                    else:
                        Examples.query.filter_by(example_id=int(name[-1])).delete()
        db.session.commit()
        BackUp.add_dump(unit_id, user_id=user_id, event=2, source=source)
        return Amend.flash('Изменения сохранены.', 'success', url_for('examples', unit_id=cypher))

@app.route('/dict/<string:unit_id>/edit/history', methods=['GET', 'POST'])
def entry_history(unit_id):
    if request.method == 'GET':
        if not session.get('user'):
            return Check.login()
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
        if Users.query.get(user_id).role_id not in [2, 3]:
            return Check.status()
        Check.update()
        original_unit_id = unit_id
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
        if not Units.query.get(unit_id):
            return Check.page(url_for('search'))
        #entry_dumps = [loads(l.entry_dump) for l in Entry_logs.query.filter_by(unit_id=unit_id).all()]
        return render_template('entry_history.html',
                               unit_id=unit_id,
                               original_unit_id=original_unit_id,
                               Markup=Markup,
                               Units=Units,
                               Forms=Forms,
                               Users=Users,
                               Examples=Examples,
                               Label_names=Label_names,
                               Amend=Amend,
                               Entry_logs=Entry_logs,
                               #entry_dumps=entry_dumps,
                               Check=Check,
                               Glosses=Glosses
                               )

    if request.method == 'POST':
        if not session.get('user'):
            return Check.login()
        user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
        if Users.query.get(user_id).role_id not in [1, 2, 3]:
            return Check.status()
        cypher = unit_id
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
        if request.form.get('altered'):
            source = 1
        else:
            source = Units.query.get(unit_id).source
        target_log_id = int(request.form.get('log_id'))
        if target_log_id:
            BackUp.add_dump(unit_id, user_id=user_id, event=3, source=source)
            BackUp.rollback(target_log_id)
            return Amend.flash('Откат получен.', 'success', url_for('entry_history', unit_id=cypher))
        else:
            return Amend.flash('Ошибка при откате.', 'danger', url_for('entry_history', unit_id=cypher))

@app.route('/dict/<string:unit_id>/edit/delete', methods=['GET'])
def delete_entry(unit_id):
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id != 3:
        return Check.status()
    Check.update()
    unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').loads(unit_id)
    if not Units.query.get(unit_id):
        return Amend.flash('Проверьте ID статьи.', 'success', url_for('search'))
    else:
        Amend.delete('u', unit_id)
        db.session.commit()
    return Amend.flash('Статья удалена.', 'success', url_for('search'))
@app.route('/<string:en>/entries', methods=['GET', 'POST'])
@app.route('/<string:en>/entries/<int:page>', methods=['GET', 'POST'])
@app.route('/entries', methods=['GET', 'POST'])
@app.route('/entries/<int:page>', methods=['GET', 'POST'])
def entries(page=1, en=''):
    Check.update()
    if request.method == 'GET':
        page_of_entries = Units.query.filter_by(parent_id=None).join(Forms).order_by(Forms.latin.asc(), Forms.form_id.asc()).paginate(page, 100)
        entries = page_of_entries.items
        if en == 'en':
            return render_template('entries_en.html',
                                   entries=entries,
                                   items=page_of_entries,
                                   Amend=Amend,
                                   Forms=Forms,
                                   Entry_logs=Entry_logs,
                                   Language_assignment=Language_assignment,
                                   Languages=Languages,
                                   page=page
                                   )
        else:
            return render_template('entries.html',
                                   entries=entries,
                                   items=page_of_entries,
                                   Amend=Amend,
                                   Forms=Forms,
                                   Entry_logs=Entry_logs,
                                   Language_assignment=Language_assignment,
                                   Languages=Languages,
                                   page=page
                                   )

    elif request.method == 'POST':
        if request.form.get('query'):
            if request.form.get('parameter') == 'ID':
                try:
                    int(request.form.get('query'))
                except:
                    return Amend.flash('Введите число.', 'danger', url_for('profiles'))
                return redirect(url_for('entry', unit_id=URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(int(request.form.get('query'))), ortho='po'))
        return Amend.flash('Введите поисковый запрос.', 'danger', url_for('profiles'))


@app.route('/dict/add_entry', methods=['GET', 'POST'])
def add_entry(unit_id='new'):
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()

    if request.method == 'GET':
        return render_template('adding_entry.html',
                               Markup=Markup,
                               Glosses=Glosses,
                               Units=Units,
                               Label_names=Label_names,
                               Form_labels=Form_labels,
                               Meaning_labels=Meaning_labels,
                               Topological_labels=Topological_labels,
                               Mereological_labels=Mereological_labels,
                               Taxonomic_labels=Taxonomic_labels,
                               Grammar_labels=Grammar_labels,
                               Pictures=Pictures,
                               Unit_comments=Unit_comments,
                               Entry_logs=Entry_logs,
                               Unit_labels=Unit_labels,
                               Parts_of_speech=Parts_of_speech,
                               Languages=Languages,
                               Amend=Amend,
                               Forms=Forms,
                               Check=Check,
                               unit_id=unit_id
                               )

    if request.method == 'POST':
        no_spaces_at_edges = compile(r'( +$|^ +)')
        def cypher_unit_id(id):
            return URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(id)
        semantics = no_spaces_at_edges.sub('', request.form.get(f'sem_{unit_id}'))
        etymology = no_spaces_at_edges.sub('', request.form.get(f'etym_{unit_id}'))
        comments = no_spaces_at_edges.sub('', request.form.get(f'comments_{unit_id}'))
        gloss = request.form.get('gloss')
        post = dict(request.form)
        all_forms = [f for f in post if '_f_f' in f and post.get(f)]
        if not all_forms:
            return Amend.flash('Чтобы добавить статью, нужна хотя бы одна форма.', 'danger', url_for('add_entry'))
        all_meanings = [m for m in post if '_m_value' in m and post.get(m)]
        if not all_meanings:
            return Amend.flash('Чтобы добавить статью, нужно хотя бы одно значение.', 'danger', url_for('add_entry'))
        if request.form.get('root'):
            not_root = 1
        else:
            not_root = None
        if request.form.get('hidden'):
            is_shown = 0
        else:
            is_shown = 1
        for i in post:
            post.update({i: Amend.spaces(post.get(i))})
        source = request.form.get('source')
        unit = Units(
            full_entry=post.get('entry_text'),
            gloss=gloss,
            source=request.form.get('source'),
            status=is_shown,
            not_root=not_root,
            lang_id=','.join(request.form.to_dict(flat=False).get('langs'))
        )
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.unit_id
        unit_labels = [l for l in post if l.startswith('l_u')]
        unit_taxonomic_labels = [l for l in post if l.startswith('l_t_u')]
        unit_topological_labels = [l for l in post if l.startswith('l_top_u')]
        unit_mereological_labels = [l for l in post if l.startswith('l_mer_u')]
        for l in unit_labels:
            db.session.add(
                Unit_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()
        for l in unit_taxonomic_labels:
            db.session.add(
                Taxonomic_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()

        for l in unit_topological_labels:
            db.session.add(
                Topological_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()

        for l in unit_mereological_labels:
            db.session.add(
                Mereological_labels(
                    unit_id=int(unit_id),
                    label_id=int(post.get(l))
                )
            )
            db.session.commit()

        db.session.add(
            Unit_comments(
                unit_id=unit_id,
                type=1,
                comment=semantics
            )
        )
        db.session.add(
            Unit_comments(
                unit_id=unit_id,
                type=4,
                comment=etymology
            )
        )
        db.session.add(
            Unit_comments(
                unit_id=unit_id,
                type=3,
                comment=comments
            )
        )
        db.session.add(
            Unit_comments(
                unit_id=unit_id,
                type=5,
                comment=no_spaces_at_edges.sub('', request.form.get(f'notes_{unit_id}'))
            )
        )
        if request.form.to_dict(flat=False).get('pictures'):
            for p in request.form.to_dict(flat=False).get('pictures'):
                db.session.add(
                    Unit_pictures(
                        unit_id=unit_id,
                        picture_id=p
                    )
                )
        for l in [i for i in post if i.startswith('link_id_') and sub('[^0-9,]', '', post.get(i))]:
            if Units.query.filter_by(unit_id=post.get(l), parent_id=None).first():
                db.session.add(
                    Unit_links(
                        unit_id=unit_id,
                        target_id=post.get(l),
                        rank=post.get(f'link_rank_{l.split("_")[-1]}', None),
                        type=post.get(f'link_type_{l.split("_")[-1]}')
                    )
                )
                db.session.commit()
        if request.form.to_dict(flat=False).get('langs'):
            for l in request.form.to_dict(flat=False).get('langs'):
                db.session.add(
                    Language_assignment(
                        unit_id=unit_id,
                        lang_id=l
                    )
                )
            db.session.commit()

        """Processing all meanings of the lexeme"""
        for m in [m for m in post if 'lex_m' in m]:
            name = m.split('_')
            value = post.get(m)
            if len(name) > 5:
                if value and 'value' in name:
                    meaning = Meanings(
                            unit_id=unit_id,
                            meaning=value,
                            pos_id=post.get(f'existent_lex_m_pos_{name[-2]}_{name[-1]}'),
                            rank=post.get(f'existent_lex_m_rank_{name[-2]}_{name[-1]}'),
                            source=source
                        )
                    db.session.add(meaning)
                    db.session.commit()
                    for l in [l for l in post if
                              l.startswith(f'existent_lex_m_l_') and l.endswith(f'{name[-2]}_{name[-1]}')]:
                        db.session.add(
                            Meaning_labels(
                                meaning_id=meaning.meaning_id,
                                label_id=post.get(l),
                                source=source
                            )
                        )
                        db.session.commit()
                    for l in request.form.to_dict(flat=False).get(f'existent_lex_m_grammar_{name[-2]}_{name[-1]}', []):
                        db.session.add(
                            Grammar_labels(
                                meaning_id=meaning.meaning_id,
                                label_id=l
                            )
                        )
                        db.session.commit()
            db.session.commit()

        """Processing all new forms of the lexeme"""
        skip = []
        for f in [f for f in post if '_lex_f_f' in f]:
            if f in skip:
                continue
            name = f.split('_')
            value = post.get(f)
            if not value:
                continue
            if len(name) > 6:
                if 'fl' in name:
                    if post.get(f'{name[0]}_lex_f_fc_{name[-3]}_{name[-2]}_{name[-1]}'):
                        cyrillic = post.get(f'{name[0]}_lex_f_fc_{name[-3]}_{name[-2]}_{name[-1]}')
                    else:
                        cyrillic = fullconvert(value, to_Ossetic=True)[-1]
                    form = Forms(
                        latin=value,
                        cyrillic=cyrillic,
                        gloss_id=int(name[-2]),
                        unit_id=unit_id,
                        source=source
                    )
                    db.session.add(form)
                    db.session.commit()
                    skip.append(f'{name[0]}_lex_f_fc_{name[-3]}_{name[-2]}_{name[-1]}')
                    for l in [l for l in post if
                              l.startswith(f'{name[0]}_lex_f_l_') and l.endswith(f'{name[-3]}_{name[-2]}_{name[-1]}')]:
                        db.session.add(
                            Form_labels(
                                form_id=form.form_id,
                                label_id=post.get(l),
                                source=source
                            )
                        )
                        db.session.commit()
                elif 'fc' in name:
                    if post.get(f'{name[0]}_lex_f_fl_{name[-3]}_{name[-2]}_{name[-1]}'):
                        latin = post.get(f'{name[0]}_lex_f_fl_{name[-3]}_{name[-2]}_{name[-1]}')
                    else:
                        latin = fullconvert(value, to_Ossetic=False)[-1]
                    form = Forms(
                        latin=latin,
                        cyrillic=value,
                        gloss_id=int(name[-2]),
                        unit_id=unit_id,
                        source=source
                    )
                    db.session.add(form)
                    db.session.commit()
                    skip.append(f'{name[0]}_lex_f_fl_{name[-3]}_{name[-2]}_{name[-1]}')
                    for l in [l for l in post if
                              l.startswith(f'{name[0]}_lex_f_l_') and l.endswith(f'{name[-3]}_{name[-2]}_{name[-1]}')]:
                        db.session.add(
                            Form_labels(
                                form_id=form.form_id,
                                label_id=post.get(l),
                                source=source
                            )
                        )
                        db.session.commit()

        """Processing idioms and cvs"""
        for type in ['i', 'cv']:
            if type == 'i':
                gloss_id = 5
            elif type == 'cv':
                gloss_id = 22
            all_units = [i for i in post if f'_{type}_m_value' in i]
            unique_units = set()
            all_unit_ids = set()
            for u in all_units:
                if u.split('_')[-1] not in all_unit_ids:
                    unique_units.add(u)
                    all_unit_ids.add(u.split('_')[-1])
            skip = list()
            for uu in unique_units:
                prefix = uu.split('_')[0]
                uu_id = uu.split('_')[-1]
                if len(uu.split('_')) > 5 and not uu.startswith('existent_'):
                    forms = [f for f in post if f'{type}_f_f' in f and f.endswith(f'_{uu_id}')]
                    if forms:
                        unit = Units(
                            parent_id=unit_id,
                            type=type,
                            source=source
                        )
                        db.session.add(unit)
                        db.session.commit()
                    else:
                        continue
                    for f in forms:
                        name = f.split('_')
                        value = post.get(f)
                        if not value:
                            continue
                        if 'fl' in name:
                            if post.get(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}'):
                                cyrillic = post.get(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}')
                            else:
                                cyrillic = fullconvert(value, to_Ossetic=True)[-1]
                            skip.append(f'{name[0]}_{type}_f_fc_{name[-2]}_{name[-1]}')
                            form = Forms(
                                latin=value,
                                cyrillic=cyrillic,
                                gloss_id=gloss_id,
                                unit_id=unit.unit_id,
                                source=source
                            )
                            db.session.add(form)
                            db.session.commit()
                        elif 'fc' in name:
                            if post.get(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}'):
                                latin = post.get(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}')
                            else:
                                latin = fullconvert(value, to_Ossetic=False)[-1]
                            skip.append(f'{name[0]}_{type}_f_fl_{name[-2]}_{name[-1]}')
                            form = Forms(
                                latin=latin,
                                cyrillic=value,
                                gloss_id=gloss_id,
                                unit_id=unit.unit_id,
                                source=source
                            )
                            db.session.add(form)
                            db.session.commit()
                        for l in [l for l in post if l.startswith(f'{prefix}_{type}_f_l_') and l.endswith(f'_{name[-2]}_{name[-1]}')]:
                            db.session.add(
                                Form_labels(
                                    form_id=form.form_id,
                                    label_id=post.get(l),
                                    source=source
                                )
                            )
                            db.session.commit()
                    meanings = [m for m in post if f'{prefix}_{type}_m_value_' in m and m.endswith(f'_{uu_id}')]
                    for m in meanings:
                        name = m.split('_')
                        value = post.get(m)
                        if not value:
                            continue
                        meaning = Meanings(
                                unit_id=unit.unit_id,
                                meaning=value,
                                rank=post.get(f'{prefix}_{type}_m_rank_{name[-2]}_{uu_id}'),
                                pos_id=post.get(f'{prefix}_{type}_m_pos_{name[-2]}_{name[-1]}'),
                                source=source
                            )
                        db.session.add(meaning)
                        db.session.commit()
                        for l in [l for l in post if
                                  l.startswith(f'{prefix}_{type}_m_l_') and l.endswith(f'_{name[-2]}_{uu_id}')]:
                            db.session.add(
                                Meaning_labels(
                                    meaning_id=meaning.meaning_id,
                                    label_id=post.get(l),
                                    source=source
                                )
                            )
                            db.session.commit()
                        for l in request.form.to_dict(flat=False).get(f'{prefix}_{type}_m_grammar_{name[-2]}_{name[-1]}',
                                                                      []):
                            db.session.add(
                                Grammar_labels(
                                    meaning_id=meaning.meaning_id,
                                    label_id=l
                                )
                            )
                            db.session.commit()
            update_stems(unit_id)
        db.session.commit()
        if len(Meanings.query.filter_by(unit_id=unit_id).all()) == 1 and Meaning_labels.query.filter_by(
                meaning_id=Meanings.query.filter_by(unit_id=unit_id).first().meaning_id).first():
            for l in Meaning_labels.query.filter_by(
                    meaning_id=Meanings.query.filter_by(unit_id=unit_id).first().meaning_id).all():
                if not Unit_labels.query.filter_by(unit_id=unit_id, label_id=l.label_id).first():
                    db.session.add(
                        Unit_labels(
                            unit_id=unit_id,
                            label_id=l.label_id
                        )
                    )
                Meaning_labels.query.filter_by(meaning_id=Meanings.query.filter_by(unit_id=unit_id).first().meaning_id,
                                               label_id=l.label_id).delete()
        BackUp.add_dump(unit_id, user_id=user_id, event=4, source=source)
        db.session.commit()
        return Amend.flash('Статья добавлена.', 'success', url_for('edit_entry', unit_id=cypher_unit_id(unit_id)))

@app.route('/edit/autocomplete', methods=['POST'])
def autocomplete():
    Check.update()
    """
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    """
    no_spaces_at_edges = compile(r'( +$|^ +)')
    type, input, area, langs, en = (
    request.get_json().get('type'), no_spaces_at_edges.sub('', request.get_json().get('input')).lower(),
    request.get_json().get('area', ''), request.get_json().get('langs', ''), request.get_json().get('en', ''))
    langs = tuple([int(l) for l in langs if Languages.query.filter_by(lang_id=int(l)).first()])
    if len(langs) == 1:
        langs = (langs[0], langs[0])
    if type == 'search_input' and len(input) > 2:
        create_query = Amend.create_query
        query = create_query(input, lengths='l', mapping=False, type='sub_beginning', langs=langs)
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "abaev.db"))
        conn.create_function("REGEXP", 2, Amend.regexp)
        cur = conn.cursor()
        if area not in ['meaning', 'full_entry']:
            res = cur.execute(
                f'''
                            SELECT latin FROM Forms
                            JOIN Units ON Forms.unit_id == Units.unit_id
                            JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id 
                            WHERE gloss_id NOT IN (5,22) AND
                            latin REGEXP ?
                            AND Units.status == 1 AND Language_assignment.lang_id IN {langs}
                            ORDER BY latin ASC 
                            LIMIT 15;
                            ''',
                [query]
            )
            response = {f[0].lower() for f in res.fetchall()}
        elif area == 'meaning':
            if en == 'en':
                res = cur.execute(
                    f'''
                    SELECT Meanings.meaning_en FROM Meanings 
                    JOIN Units ON Meanings.unit_id == Units.unit_id
                    JOIN Language_assignment ON Meanings.unit_id == Language_assignment.unit_id
                    WHERE meaning_en REGEXP ? AND Units.status == 1 AND Language_assignment.lang_id IN {langs}
                    ORDER BY Units.full_entry_en ASC
                    ''',
                    [create_query(input, lengths='l', mapping=False, type='sub_beginning')]
                )
            else:
                res = cur.execute(
                    f'''
                            SELECT Meanings.meaning FROM Meanings 
                            JOIN Units ON Meanings.unit_id == Units.unit_id
                            JOIN Language_assignment ON Meanings.unit_id == Language_assignment.unit_id
                            WHERE meaning REGEXP ? AND Units.status == 1 AND Language_assignment.lang_id IN {langs}
                            ORDER BY Units.full_entry ASC
                            ''',
                [create_query(input, lengths='l', mapping=False, type='sub_beginning')]
            )
            response = set()
            for m in res.fetchall():
                m = sub(r'[́\.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n*]', '', m[0]).split()
                for t in m:
                    if search(query, sub('[́‌]', '', t), flags=IGNORECASE):
                        response.add(t.lower())
        else:
            return {}
        return jsonify(list(response)[:5])
    elif type == 'preview_entry':
        if Units.query.filter_by(unit_id=input, parent_id=None).first():
            return jsonify(Amend.entry(input, link=True, new_window=True))
        return jsonify('статья не найдена')
    return jsonify([])

@app.route('/dict/get_xml/<string:unit_id>', methods=['GET', 'POST'])
@app.route('/<string:en>/dict/get_xml/<string:unit_id>', methods=['GET', 'POST'])
def xml_entry(unit_id, en=''):
    if en == 'en':
        what = Units.query.get(unit_id).full_entry_en
        header = f'''<?xml-stylesheet type="text/css" href="{url_for('static', filename='css/Abaev/abaev.css')}"?>
                    <?xml-stylesheet type="text/css" href="{url_for('static', filename='css/Abaev/en.css')}"?>
                    <?xml-stylesheet type="text/css" href="{url_for('static', filename='css/Abaev/en_langs.css')}"?>
                        '''
    else:
        what = Units.query.get(unit_id).full_entry
        header = f'''<?xml-stylesheet type="text/css" href="{url_for('static', filename='css/Abaev/abaev.css')}"?>
            <?xml-stylesheet type="text/css" href="{url_for('static', filename='css/Abaev/ru.css')}"?>
            <?xml-stylesheet type="text/css" href="{url_for('static', filename='css/Abaev/ru_langs.css')}"?>
                '''
    entry_text = f"""<?xml version="1.0" encoding="UTF-8"?>
    {header}
    <TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:abv="http://ossetic-studies.org/ns/abaevdict" xmlns:xi="http://www.w3.org/2001/XInclude">
        <teiHeader>
            <fileDesc>
                <titleStmt>
                    <title>Abaev Dictionary: entry <hi rendition="#rend_italic">ældar</hi></title>
                </titleStmt>
                <publicationStmt xml:base="../pubstmt.xml"><p>Translated from Russian in 2020 by Oleg Belyaev (ed.), Irina Khomchenkova, Julia
        Sinitsyna and Vadim Dyachkov.</p></publicationStmt>
                <sourceDesc>
                    <bibl xml:lang="ru"><author>Абаев, Василий Иванович</author>.
                            <title>Историко-этимологический словарь осетинского языка</title>. Т.
                            <biblScope unit="volume">I</biblScope>. A–Kʼ. <pubPlace>М.–Л.</pubPlace>:
                            <publisher>Наука</publisher>, <date>1958</date>. С. <biblScope unit="page">??–??</biblScope>.</bibl>
                </sourceDesc>
            </fileDesc>
            <encodingDesc xml:base="../encodingdesc.xml">
        <tagsDecl>
            <rendition xml:id="rend_italic" scheme="css">font-variant: italic;</rendition>
            <rendition xml:id="rend_smallcaps" scheme="css">font-variant: small-caps;</rendition>
            <rendition xml:id="rend_singlequotes" scheme="css" scope="q">quotes: "‘" "’";</rendition>
            <rendition xml:id="rend_doublequotes" scheme="css" scope="q">quotes: "«" "»";</rendition>
        </tagsDecl>
    </encodingDesc>
        </teiHeader>
        <text>
            <body>
                {what}
            </body>
        </text>
    </TEI>
            """
    return Response(entry_text, mimetype='text/xml')

@app.route('/dict/xml_redirect/<string:xml_id>', methods=['GET', 'POST'])
def redirect_to_entry(xml_id):
    #if Units.query.filter_by(xml_id=xml_id, dummy=0).join(Language_assignment, Units.unit_id==Language_assignment.unit_id).filter(Language_assignment.lang_id==198).first():
    if Units.query.filter_by(xml_id=xml_id, dummy=0).first():
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(Units.query.filter_by(xml_id=xml_id, dummy=0).first().unit_id)
        return redirect(url_for('entry', unit_id=unit_id))
    else:
        return Amend.flash(f'Статьи с ID <em>{xml_id}</em> не найдено.', 'danger', url_for('search'))

@app.route('/<string:en>/dict/map/<string:unit_id>', methods=['GET', 'POST'])
@app.route('/dict/map/<string:unit_id>', methods=['GET', 'POST'])
def map_for_entry(unit_id, en=''):
    if en == 'en':
        mentioned = {unit.target_id: (Language_assignment.query.filter_by(unit_id=unit.target_id).first().lang_id,
                                      [Meanings.query.filter_by(unit_id=unit.target_id).first().meaning_en for m in [1] if
                                       Meanings.query.filter_by(
                                           unit_id=unit.target_id).first() and Meanings.query.filter_by(
                                           unit_id=unit.target_id).first().meaning_en != None]) for unit in
                     Unit_links.query.filter_by(unit_id=unit_id, type=2)}
    else:
        mentioned = {unit.target_id: (Language_assignment.query.filter_by(unit_id=unit.target_id).first().lang_id,
                                      [Meanings.query.filter_by(unit_id=unit.target_id).first().meaning for m in [1] if
                                       Meanings.query.filter_by(
                                           unit_id=unit.target_id).first() and Meanings.query.filter_by(
                                           unit_id=unit.target_id).first().meaning != None]) for unit in
                     Unit_links.query.filter_by(unit_id=unit_id, type=2)}

    m = folium.Map(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: US National Park Service",
        location=[42.98, 44.61],
        zoom_start=4)
    folium.Marker(location=[42.98, 44.61], icon=folium.Icon(color='red')).add_to(m)

    clusters = {}
    for lang in Languages.query.all():
        clusters[lang.lang_en] = MarkerCluster(name=lang.lang_en).add_to(m)
    for token in mentioned:
        if mentioned.get(token)[1]:
            gloss = f'‘{mentioned.get(token)[1][0]}’'
        else:
            gloss = ''
        if Languages.query.get(mentioned.get(token)[0]).latitude != -99 and not (Languages.query.get(mentioned.get(token)[0]).ISO == "os" or Languages.query.get(mentioned.get(token)[0]).ISO.startswith("os-")):
            folium.Marker(location=[Languages.query.get(mentioned.get(token)[0]).latitude, Languages.query.get(mentioned.get(token)[0]).longitude],
                          tooltip=folium.Tooltip(text=Forms.query.filter_by(unit_id=token).first().latin, permanent=True),
                          popup=folium.Popup(
                              html=Languages.query.get(mentioned.get(token)[0]).lang_en + " <i>" + Forms.query.filter_by(unit_id=token).first().latin + "</i> " + gloss,
                              show=False)).add_to(clusters[Languages.query.get(mentioned.get(token)[0]).lang_en])
    # folium.LayerControl().add_to(map)

    #m.save("Ossetic" + url_for('static', filename=f'temp' + f"/map_{unit_id}.html"))
    #m.save(f"map_{unit_id}.html")
    return Response(m._repr_html_(), mimetype='text/html')


