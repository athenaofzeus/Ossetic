from markdown import markdown
from flask import session, url_for, Markup, redirect, flash
from Ossetic.models import db, Users, Units, Forms, Examples, Example_labels, Form_labels, Meanings, Entry_logs,\
    Label_names, Tasks, Meaning_labels, Unit_labels, Unit_pictures, Unit_comments, Taxonomic_labels, Topological_labels,\
    Mereological_labels, Unit_links, Language_assignment
from flask_mail import Mail, Message
from Ossetic import app
from bs4 import BeautifulSoup
from time import strftime, gmtime
from calendar import timegm
from re import sub, IGNORECASE, search
from json import dumps, loads
from itsdangerous import URLSafeSerializer
#from Levenshtein import distance

mail = Mail(app)

class Amend:
    def task_status(self):
        self = int(self)
        if self == 1:
            return '<span class="text-warning">Назначена</span>'
        elif self == 2:
            return '<span class="text-secondary">Выполнена</span>'
        elif self == 3:
            return '<span class="text-success">Исполняется</span>'
        elif self == 4:
            return '<span class="text-danger">Отклонена</span>'

    def anti_html(self):
        if self:
            return BeautifulSoup(self, features='html.parser').get_text()

    def md(self, html=False, delete_p=True, delete_br=True):
        if not self:
            return self
        if self:
            if html:
                string = markdown(self, extensions=['nl2br'])
            else:
                string = markdown(Amend.anti_html(self), extensions=['nl2br'])
            if delete_p:
                for tag in ['<p>', '</p>']:
                    string = string.replace(tag, '')
            if delete_br:
                for tag in ['<br />', '<br />']:
                    string = string.replace(tag, '')
            string = string.replace('<img', '<img class="img-fluid"').replace('--', '—')
            return Markup(string)

    def username(self, link=True):
        role_id = Users.query.get(self).role_id
        if role_id == 2:
            if link:
                username = Markup(f"""<a href="{url_for('profile', user_id=self)}" class="link-success">{Users.query.get(self).username}</a>""")
            else:
                username = Markup(f"""<span class="text-success">{Users.query.get(self).username}</span>""")
        elif role_id == 3:
            if link:
                username = Markup(f"""<a href="{url_for('profile', user_id=self)}" class="link-danger">{Users.query.get(self).username}</a>""")
            else:
                username = Markup(f"""<span class="text-danger">{Users.query.get(self).username}</span>""")
        else:
            if link:
                username = Markup(f"""<a href="{url_for('profile', user_id=self)}" class="link-secondary">{Users.query.get(self).username}</a>""")
            else:
                username = Markup(f"""<span class="text-secondary">{Users.query.get(self).username}</span>""")

        return username

    def flash(self, type, url=None):
        flash(Markup(self), f'alert alert-{type}')
        if url:
            return redirect(url)

    def cypher_unit(self):
        return URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(self)

    def cypher_user(self):
        return URLSafeSerializer(app.config['SECRET_KEY'], salt='login').dumps(self)

    def datetime(self):
        return strftime('%d.%m.%Y %H:%M', gmtime(self+10800))

    def spaces(self):
        while self.endswith(' ') or self.endswith(' ') or self.endswith(',') or self.endswith(';'):
            self = self[:-1]
        while self.startswith(' ') or self.startswith(' ') or self.startswith(',') or self.startswith(';'):
            self = self[1:]
        return self

    def mark(what, where):
        what = what.replace(r'([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|^)', '').replace(r'([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|$)', '')
        #where = sub(r'(-|=)', '(-|=|)', where)
        #print(what, where) #кашкаш -- не выделяет
        if not where:
            where = ''
        return Markup(sub(what, r"<mark class='p-0'>\1</mark>", where, flags=IGNORECASE))

    def entry(self, link=True, new_window=False, en=''):
        unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(self)
        if not Units.query.get(self):
            return None
        if Units.query.get(self).parent_id:
            self = Units.query.get(self).parent_id
            unit_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='entry').dumps(self)
        if Units.query.get(self):
            if new_window:
                add = ', target="_blank"'
            else:
                add = ''
            if link:
                entry = Markup(f"""<a href="{url_for('entry', unit_id=unit_id, en=en)}" class="link-primary"{add}>{Check.main_form(self)}</a>""")
            else:
                entry = Markup(f"""<span class="text-dark"{add}>{Check.main_form(self)}</span>""")
        else:
            return None
        return entry

    def delete(self, id):
        if self == 'e':
            Examples.query.filter_by(example_id=id).delete()
            Example_labels.query.filter_by(example_id=id).delete()
        elif self == 'f':
            Forms.query.filter_by(form_id=id).delete()
            Form_labels.query.filter_by(form_id=id).delete()
        elif self == 'm':
            Meanings.query.filter_by(meaning_id=id).delete()
            Meaning_labels.query.filter_by(meaning_id=id).delete()
            for e in Examples.query.filter_by(meaning_id=id).all():
                Example_labels.query.filter_by(example_id=e.example_id).delete()
            Examples.query.filter_by(meaning_id=id).delete()
        elif self == 'u':
            Units.query.filter_by(unit_id=id).delete()
            for f in Forms.query.filter_by(unit_id=id).all():
                Forms.query.filter_by(form_id=f.form_id).delete()
                Form_labels.query.filter_by(form_id=f.form_id).delete()
            for m in Meanings.query.filter_by(unit_id=id).all():
                Meaning_labels.query.filter_by(meaning_id=m.meaning_id).delete()
                for e in Examples.query.filter_by(meaning_id=m.meaning_id).all():
                    Example_labels.query.filter_by(example_id=e.example_id).delete()
                Examples.query.filter_by(meaning_id=m.meaning_id).delete()
            Meanings.query.filter_by(unit_id=id).delete()
            Entry_logs.query.filter_by(unit_id=id).delete()
            Unit_comments.query.filter_by(unit_id=id).delete()
            Unit_pictures.query.filter_by(unit_id=id).delete()
            Unit_labels.query.filter_by(unit_id=id).delete()
            Language_assignment.query.filter_by(unit_id=id).delete()
            Unit_links.query.filter_by(unit_id=id).delete()
            Unit_links.query.filter_by(target_id=id).delete()
            Taxonomic_labels.query.filter_by(unit_id=id).delete()
            Topological_labels.query.filter_by(unit_id=id).delete()
            Mereological_labels.query.filter_by(unit_id=id).delete()
        db.session.commit()

    def see_also(self, en=''):
        if not Unit_links.query.filter_by(unit_id=self).all():
            return ''
        result = '<ul class="list-group list-group-flush">'
        for link in Unit_links.query.filter_by(unit_id=self).order_by(Unit_links.type.asc(), Unit_links.rank.asc()).all():
            if link.type == 1:
                if Language_assignment.query.filter_by(unit_id=link.target_id).first().lang_id == 198:
                    if en == 'en':
                        type = '(Digor)'
                    else:
                        type = '(дигорское)'
                elif Language_assignment.query.filter_by(unit_id=link.target_id).first().lang_id == 199:
                    if en == 'en':
                        type = '(Iron)'
                    else:
                        type = '(иронское)'
            elif link.type == 2:
                if en == 'en':
                    type = '(mentioned)'
                else:
                    type = '(упомянуто)'
            elif link.type == 3:
                type = '(антоним)'
            elif link.type == 4:
                type = '(омоним)'
            elif link.type == 5:
                type = '(дериват)'
            elif link.type == 6:
                type = '(когнат)'
            elif link.type == 7:
                type = '(гипероним)'
            elif link.type == 8:
                type = '(гипоним)'
            elif link.type == 9:
                type = '(когипоним)'
            elif link.type == 10:
                type = '(конверсив)'
            type = f' <em>{type}</em>'
            if link.target_id:
                result += f'<li class="list-group-item px-0">🔶 <b>{Amend.entry(link.target_id, new_window=True)}{type}</b></li>'
        result += '</ul>'
        return Markup(result)

    def create_query(query, lengths=None, mapping=True, alternant=None, type='full', langs=[1]):
        query = sub(r'''[!\?\\[\]\"\':;&$#@=\|\-́]''', '', query)
        query = query.replace('.', '\.').replace('(', '\(').replace(')', '\)')
        query = sub('^ +', '', query)
        query = sub(' +$', '', query)
        if lengths == 'l':
            query = f'({query})'
            if type == 'full':
                query = rf'(([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|^)({query})([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|$))'
            elif 'sub' in type:
                query = rf'({query})'
        elif lengths == 'nl' and mapping:
            mapping_c = ['(а́|ā(?!́)|а(?!́)|á|ā́)', '(е́|ê|ę|е(?!́)|ê(?!́)|ế|ё|ё(?!́))', '(и́|и(?!́)|ӣ(?!́)|ӣ́)',
                         '(ǫ|о́|о(?!́))',
                         '(ӯ|у(?!̊)|у̊|у(?!́)|у́)', '(к|қ)', '(х(?!̌)|ӽ|х̌)', '(ч|ҷ)', '(ɣ(?!̌)|ɣ̌)', '(г|ғ)']
            mapping_l = ['(ā|á|a(?!́))', '(é|ế|e(?!́)|ê(?!́))', '(í|ī|i(?!́))', '(ú|ū|ů|u(?!́))', '(x(?!̌)|x̌)',
                         '(ɣ(?!̌)|ɣ̌)', '(j(?!̌)|ǰ|ǰ)']
            for m in mapping_l:
                query = sub(m, m, query)
            if type == 'full':
                query = rf'(([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|^)({query})([ \.!\?\\,\(\)\[\]\"\':;&\$^#@=\|\n]|$))'
            elif 'sub' in type:
                query = rf'({query})'
        if type == 'sub_beginning':
            query = f'^{query}'
        return (query)

    def regexp(expr, item):
        if item:
            item = item.replace('-', '').replace('=', '')
            return search(expr, item, flags=IGNORECASE) is not None

class Check():
    def main_form(unit_id):
        if not Forms.query.filter_by(unit_id=unit_id).filter(Forms.gloss_id.in_((3, 20))).order_by(Forms.form_id.asc()).first():
            if not Forms.query.filter_by(unit_id=unit_id).order_by(Forms.form_id.asc()).first():
                return 'None'
            return Forms.query.filter_by(unit_id=unit_id).order_by(Forms.form_id.asc()).first().latin
        return Forms.query.filter_by(unit_id=unit_id).filter(Forms.gloss_id.in_((3, 20))).order_by(Forms.form_id.asc()).first().latin
    def time(self=None):
        return timegm(gmtime())
    def update(self=None):
        if session.get('user'):
            session['new_tasks'] = 0
            user_id = URLSafeSerializer(app.config['SECRET_KEY'], salt='login').loads(session.get('user'))
            for t in Tasks.query.filter_by(status=1).all():
                if t.assignees and str(user_id) in t.assignees.split(','):
                    session['new_tasks'] = 1
                    break
            if Users.query.get(user_id).role_id not in [2, 3]:
                return redirect(url_for('login'))
        return None

    def status(self=None):
        return Amend.flash('У вас недостаточно прав для этого действия.', 'danger', url_for('profile'))
    def login(self=None):
        return Amend.flash('Для выполнения этого действия нужно войти.', 'danger', url_for('login'))
    def page(url='/'):
        return Amend.flash('Такой страницы не существует.', 'danger', url)
    def index(self, list):
        if not list:
            return None
        return list.index(self)
    def len(self):
        return len(self)
    def range(self, max):
        return range(self, max)
    def split(what, by, to_int=False):
        if what and isinstance(what, str):
            if to_int:
                return [int(i) for i in what.split(by)]
            return what.split(by)
        return []
    def str(what):
        if what:
            return str(what)
        return ''
    def int(what):
        if what:
            return int(what)
        return ''
    def set(self):
        dic = {}
        for i in self:
            dic.update({i:0})
        return list(dict(dic))
    def minimal_pair(unit_id):
        counterparts = {
            'b': 'p',
            'p': 'b',
            'd': 't',
            't': 'd',
            'g': 'k',
            'k': 'g',
            'ӡ': 'c',
            'c': 'ӡ',
            'ǰ': 'č',
            'č': 'ǰ',
            'v': 'f',
            'f': 'v',
            'δ': 'θ',
            'θ': 'δ',
            'z': 's',
            's': 'z',
            'ž': 'š',
            'š': 'ž',
            'ɣ̌': 'x̌',
            'x̌': 'ɣ̌',
            'ɣ': 'x',
            'x': 'ɣ'
        }
        output = []
        if Units.query.get(unit_id).type == 'v':
            main_form_id = 3
        elif Units.query.get(unit_id).type == 'nv':
            main_form_id = 20
        main_form = Forms.query.filter_by(unit_id=unit_id, gloss_id=main_form_id).first()
        for f in Forms.query.all():
            if distance(sub('[-=]', '', main_form.latin), f.latin) < 2:
                output.append(f)
        #if self[-1] in counterparts.keys():
            #for i in Check.minimal_pair(Forms.query.filter_by(gloss_id=3, unit_id=self).first().latin).all():

            #return Forms.query.filter_by(latin=self[:-1]+counterparts[self[-1]]).all()
        #else:
            #return []
        return output
    def labels(self, type, tooltips=True):
        if type == 'f':  # form, example or meaning?
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode) for l in
                      Form_labels.query.join(Label_names).filter(Form_labels.form_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        elif type == 'e':
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode) for l in
                      Example_labels.query.join(Label_names).filter(Example_labels.example_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        elif type == 'u':
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode) for l in
                      Unit_labels.query.join(Label_names).filter(Unit_labels.unit_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        elif type == 'm':
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode) for l in
                      Meaning_labels.query.join(Label_names).filter(Meaning_labels.meaning_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        elif type == 'tax':
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode, l.label_id) for l in
                      Taxonomic_labels.query.join(Label_names).filter(Taxonomic_labels.unit_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        elif type == 'top':
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode, l.label_id) for l in
                      Topological_labels.query.join(Label_names).filter(Topological_labels.unit_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        elif type == 'mer':
            labels = [(Label_names.query.get(l.label_id).label, Label_names.query.get(l.label_id).decode, l.label_id) for l in
                      Mereological_labels.query.join(Label_names).filter(Mereological_labels.unit_id == self).order_by(
                          Label_names.rank.asc(), Label_names.label.asc()).all()]
        if labels and type not in ['tax', 'top', 'mer']:
            if tooltips:
                labels = [
                    f'<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><b>{l[0]}</b></abbr>'
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'tax':
            if tooltips:
                labels = [
                    f'''<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><a href="{url_for('listing', type='taxonomy', label_id=l[2])}" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'top':
            if tooltips:
                labels = [
                    f'''<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><a href="{url_for('listing', type='topology', label_id=l[2])}" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        elif labels and type == 'mer':
            if tooltips:
                labels = [
                    f'''<abbr style="font-variant-caps: small-caps" data-bs-toggle="tooltip" title="{l[1]}"><a href="{url_for('listing', type='mereology', label_id=l[2])}" target="_blank">{l[0]}</a></abbr>'''
                    for l in labels]
            else:
                labels = [f'<span style="font-variant-caps: small-caps"><b>{l[0]}</b></span>' for l in labels]
            labels = f"""<span>{', '.join(labels)}</span>"""
        else:
            return ''
        return Markup(labels)

class Emails():
    def send(heading, body, to, reply_to=None):
        msg = Message(heading, recipients=to)
        msg.html = body
        if reply_to:
            msg.reply_to = reply_to
        return mail.send(msg)

class BackUp():
    def row(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def serialise_entry(self):
        output = []
        units = [BackUp.row(Units.query.get(self))]
        for ch in Units.query.filter_by(parent_id=self).all():
            units.append(BackUp.row(ch))
        for u in units:
            unit_id = u.get('unit_id')
            forms = []
            meanings = []
            unit = {'Units': u}
            for f in Forms.query.filter_by(unit_id=unit_id).all():
                forms.append({'Forms': BackUp.row(f), 'Form_labels': [BackUp.row(fl) for fl in f.labels]})
            unit.update({'forms': forms})
            for m in Meanings.query.filter_by(unit_id=unit_id).all():
                examples = []
                for e in m.examples:
                    examples.append(
                        {
                            'Examples': BackUp.row(e),
                            'Example_labels': [BackUp.row(el) for el in e.labels]
                        }
                    )
                meanings.append(
                    {
                        'Meanings': BackUp.row(m),
                        'Meaning_labels': [BackUp.row(ml) for ml in m.labels],
                        'Examples': examples
                    }
                )
            unit.update(
                {
                    'meanings': meanings,
                    'Unit_labels': [BackUp.row(ul) for ul in Unit_labels.query.filter_by(unit_id=unit_id).all()],
                    'Unit_pictures': [BackUp.row(up) for up in Unit_pictures.query.filter_by(unit_id=unit_id).all()],
                    'Unit_comments': [BackUp.row(uc) for uc in Unit_comments.query.filter_by(unit_id=unit_id).all()]
                }
            )
            output.append(unit)
        return dumps(output, ensure_ascii=False)

    '''def rollback(self):
        data = Entry_logs.query.get(self).entry_dump
        data = loads(data)
        for u in data.get('Units'):
            if u.get('parent_id') is None:
                for sub_u in Units.query.filter_by(parent_id=u.get('unit_id')).all():
                    db.session.delete(sub_u)
                for f in Units.query.get(u.get('unit_id')).forms:
                    db.session.delete(f)
                for m in Units.query.get(u.get('unit_id')).meanings:
                    db.session.delete(m)
                Units.query.filter_by(unit_id=u.get('unit_id')).update(
                    dict(
                        type=u.get('type'), full_entry=u.get('full_entry'), gloss=u.get('gloss'),
                        source=u.get('source'), status=u.get('status')
                    )
                )
        db.session.commit()
        for u in data.get('Units'):
            if u.get('parent_id'):
                db.session.add(
                    Units(
                        unit_id=u.get('unit_id'),
                        parent_id=u.get('parent_id'),
                        type=u.get('type'),
                        full_entry=u.get('full_entry'),
                        gloss=u.get('gloss'),
                        source=u.get('source'),
                        status=u.get('status')
                    )
                )
        db.session.commit()
        for f in data.get('Forms'):
            db.session.add(
                Forms(
                    form_id=f.get('form_id'),
                    unit_id=f.get('unit_id'),
                    gloss_id=f.get('gloss_id'),
                    latin=f.get('latin'),
                    cyrillic=f.get('cyrillic'),
                    stem=f.get('stem'),
                    variant=f.get('variant'),
                    source=f.get('source')
                )
            )
        db.session.commit()
        for fl in data.get('Form_labels'):
            db.session.add(
                Form_labels(
                    label_id=fl.get('label_id'),
                    form_id=fl.get('form_id'),
                    source=fl.get('source')
                )
            )
        db.session.commit()
        for m in data.get('Meanings'):
            db.session.add(
                Meanings(
                    meaning_id=m.get('meaning_id'),
                    unit_id=m.get('unit_id'),
                    meaning=m.get('meaning'),
                    source=m.get('source')
                )
            )
        db.session.commit()
        for ml in data.get('Meaning_labels'):
            db.session.add(
                Meaning_labels(
                    label_id=ml.get('label_id'),
                    meaning_id=ml.get('meaning_id'),
                    source=ml.get('source')
                )
            )
        db.session.commit()
        for e in data.get('Examples'):
            db.session.add(
                Examples(
                    example_id=e.get('example_id'),
                    meaning_id=e.get('meaning_id'),
                    example=e.get('example'),
                    translation=e.get('translation'),
                    source=e.get('source')
                )
            )
        db.session.commit()
        for el in data.get('Example_labels'):
            db.session.add(
                Example_labels(
                    label_id=el.get('label_id'),
                    example_id=el.get('example_id'),
                    source=el.get('source')
                )
            )
        db.session.commit()
        return None'''

    def add_dump(self, user_id, event,
                 source):  # 1 -- entry is edited, 2 -- examples are edited, 3 -- entry+examples are rolled back, 4 -- entry is added
        max_logs_per_unit = 16
        seconds_to_separate_logs = 300
        if len(Entry_logs.query.filter_by(unit_id=self).all()) < max_logs_per_unit:
            if Entry_logs.query.filter_by(unit_id=self).order_by(Entry_logs.datetime.desc()).first():
                if Check.time() \
                        - Entry_logs.query.filter_by(unit_id=self).order_by(Entry_logs.datetime.desc()).first().datetime \
                        < seconds_to_separate_logs:
                    if Entry_logs.query.filter_by(unit_id=self).order_by(
                            Entry_logs.datetime.desc()).first().event == event \
                            and Entry_logs.query.filter_by(unit_id=self).order_by(
                        Entry_logs.datetime.desc()).first().user_id == user_id:
                        last = Entry_logs.query.filter_by(unit_id=self).order_by(
                            Entry_logs.datetime.desc()).first().log_id
                        Entry_logs.query.filter_by(log_id=last).update(
                            dict(
                                unit_id=self,
                                user_id=user_id,
                                event=event,
                                datetime=Check.time(),
                                source=source
                            )
                        )
                        db.session.commit()
                    else:
                        db.session.add(
                            Entry_logs(
                                unit_id=self,
                                user_id=user_id,
                                event=event,
                                datetime=Check.time(),
                                source=source
                            )
                        )
                        db.session.commit()
                else:
                    db.session.add(
                        Entry_logs(
                            unit_id=self,
                            user_id=user_id,
                            event=event,
                            datetime=Check.time(),
                            source=source
                        )
                    )
                    db.session.commit()
            else:
                db.session.add(
                    Entry_logs(
                        unit_id=self,
                        user_id=user_id,
                        event=event,
                        datetime=Check.time(),
                        source=source
                    )
                )
                db.session.commit()
        elif len(Entry_logs.query.filter_by(unit_id=self).all()) >= max_logs_per_unit:
            db.session.delete(Entry_logs.query.filter_by(unit_id=self).order_by(Entry_logs.datetime.asc()).first())
            db.session.add(
                Entry_logs(
                    unit_id=self,
                    user_id=user_id,
                    event=event,
                    datetime=Check.time(),
                    source=source
                )
            )
            db.session.commit()