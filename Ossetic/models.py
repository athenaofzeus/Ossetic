from Ossetic import app
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)


class Languages(db.Model):
    lang_id = db.Column(db.Integer, primary_key=True)
    lang_ru = db.Column(db.Text, nullable=False)
    lang_en = db.Column(db.Text, nullable=False)
    glottocode = db.Column(db.Text, nullable=True)
    ISO = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Text)
    longitude = db.Column(db.Text)

class Units(db.Model):
    unit_id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, default=None)
    dummy = db.Column(db.Integer, default=None)
    xml_id = db.Column(db.Text)
    full_entry = db.Column(db.Text)
    full_entry_en = db.Column(db.Text)
    source = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.Integer, default=1, nullable=False)
    forms = db.relationship('Forms', backref='unit', lazy=True)
    meanings = db.relationship('Meanings', backref='unit', lazy=True)
    log = db.relationship('Entry_logs', backref='unit', lazy=True)
    comments = db.relationship('Unit_comments', backref='unit', lazy=True)
    pictures = db.relationship('Unit_pictures', backref='unit', lazy=True)
    labels = db.relationship('Unit_labels', backref='unit', lazy=True)

class Language_assignment(db.Model):
    asgmt_id = db.Column(db.Text, nullable=False, primary_key=True)
    unit_id = db.Column(db.Integer)
    lang_id = db.Column(db.Integer, nullable=False)

class Unit_links(db.Model):
    link_id = db.Column(db.Integer, nullable=False, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id))
    target_id = db.Column(db.Text, nullable=False)
    type = db.Column(db.Integer, nullable=False) #1 -- just link, 2 -- synonym, 3 -- antonym, 4 -- derivate, 5 -- cognate, 6 -- hyperonym, 7 -- conversive
    rank = db.Column(db.Integer, nullable=True)

class Unit_comments(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), nullable=False)
    type = db.Column(db.Integer, nullable=False) #1 -- семантика, 2 -- ссылки на статьи, 3 -- комментарии редакции, 4 -- etym, 5 -- notes
    comment = db.Column(db.Text, nullable=False)

class Pictures(db.Model):
    picture_id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.Text, nullable=False)

class Unit_pictures(db.Model):
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id))
    picture_id = db.Column(db.Integer, db.ForeignKey(Pictures.picture_id), primary_key=True)
    picture = db.relationship('Pictures', backref='units', lazy=True)

class Glosses(db.Model):
    gloss_id = db.Column(db.Integer, primary_key=True)
    russian = db.Column(db.Text, nullable=False)
    english = db.Column(db.Text, nullable=True)
    rank = db.Column(db.Integer, unique=True)
    forms = db.relationship('Forms', backref='gloss', lazy=True)

class Label_names(db.Model):
    label_id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.Text, unique=True)
    decode = db.Column(db.Text)
    rank = db.Column(db.Integer, unique=True)
    type = db.Column(db.Integer, unique=False) # 1 -- lexical, 2 -- grammatical, 3 -- taxonomic, 4 -- topological, 5 -- mereological
    pos_id = db.Column(db.Text, unique=False) #1,2,3...
    forms = db.relationship('Form_labels', backref='label', lazy=True)
    examples = db.relationship('Example_labels', backref='label', lazy=True)

class Unit_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), unique=True)

class Taxonomic_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), unique=False)

class Topological_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), unique=False)

class Mereological_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), unique=False)

class Forms(db.Model):
    form_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), nullable=False)
    gloss_id = db.Column(db.Integer, db.ForeignKey(Glosses.gloss_id), nullable=False)
    latin = db.Column(db.Text, nullable=False)
    dummy = db.Column(db.Integer, default=0, nullable=False)
    labels = db.relationship('Form_labels', backref='forms', lazy=True)

class Form_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    form_id = db.Column(db.Text, db.ForeignKey(Forms.form_id), unique=True)

class Parts_of_speech(db.Model):
    pos_id = db.Column(db.Integer, primary_key=True)
    pos = db.Column(db.Text, unique=True, nullable=False)
    pos_short = db.Column(db.Text, nullable=True)

class Meanings(db.Model):
    meaning_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), nullable=False)
    meaning = db.Column(db.Text, nullable=True)
    meaning_en = db.Column(db.Text, nullable=True)
    pos_id = db.Column(db.Integer, db.ForeignKey(Parts_of_speech.pos_id), nullable=True)
    is_def = db.Column(db.Integer)
    rank = db.Column(db.Integer, nullable=True)
    examples = db.relationship('Examples', backref='meaning', lazy=True)
    labels = db.relationship('Meaning_labels', backref='meanings', lazy=True)
    grammar_labels = db.relationship('Grammar_labels', backref='meanings', lazy=True)

class Grammar_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    meaning_id = db.Column(db.Integer, db.ForeignKey(Meanings.meaning_id), unique=True)

class Meaning_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    meaning_id = db.Column(db.Text, db.ForeignKey(Meanings.meaning_id), unique=True)

class Examples(db.Model):
    example_id = db.Column(db.Integer, primary_key=True)
    meaning_id = db.Column(db.Integer, db.ForeignKey(Meanings.meaning_id), nullable=False)
    example = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=True)
    translation_en = db.Column(db.Text, nullable=True)
    labels = db.relationship('Example_labels', backref='forms', lazy=True) #, cascade='all, delete-orphan'

class Example_labels(db.Model):
    label_id = db.Column(db.Integer, db.ForeignKey(Label_names.label_id), primary_key=True)
    example_id = db.Column(db.Text, db.ForeignKey(Examples.example_id), unique=True)

class Roles(db.Model):
    role_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Text, unique=True)
    users = db.relationship('Users', backref='role', lazy=True)

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text(40), nullable=False, unique=True)
    firstname = db.Column(db.Text(40), nullable=False)
    surname = db.Column(db.Text(40), nullable=False)
    email = db.Column(db.Text(100), unique=True)
    password = db.Column(db.Text(100))
    joined = db.Column(db.Integer, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey(Roles.role_id), default=1)
    last_seen = db.Column(db.Integer, nullable=False)

class Tasks(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    unit_ids = db.Column(db.Integer, nullable=True)
    datetime = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    assignees = db.Column(db.Text, nullable=True)
    status = db.Column(db.Integer, nullable=False, default=1) #1--assigned, 2--solved, 3--in progress, 4 -- declined
    type = db.Column(db.Integer, nullable=False, default=1) #1--mistake report, 2--task

class Messages(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.Integer, nullable=False)
    last_edited = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey(Users.user_id), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Tasks.task_id), nullable=True)

class Task_logs(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Tasks.task_id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(Users.user_id), nullable=True)
    target_id = db.Column(db.Text, nullable=True)
    event = db.Column(db.Integer, nullable=False) #1-task created, 2-task solved, 3-in progress, 4-declined, 5-user_assigned, 6-unit_assigned
    datetime = db.Column(db.Integer, nullable=False)

class Entry_logs(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey(Units.unit_id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(Users.user_id), nullable=False)
    event = db.Column(db.Integer, nullable=False)
    #entry_dump = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.Integer, nullable=False)
    source = db.Column(db.Integer, default=1, nullable=False)