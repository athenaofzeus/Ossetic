from Ossetic import app
from flask import render_template, request, url_for, Markup, session
from math import ceil
from Ossetic.models import Forms, Units, Glosses, Entry_logs, Examples, Users, Label_names, Form_labels, Unit_labels,\
    Grammar_labels, Taxonomic_labels, Meaning_labels, Meanings, Parts_of_speech, Topological_labels, Mereological_labels,\
    Languages, Language_assignment
from Ossetic.supplement import Amend, Check
from re import sub, IGNORECASE, search
from itsdangerous import URLSafeSerializer
import sqlite3, os
from urllib.parse import unquote

@app.route('/dict/search/<string:langs>/<string:query>/<string:type>/<string:lengths>/<string:param>/',
           methods=['GET'])
@app.route('/dict/search/<string:langs>/<string:query>/<string:type>/<string:lengths>/<string:param>/<int:page>/',
           methods=['GET'])
@app.route('/<string:en>/dict/search/<string:langs>/<string:query>/<string:type>/<string:lengths>/<string:param>/',
           methods=['GET'])
@app.route('/<string:en>/dict/search/<string:langs>/<string:query>/<string:type>/<string:lengths>/<string:param>/<int:page>/',
           methods=['GET'])
def results(query, param, type, lengths, langs, page=1, en=''):
    Check.update()
    def sort_by_forms(unit_ids):
        forms = list()
        for id in unit_ids:
            if Forms.query.filter_by(unit_id=id, gloss_id=0).first():
                forms.append(f'{Forms.query.filter_by(unit_id=id, gloss_id=0).first().latin}_{id}')
            elif Forms.query.filter_by(unit_id=id).first():
                forms.append(f'{Forms.query.filter_by(unit_id=id).first().latin}_{id}')
        forms.sort()
        return [int(f.split('_')[-1]) for f in forms]

    query = unquote(query)
    if len(query) < 3 and type != 'full' and not en:
        return Amend.flash(f'Запрос <code>{query}</code> слишком короток.', 'warning', url_for('search'))
    elif len(query) < 3 and type != 'full' and en == 'en':
        return Amend.flash(f'The query <code>{query}</code> is too short.', 'warning', url_for('search', en='en'))
    original_param = param
    original_query = query
    langs = tuple([int(l) for l in langs.split(',') if Languages.query.filter_by(lang_id=int(l)).first()])
    if len(langs) == 1:
        langs = (langs[0], langs[0])
    if request.method == 'GET':
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "abaev.db"))
        conn.create_function("REGEXP", 2, Amend.regexp)
        cur = conn.cursor()
        output = {}
        if param == 'forms':
            query = Amend.create_query(query, lengths=lengths, mapping=True, type=type, langs=langs)
            res = cur.execute(
                f'''
                SELECT Forms.unit_id, latin FROM Forms 
                JOIN Units ON Forms.unit_id == Units.unit_id
                JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id
                WHERE latin REGEXP ? AND gloss_id NOT IN (5, 22) AND Units.status == 1 AND Units.parent_id IS NULL
                AND Language_assignment.lang_id IN {langs}
                ''',
                (query,)
            )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди форм'
            where_found_en = 'within forms'
        elif param == 'meaning':
            query = Amend.create_query(query, lengths=lengths, mapping=True, type=type, langs=langs)
            if en == 'en':
                area = 'meaning_en'
            else:
                area = 'meaning'
            res = cur.execute(
                f'''
                SELECT Meanings.unit_id FROM Meanings 
                JOIN Units ON Meanings.unit_id == Units.unit_id
                JOIN Language_assignment ON Meanings.unit_id == Language_assignment.unit_id
                WHERE {area} REGEXP ? AND Units.status == 1 AND Language_assignment.lang_id IN {langs}
                ''',
                [(query)]
            )
            output = set()
            for r in res.fetchall():
                r = r[0]
                if Units.query.get(r).parent_id:
                    output.add(Units.query.get(r).parent_id)
                else:
                    output.add(r)
            where_found = 'среди значений'
            where_found_en = 'within senses'
        elif param == 'example':
            query = Amend.create_query(query, lengths=lengths, mapping=True, type=type, langs=langs)
            res = cur.execute(
                f'''
                SELECT Units.unit_id FROM Examples 
                JOIN Meanings ON Examples.meaning_id == Meanings.meaning_id 
                JOIN Units ON Meanings.unit_id == Units.unit_id
                JOIN Language_assignment ON Meanings.unit_id == Language_assignment.unit_id
                WHERE example REGEXP ? and Units.parent_id IS NULL AND Units.status == 1
                AND Language_assignment.lang_id IN {langs}
                ''',
                [(query)]
            )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди примеров'
            where_found_en = 'within examples'
        elif param == 'idioms':
            query, alternant = Amend.create_query(query, lengths=lengths, mapping=True, type=type, langs=langs)
            res = cur.execute(
                f'''SELECT Units.parent_id FROM Forms
                    JOIN Units ON Forms.unit_id == Units.unit_id
                    JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id
                    WHERE latin REGEXP ?
                    AND Forms.gloss_id == 5 AND Language_assignment.lang_id IN {langs}
                    ''',
                [(query)]
            )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди идиом и дериватов'
            where_found_en = 'within idioms and derivates'
        elif param == 'cvs':
            query, alternant = Amend.create_query(query, lengths=lengths, mapping=True, type=type, langs=langs)
            res = cur.execute(
                f'''SELECT Units.parent_id FROM Forms
                    JOIN Units ON Forms.unit_id == Units.unit_id 
                    JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id
                    WHERE latin REGEXP ? AND Forms.gloss_id == 22 
                    AND Language_assignment.lang_id IN {langs}
                    ''',
                [(query)]
            )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди сложных глаголов'
            where_found_en = 'within compound verbs'
        elif param == 'full_entry':
            query = Amend.create_query(query, lengths=lengths, mapping=True, type=type, langs=langs)
            if en == 'en':
                area = 'full_entry_en'
            else:
                area = 'full_entry'
            res = cur.execute(
                f'''
                SELECT Units.unit_id FROM Units 
                JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                WHERE {area} REGEXP ? and parent_id IS NULL AND Units.status == 1
                AND Language_assignment.lang_id IN {langs}
                ''',
                [(query)]
            )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди полного текста статей'
            where_found_en = 'within original entry texts'
        if type == 'full':
            type_message = '(указано слово целиком) '
            type_message_en = '(the query is a complete word) '
        elif type == 'sub':
            type_message = ''
            type_message_en = ''
        if lengths == 'l':
            lengths_message = '; диакритики из запроса учтены'
            lengths_message_en = '; diacritics matter'
        elif lengths == 'nl' and original_param == 'shughni':
            lengths_message = '; диакритики из запроса <b>не</b>&nbsp;учтены'
            lengths_message_en = '; diacritics <b>do not</b>&nbsp;matter'
        else:
            lengths_message = ''
            lengths_message_en = ''
        languages = ', '.join({Languages.query.get(l).lang_en for l in langs if Languages.query.filter_by(lang_id=l).first()})
        ortho_message = f'<br><span>Языки: {languages}.</span>'
        ortho_message_en = f'<br><span>Languages: {languages}.</span>'
        message = f'''<span>Результаты поиска по запросу <code>{original_query}</code> 
        {type_message}{where_found}{lengths_message}.{ortho_message}'''
        message_en = f'''<span>Results for the query <code>{original_query}</code> 
                {type_message_en}{where_found_en}{lengths_message_en}.{ortho_message_en}'''
        if not output and not en:
            return Amend.flash(f'По запросу <code>{original_query}</code> {type_message}{where_found} \
            ничего не найдено{lengths_message}.{ortho_message}', 'warning', url_for('search'))
        elif not output and en == 'en':
            return Amend.flash(f'The query <code>{original_query}</code> {type_message_en}{where_found_en} \
            has yielded no results{lengths_message_en}.{ortho_message_en}', 'warning', url_for('search', en='en'))
        output = sort_by_forms(output)
        message += f'<hr><span>Количество найденных лексем&nbsp;— {len(output)}.<span>'
        message_en += f'<hr><span>Lexemes found: {len(output)}.<span>'
        if ceil(len(output) / 20) < page and len(output) > 20:
            return Check.page()
        if len(output) > page*20:
            has_next = True
        else:
            has_next = False
        if page > 1:
            has_prev = True
        else:
            has_prev = False
        page_of_units = {'units': sort_by_forms(output[(page-1)*20:(page-1)*20+20]),
                         'has_next': has_next,
                         'has_prev': has_prev
                         }
        if en == 'en':
            return render_template('results_page_en.html',
                               unit_ids=page_of_units.get('units'),
                               param=param,
                               type=type,
                               lengths=lengths,
                               original_query=original_query,
                               query=query,
                               page_of_units=page_of_units,
                               page=page,
                               message=message_en,
                               Markup=Markup,
                               Forms=Forms,
                               Units=Units,
                               Check=Check,
                               Glosses=Glosses,
                               Label_names=Label_names,
                               Grammar_labels=Grammar_labels,
                               Parts_of_speech=Parts_of_speech,
                               app=app,
                               URLSafeSerializer=URLSafeSerializer,
                               Entry_logs=Entry_logs,
                               Examples=Examples,
                               Meanings=Meanings,
                               Amend=Amend,
                               Languages=Languages,
                               Language_assignment=Language_assignment,
                               langs=','.join([str(l) for l in langs])
                               )
        else:
            return render_template('results_page.html',
                               unit_ids=page_of_units.get('units'),
                               param=param,
                               type=type,
                               lengths=lengths,
                               original_query=original_query,
                               query=query,
                               page_of_units=page_of_units,
                               page=page,
                               message=message,
                               Markup=Markup,
                               Forms=Forms,
                               Units=Units,
                               Check=Check,
                               Glosses=Glosses,
                               Label_names=Label_names,
                               Grammar_labels=Grammar_labels,
                               Parts_of_speech=Parts_of_speech,
                               app=app,
                               URLSafeSerializer=URLSafeSerializer,
                               Entry_logs=Entry_logs,
                               Examples=Examples,
                               Meanings=Meanings,
                               Amend=Amend,
                               Languages=Languages,
                               Language_assignment=Language_assignment,
                               langs=','.join([str(l) for l in langs])
                               )

@app.route('/dict/extended_search', methods=['GET', 'POST'])
def extended_search():
    params={'minimal_pairs': request.form.get('minimal_pairs')}
    Check.update()
    if not session.get('user'):
        return Check.login()
    user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
    if Users.query.get(user_id).role_id not in [2, 3]:
        return Check.status()
    def sort_by_forms(unit_ids):
        forms = {}
        for id in unit_ids:
            if Forms.query.filter_by(unit_id=id, gloss_id=20).first():
                forms.update({Forms.query.filter_by(unit_id=id, gloss_id=20).first().latin: id})
            elif Forms.query.filter_by(unit_id=id, gloss_id=3).first():
                forms.update({Forms.query.filter_by(unit_id=id, gloss_id=3).first().latin: id})
            elif Forms.query.filter_by(unit_id=id).first():
                forms.update({Forms.query.filter_by(unit_id=id).first().latin: id})
        forms_sorted = sorted(forms.keys())
        return [forms[f] for f in forms_sorted]

    def regexp(expr, item):
        if item:
            return search(expr, item, flags=IGNORECASE) is not None

    if request.method == 'GET':
        return render_template('extended_search.html',
                               Label_names=Label_names,
                               Parts_of_speech=Parts_of_speech,
                               Markup=Markup,
                               Languages=Languages)
    if request.method == 'POST':
        query = rf"{request.form.get('query_text')}".replace(r'"', r"/")
        param = request.form.get('query_area')
        langs = tuple([int(l) for l in request.form.to_dict(flat=True).get('languages').split(',') if Languages.query.filter_by(lang_id=int(l)).first()])
        if len(langs) == 1:
            langs = (langs[0], langs[0])
        if len(query) < 1:
            return Amend.flash(f'Запрос <code>{query}</code> слишком короток.', 'warning', url_for('extended_search'))
        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "database3.0.db"))
        conn.create_function("REGEXP", 2, regexp)
        cur = conn.cursor()
        output = {}
        if [l for l in request.form if l.startswith('l_')]:
            label_ids = tuple([l[1:] for l in request.form if l.startswith('l_')])
        else:
            label_ids = []
        if len(label_ids) == 1:
            label_ids = (label_ids[0], label_ids[0])
        if param == 'shughni':
            if label_ids:
                res = cur.execute(
                        f'''
                        SELECT Units.unit_id, latin FROM Forms 
                        JOIN Units ON Forms.unit_id == Units.unit_id
                        JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                        JOIN Form_labels ON Forms.form_id == Form_labels.form_id
                        WHERE latin REGEXP "{query}" AND gloss_id NOT IN (5, 22) AND label_id IN {label_ids}
                        AND Language_assignment.lang_id IN {langs}
                        '''
                    )
                [output.update({f[0]: None}) for f in res.fetchall()]
                for id in {uid[0] for uid in Unit_labels.query.join(Forms, Unit_labels.unit_id==Forms.unit_id).filter(Unit_labels.label_id.in_([int(l.split('_')[-1]) for l in request.form if l.startswith('l_')])).with_entities(Unit_labels.unit_id)}:
                    if id not in output:
                        output.update({id: None})
            else:
                res = cur.execute(
                    f'''
                    SELECT Units.unit_id, latin FROM Forms 
                    JOIN Units ON Forms.unit_id == Units.unit_id
                    JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                    WHERE latin REGEXP "{query}" AND gloss_id NOT IN (5, 22)
                    AND Language_assignment.lang_id IN {langs}
                    '''
                )
                [output.update({f[0]: None}) for f in res.fetchall()]
            if request.form.get('pos'):
                pos_id = int(request.form.get('pos'))
                for id in list(output):
                    if (pos_id,) not in [i for i in Meanings.query.filter_by(unit_id=id).with_entities(Meanings.pos_id)]:
                        del output[id]
            where_found = 'среди форм'
        elif param == 'example':
            if label_ids:
                res = cur.execute(
                    f'''
                    SELECT Units.unit_id FROM Examples  
                    JOIN Meanings ON Examples.meaning_id == Meanings.meaning_id 
                    JOIN Units ON Meanings.unit_id == Units.unit_id
                    JOIN Example_labels ON Examples.example_id == Example_labels.example_id
                    JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                    WHERE example REGEXP "{query}" and Units.parent_id IS NULL AND Units.status == 1 AND label_id IN ({label_ids})
                    AND Language_assignment.lang_id IN {langs}
                    '''
                )
            else:
                res = cur.execute(
                    f'''
                    SELECT Units.unit_id FROM Examples  
                    JOIN Meanings ON Examples.meaning_id == Meanings.meaning_id 
                    JOIN Units ON Meanings.unit_id == Units.unit_id 
                    JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                    WHERE example REGEXP "{query}" and Units.parent_id IS NULL AND Units.status == 1
                    AND Language_assignment.lang_id IN {langs}
                    '''
                )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди примеров'
        elif param == 'meaning':
            if label_ids:
                res = cur.execute(
                    f'''
                    SELECT Meanings.unit_id FROM Meanings 
                    JOIN Units ON Meanings.unit_id == Units.unit_id 
                    JOIN Meaning_labels ON Meanings.meaning_id == Meaning_labels.meaning_id
                    JOIN Language_assignment ON Meanings.unit_id == Language_assignment.unit_id
                    WHERE meaning REGEXP "{query}" and Units.parent_id IS NULL AND label_id IN ({label_ids})
                    AND Language_assignment.lang_id IN {langs}
                    '''
                )
            else:
                res = cur.execute(
                    f'''
                    SELECT Meanings.unit_id FROM Meanings 
                    JOIN Units ON Meanings.unit_id == Units.unit_id 
                    JOIN Language_assignment ON Meanings.unit_id == Language_assignment.unit_id
                    WHERE meaning REGEXP "{query}" and Units.parent_id IS NULL
                    AND Language_assignment.lang_id IN {langs}
                    '''
                )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди значений'
        elif param == 'idioms':
            if label_ids:
                res = cur.execute(
                    f'''SELECT Units.parent_id FROM Forms
                        JOIN Units ON Forms.unit_id == Units.unit_id 
                        JOIN Form_labels ON Forms.form_id == Form_labels.form_id
                        JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id
                        WHERE latin REGEXP "{query}" AND Forms.gloss_id == 5 AND label_id IN ({label_ids})
                        AND Language_assignment.lang_id IN {langs}
                        '''
                )
            else:
                res = cur.execute(
                    f'''SELECT Units.parent_id FROM Forms
                    JOIN Units ON Forms.unit_id == Units.unit_id 
                    JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id
                    WHERE latin REGEXP "{query}" AND Forms.gloss_id == 5
                    AND Language_assignment.lang_id IN {langs}
                    '''
                )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди идиом и устойчивых сочетаний'
        elif param == 'cvs':
            if label_ids:
                res = cur.execute(
                    f'''SELECT Units.parent_id FROM Forms
                        JOIN Units ON Forms.unit_id == Units.unit_id
                        JOIN Form_labels ON Forms.form_id == Form_labels.form_id 
                        JOIN Language_assignment ON Forms.unit_id == Language_assignment.unit_id
                        WHERE latin REGEXP "{query}" AND Forms.gloss_id == 22 AND label_id IN ({label_ids})
                        AND Language_assignment.lang_id IN {langs}
                        '''
                )
            else:
                res = cur.execute(
                    f'''SELECT Units.parent_id FROM Forms
                        JOIN Units ON Forms.unit_id == Units.unit_id
                        JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                        WHERE latin REGEXP "{query}" AND Forms.gloss_id == 22
                        AND Language_assignment.lang_id IN {langs}
                        '''
                )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди сложных глаголов'
        elif param == 'full_entry':
            res = cur.execute(
                f'''
                SELECT Units.unit_id FROM Units 
                JOIN Language_assignment ON Units.unit_id == Language_assignment.unit_id
                WHERE full_entry REGEXP "{query}" and parent_id IS NULL
                AND Language_assignment.lang_id IN {langs}
                '''
            )
            [output.update({f[0]: None}) for f in res.fetchall()]
            where_found = 'среди полного текста статей'
        languages = ', '.join(
            {Languages.query.get(l).lang for l in langs if Languages.query.filter_by(lang_id=l).first()})
        message = f'''<span>Результаты поиска по запросу <code>{query}</code> {where_found}.<br>Языки: {languages}.</span>'''
        if not output:
            return Amend.flash(f'По запросу <code>{query}</code> {where_found} \
            ничего не найдено.', 'warning', url_for('extended_search'))
        message += f'<hr><span>Количество найденных лексем&nbsp;— {len(output)}.<span>'
        return render_template('extended_results_page.html',
                               unit_ids=sort_by_forms(output.keys()),
                               query=query,
                               message=message,
                               Markup=Markup,
                               Forms=Forms,
                               Units=Units,
                               Check=Check,
                               Glosses=Glosses,
                               app=app,
                               URLSafeSerializer=URLSafeSerializer,
                               Entry_logs=Entry_logs,
                               Examples=Examples,
                               Amend=Amend,
                               params=params
                               )

@app.route('/dict/listing/<string:type>/<string:label_id>', methods=['GET', 'POST'])
def listing(type, label_id):
    Check.update()
    if not Label_names.query.get(label_id):
        return Amend.flash('Ничего не найдено.', 'warning', url_for('search'))
    params = {}
    def sort_by_forms(unit_ids):
        forms = {}
        for id in unit_ids:
            if Forms.query.filter_by(unit_id=id, gloss_id=20).first():
                forms.update({Forms.query.filter_by(unit_id=id, gloss_id=20).first().latin: id})
            elif Forms.query.filter_by(unit_id=id, gloss_id=3).first():
                forms.update({Forms.query.filter_by(unit_id=id, gloss_id=3).first().latin: id})
            elif Forms.query.filter_by(unit_id=id).first():
                forms.update({Forms.query.filter_by(unit_id=id).first().latin: id})
        forms_sorted = sorted(forms.keys())
        return [forms[f] for f in forms_sorted]

    if request.method == 'GET':
        if type in ['taxonomy', '3']:
            output = sort_by_forms([u[-1] for u in Taxonomic_labels.query.filter_by(label_id=label_id).with_entities(Taxonomic_labels.unit_id)])
            query = Label_names.query.get(label_id).label
            message = Markup(f'Поиск по таксономической помете <abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{Label_names.query.get(label_id).decode}"><b>{Label_names.query.get(label_id).label}</b></abbr>. Результатов: {len(output)}.')
        elif type in ['topology', '4']:
            output = sort_by_forms([u[-1] for u in Topological_labels.query.filter_by(label_id=label_id).with_entities(Topological_labels.unit_id)])
            query = Label_names.query.get(label_id).label
            message = Markup(f'Поиск по топологической помете <abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{Label_names.query.get(label_id).decode}"><b>{Label_names.query.get(label_id).label}</b></abbr>. Результатов: {len(output)}.')
        elif type in ['mereology', '5']:
            output = sort_by_forms([u[-1] for u in Mereological_labels.query.filter_by(label_id=label_id).with_entities(Mereological_labels.unit_id)])
            query = Label_names.query.get(label_id).label
            message = Markup(f'Поиск по мереологической помете <abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{Label_names.query.get(label_id).decode}"><b>{Label_names.query.get(label_id).label}</b></abbr>. Результатов: {len(output)}.')
        elif type == 'forms_and_meanings' or type == '1':
            if not session.get('user'):
                return Check.login()
            user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
            if Users.query.get(user_id).role_id not in [2, 3]:
                return Check.status()
            res1 = [u[-1] for u in
                      Unit_labels.query.filter_by(label_id=label_id).with_entities(Unit_labels.unit_id)]
            res2 = [Forms.query.get(u[-1]).unit_id for u in
                      Form_labels.query.filter_by(label_id=label_id).with_entities(Form_labels.form_id) if Forms.query.get(u[-1])]
            res3 = [Meanings.query.get(u[-1]).unit_id for u in
                       Meaning_labels.query.filter_by(label_id=label_id).with_entities(Meaning_labels.meaning_id) if Meanings.query.get(u[-1])]
            output = sort_by_forms(list({u for u in res1 + res2 + res3}))
            query = Label_names.query.get(label_id).label
            message = Markup(
                f'Поиск по помете <abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{Label_names.query.get(label_id).decode}"><b>{Label_names.query.get(label_id).label}</b></abbr>. Результатов: {len(output)}.')
        elif type == 'grammar' or type == '2':
            if not session.get('user'):
                return Check.login()
            user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
            if Users.query.get(user_id).role_id not in [2, 3]:
                return Check.status()
            output = sort_by_forms([Meanings.query.get(u[-1]).unit_id for u in
                      Grammar_labels.query.filter_by(label_id=label_id).with_entities(Grammar_labels.meaning_id) if Meanings.query.get(u[-1])])
            query = Label_names.query.get(label_id).label
            message = Markup(
                f'Поиск по грамматической помете <abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{Label_names.query.get(label_id).decode}"><b>{Label_names.query.get(label_id).label}</b></abbr>. Результатов: {len(output)}.')
        if not output:
            return Amend.flash('Ничего не найдено.', 'warning', url_for('search'))
        return render_template('extended_results_page.html',
                               unit_ids=output,
                               query=query,
                               message=message,
                               Markup=Markup,
                               Forms=Forms,
                               Units=Units,
                               Check=Check,
                               Glosses=Glosses,
                               app=app,
                               URLSafeSerializer=URLSafeSerializer,
                               Entry_logs=Entry_logs,
                               Examples=Examples,
                               Amend=Amend,
                               params=params)