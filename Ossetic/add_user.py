from Ossetic import app
from flask import render_template, session, request, url_for
from Ossetic.models import Users, db
from Ossetic.supplement import Amend, Check, Emails
from re import sub
from itsdangerous import URLSafeSerializer


