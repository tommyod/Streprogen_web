# -*- coding: utf-8 -*-
from app import app, models, db
from app.streprogen import Day, StaticExercise, DynamicExercise, Program
from flask import render_template, request, redirect, url_for, flash
from app.functions import random_string
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        unique_id = request.form['unique_id'].strip()
        if models.Program.query.filter_by(unique_id=unique_id).first() is None:
            flash(u'The program you searched for was not found.','danger')
        else:
            return redirect(url_for('overview', unique_id=unique_id))
    return render_template('search.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/edit/<unique_id>')
def edit(unique_id):
    program = models.Program.query.filter_by(unique_id=unique_id).first()
    if program is None:
        return redirect(url_for('index'))
    program = program.pickle
    days = len(program.days)
    main = len(program.days[0].main_exercises)
    extra = len(program.days[0].extra_exercises)
    return render_template('edit.html', program=program, days=days, main=main, extra=extra)

@app.route('/newprogram', methods=['POST', 'GET'])
def newprogram():
    if request.method == 'POST':
        name = request.form['name']
        main = int(request.form['main'])
        days = int(request.form['days'])
        extra = int(request.form['extra'])
        units = request.form['units']
        round = request.form['round']
        reps_RM = request.form['reps_RM']
        nonlinearity = request.form['nonlinearity']
        duration = request.form['duration']
        intensity = request.form['intensity']
        intensity_type = request.form['intensity_type']
        reps = request.form['reps']
        reps_type = request.form['reps_type']
        reps_per_week = request.form['reps_per_week']

        prog = Program(name, units, round, duration, nonlinearity, intensity, intensity_type,
                       reps, reps_type, reps_per_week, reps_RM)

        for day in range(days):
            new_day = Day()
            for m in range(main):
                try:
                    name = request.form[str(day)+'-'+str(m)+'-main-name']
                    initial = request.form[str(day)+'-'+str(m)+'-initial']
                    final = request.form[str(day)+'-'+str(m)+'-final']
                    lowreps = request.form[str(day)+'-'+str(m)+'-highreps']
                    highreps = request.form[str(day)+'-'+str(m)+'-lowreps']
                    new_day.add_main(DynamicExercise(name, initial, final, lowreps, highreps))
                except:
                    flash(u'<strong>An error occured.</strong><br> '
                          u'Most likely a missing value near day {}. '
                          u'Hit "back" in your browser and try again.'.format(day+1), 'danger')
                    return render_template('blank.html')

                if int(lowreps) >= int(highreps):
                    flash(u'<strong>An error occured.</strong><br> '
                    u'The final weight is less than or equal the inital weight for exercise "{}".'
                    u'Hit "back" in your browser and try again.'.format(name), 'danger')
                    return render_template('blank.html')
            for ex in range(extra):
                name = request.form[str(day)+'-'+str(ex)+'-extra-name']
                scheme = request.form[str(day)+'-'+str(ex)+'-scheme']
                new_day.add_extra(StaticExercise(name, scheme))

            prog.days.append(new_day)

        prog.render()

        model_program = models.Program()

        try_string = random_string(5)
        test = models.Program.query.filter_by(unique_id=try_string).first()
        while test != None:
            try_string = random_string(5)
            test = models.Program.query.filter_by(unique_id=try_string).first()

        model_program.unique_id = try_string
        model_program.date_creation = datetime.utcnow()
        model_program.date_lastviewed = datetime.utcnow()
        model_program.pickle = prog
        db.session.add(model_program)
        db.session.commit()

        return redirect(url_for('overview', unique_id=model_program.unique_id))



    #It's a GET request
    try:
        program_type = request.args.getlist('type')[0]
        days = int(request.args.getlist('days')[0])
        main = int(request.args.getlist('main')[0])
        extra = int(request.args.getlist('extra')[0])
    except:
        return redirect(url_for('index'))
    #Filter bad values
    for val in [days, main, extra]:
        if val > 5:
            return redirect(url_for('index'))

    if program_type == 'simple':
        simple = True
        return render_template('newprogram.html', days=days, main=main, extra=extra, simple=simple)
    if program_type == 'advanced':
        simple = False
        return render_template('newprogram.html', days=days, main=main, extra=extra, simple=simple)

    return redirect(url_for('index'))


@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/examples')
def examples():
    return render_template('examples.html')

@app.route('/overview/<unique_id>')
def overview(unique_id):
    program = models.Program.query.filter_by(unique_id=unique_id).first()
    if program is None:
        return redirect(url_for('index'))
    program.date_lastviewed = datetime.utcnow()
    db.session.commit()

    return render_template('overview.html', program=program)

@app.route('/print/<unique_id>')
def Print(unique_id):
    program = models.Program.query.filter_by(unique_id=unique_id).first()
    if program is None:
        return redirect(url_for('index'))

    return render_template('print.html', program=program.pickle, unique_id=unique_id)

@app.route('/rerender/<unique_id>')
def rerender(unique_id):
    return ''
    program = models.Program.query.filter_by(unique_id=unique_id).first()
    if program is None:
        return redirect(url_for('index'))

    from copy import deepcopy
    program.pickle.render()
    prog = deepcopy(program.pickle)
    prog.name = 'Changed'

    program.pickle = prog
    db.session.commit()
    return redirect(url_for('overview', unique_id=unique_id))

@app.route('/latest')
def latest():
    programs = models.Program.query.order_by('date_creation desc').limit(20).all()
    return render_template('latest.html', programs=programs)
