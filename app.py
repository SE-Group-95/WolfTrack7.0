'''
MIT License

Copyright (c) 2024 Girish G N, Joel Jogy George, Pravallika Vasireddy

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
import logging
from flask import Flask, jsonify, request, render_template, make_response, redirect, url_for, send_from_directory, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField 
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo, Regexp
from werkzeug.utils import redirect
from Controller.send_email import *
from Controller.send_profile import *
from Controller.ResumeParser import *
from Utils.jobprofileutils import *
import os
from flask import send_file, current_app as app
from Controller.chat_gpt_pipeline import pdf_to_text,chatgpt,extract_top_job_roles
from Controller.data import data, upcoming_events, profile
from Controller.send_email import *
from dbutils import add_job, create_tables, add_client, delete_job_application_by_company, find_user, get_job_applications, get_job_applications_by_status, update_job_application_by_id
from login_utils import login_user
import requests
import json
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
logging.basicConfig(level=logging.ERROR)
from dotenv import load_dotenv



# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', "sqlite:///database.db")
# Set the SECRET_KEY, with a fallback for testing environments
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_testing_secret_key')

# Raise an error if the SECRET_KEY is missing in non-test environments
if not app.config['SECRET_KEY'] and os.getenv('FLASK_ENV') != 'testing':
    raise ValueError("No SECRET_KEY set for Flask application")

if not app.config['SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application")

db = SQLAlchemy(app)
database = "database.db"


# Create tables for the original application
create_tables(database)

# Resume Model
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_name = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    linkedin = db.Column(db.String(200), nullable=False)
    education = db.Column(db.Text, nullable=False)
    experience = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False)

# Original Form Classes
class RegisterForm(FlaskForm):
    username = StringField(render_kw={"placeholder": "Username"})
    name = StringField(render_kw={"placeholder": "Name"})
    password = PasswordField(render_kw={"placeholder": "Password"})
    usertype = SelectField(render_kw={"placeholder": "Usertype"}, choices=[('admin', 'Admin'), ('student', 'Student')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    usertype = SelectField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Usertype"}, choices=[('admin', 'Admin'), ('student', 'Student')])
    submit = SubmitField('Login')

# PDF Creation Function
def create_pdf(resume_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    
    # Style definitions
    styles.add(ParagraphStyle(
        name='NameStyle',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='ContactInfo',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=1,
        spaceAfter=12,
        textColor=colors.black
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        textColor=colors.black,
        spaceBefore=12,
        spaceAfter=6,
        alignment=0,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='NormalText',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        spaceBefore=1,
        spaceAfter=1
    ))

    story = []
    
    # Header section
    story.append(Paragraph(resume_data.name, styles['NameStyle']))
    contact_info = f"{resume_data.mobile} | {resume_data.email} | {resume_data.linkedin}"
    story.append(Paragraph(contact_info, styles['ContactInfo']))
    
    # Education section
    story.append(Paragraph("EDUCATION", styles['SectionHeader']))
    education_list = json.loads(resume_data.education)
    for edu in education_list:
        edu_header = [[
            Paragraph(edu['institution'], styles['NormalText']),
            Paragraph(edu['graduationYear'], styles['NormalText'])
        ]]
        edu_table = Table(edu_header, colWidths=[5*inch, 1.5*inch])
        edu_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (1,0), (1,0), 0),
        ]))
        story.append(edu_table)
        
        if edu.get('gpa'):
            degree_data = [[
                Paragraph(edu['degree'], styles['NormalText']),
                Paragraph(f"GPA: {edu['gpa']}/4.0", styles['NormalText'])
            ]]
        else:
            degree_data = [[
                Paragraph(edu['degree'], styles['NormalText']),
                Paragraph('', styles['NormalText'])
            ]]
        degree_table = Table(degree_data, colWidths=[5*inch, 1.5*inch])
        degree_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (1,0), (1,0), 0),
        ]))
        story.append(degree_table)
        
        if edu.get('coursework'):
            coursework = edu['coursework'].split('\n')
            if coursework:
                coursework_data = [[Paragraph(f"Related Coursework: {', '.join(c.strip() for c in coursework if c.strip())}", styles['NormalText'])]]
                coursework_table = Table(coursework_data, colWidths=[6.5*inch])
                coursework_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ]))
                story.append(coursework_table)
        
        story.append(Spacer(1, 6))
    
    # Technical Skills section
    story.append(Paragraph("TECHNICAL SKILLS", styles['SectionHeader']))
    skills_list = resume_data.skills.split('\n')
    for skill_line in skills_list:
        if skill_line.strip():
            skill_data = [[Paragraph(skill_line.strip(), styles['NormalText'])]]
            skill_table = Table(skill_data, colWidths=[6.5*inch])
            skill_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(skill_table)
    
    # Professional Experience section
    story.append(Paragraph("WORK EXPERIENCE", styles['SectionHeader']))
    experience_list = json.loads(resume_data.experience)
    for exp in experience_list:
        company_title = f"{exp['company']}, {exp['location']}" if exp.get('location') else exp['company']
        exp_header = [[
            Paragraph(f"{company_title}, {exp['title']}", styles['NormalText']),
            Paragraph(exp['dates'], styles['NormalText'])
        ]]
        exp_table = Table(exp_header, colWidths=[5*inch, 1.5*inch])
        exp_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,0), 0),
            ('RIGHTPADDING', (1,0), (1,0), 0),
        ]))
        story.append(exp_table)
        
        achievements = exp['achievements'].split('\n')
        for achievement in achievements:
            if achievement.strip():
                achievement_data = [[Paragraph(f"• {achievement.strip()}", styles['NormalText'])]]
                achievement_table = Table(achievement_data, colWidths=[6.5*inch])
                achievement_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('LEFTPADDING', (0,0), (-1,-1), 20),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ]))
                story.append(achievement_table)
        
        story.append(Spacer(1, 6))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Original Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['type'] = ''
    session['user_id'] = None
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user(str(form.username.data), database)
        if user:
            if bcrypt.check_password_hash(user[3], form.password.data):
                login_user(app, user)
                if user[4] == 'admin':
                    return redirect(url_for('admin', data=user[2]))
                elif user[4] == 'student':
                    return redirect(url_for('student', data=user[2]))
    return render_template('login.html', form=form)

# ... [Keep all other original routes from app.py] ...
@app.route('/google-login', methods=['GET','POST'])
def google_login():
    token = request.form.get('credential')  # "credential" contains the ID token from Google
    if not token:
        return jsonify({"error": "Token not provided"}), 400

    # Verify the token with Google
    google_verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
    response = requests.get(google_verify_url)
    if response.status_code != 200:
        return jsonify({"error": "Invalid token"}), 401

    # Step 2: Parse the token data
    user_data = response.json()
    google_email = user_data.get("email")
    
    # Step 3: Check user in the database
    username = google_email.split('@')[0]
    user = find_user(username, database)
    if not user:
        # Optional: create a new user if they don't exist, with a default role if applicable
        return jsonify({"error": "User not found"}), 404

    # Step 4: Determine role and redirect
    role = user[4]
    user_data_value = user[2]

    login_user(app, user)  # Log in the user

    # Redirect based on the role
    if role == 'admin':
        return redirect(url_for('admin', data=user_data_value))
    elif role == 'student':
        return redirect(url_for('student', data=user_data_value))
    else:
        return jsonify({"error": "User role undefined"}), 400


@app.route('/signup',methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        # Password hashing and new user creation
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_client = [form.name.data, form.username.data, hashed_password, form.usertype.data]
        add_client(new_client, database)
        return redirect(url_for('login'))

    # Return 400 status for invalid form data
    if request.method == 'POST' and not form.validate():
        return render_template('signup.html', form=form), 400

    return render_template('signup.html', form=form)
    
@app.route('/google-signup', methods=['POST'])
def google_signup():
    # Get the Google token and role from URL parameters
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    username = data.get('username')
    role = data.get('role')

    # Check if the user already exists
    user = find_user(username, database)
    if user:
        return jsonify({"error": "User already exists"}), 409  # Conflict

    # Generate a username from the email
    hashed_password = bcrypt.generate_password_hash('default_password').decode('utf-8')
    # Create a new user with the specified role
    new_user = [name, username, hashed_password, role]
    add_client(new_user, database)  # Function to add the new user to the database
    # Log the user in and redirect based on role
    user = find_user(username,database)

    return redirect(url_for('login'))
    # login_user(app, user)
    # if new_user["role"] == "admin":
    #     return jsonify({"redirect": url_for('admin', data=user[2])})
    # else:
    #     return jsonify({"redirect": url_for('student', data=user[2])})


@app.route('/admin',methods=['GET', 'POST'])
def admin():
    data_received = request.args.get('data')
    user = find_user(str(data_received),database)
    ##Add query
    return render_template('admin_landing.html', user=user)


@app.route('/student',methods=['GET', 'POST'])
def student():
    data_received = request.args.get('data')
    user = find_user(str(data_received),database)


    jobapplications = get_job_applications(database)
    return render_template('home.html', user=user, jobapplications=jobapplications)

@app.route('/student/<status>', methods=['GET', 'POST'])
def get_job_application_status(status):
    data_received = request.args.get('data')
    user = find_user(str(data_received), database)

    if status:
        job_applications = get_job_applications_by_status(database, status)
    else:
        job_applications = get_job_applications(database)

    return render_template('home.html', user=user, jobapplications=job_applications)


@app.route("/admin/send_email", methods=['GET','POST'])
def send_email():
    comments = request.form['comment']
    email = 'ggopala4@ncsu.edu'
    s_comment_email(email,comments)
    return make_response(render_template('admin_landing.html'), 200,{'Content-Type': 'text/html'})

@app.route("/admin/render_resume")
def tos():
    workingdir = os.path.abspath(os.getcwd())
    filepath = workingdir + '/static/files/'
    return send_from_directory(filepath, 'resume2.pdf')

@app.route("/add_job_application", methods=['POST'])
def add_job_application():
    if request.method == 'POST':
        company = request.form['company']
        location = request.form['location']
        jobposition = request.form['jobposition']
        salary = request.form['salary']
        status = request.form['status']
        user_id = request.form['user_id']

        job_data = [company, location, jobposition, salary, status]
        # Perform actions with the form data, for instance, saving to the database
        add_job(job_data,database)

        flash('Job Application Added!')
        # Redirect to a success page or any relevant route after successful job addition
        return redirect(url_for('student', data=user_id))

@app.route('/student/update_job_application',methods=['GET','POST'])
def update_job_application():
    if request.method == 'POST':
        company = request.form['company']
        location = request.form['location']
        jobposition = request.form['jobposition']
        salary = request.form['salary']
        status = request.form['status']
        user_id = request.form['user_id']

        # Perform the update operation
        update_job_application_by_id( company, location, jobposition, salary, status, database)  # Replace this with your method to update the job

        flash('Job Application Updated!')
        # Redirect to a success page or any relevant route after successful job update
        return redirect(url_for('student', data=user_id))

@app.route('/student/delete_job_application/<company>', methods=['POST'])
def delete_job_application(company):
    if request.method == 'POST':
        user_id = request.form['user_id']
        # Perform the deletion operation
        delete_job_application_by_company(company,database)  # Using the function to delete by company name

        flash('Job Application Deleted!')
        # Redirect to a success page or any relevant route after successful deletion
        return redirect(url_for('student', data=user_id))  # Redirect to the student page or your desired route

@app.route('/student/add_New',methods=['GET','POST'])
def add_New():
    company_name = request.form['fullname']
    location = request.form['location_text']
    Job_Profile = request.form['text']
    salary = request.form['sal']
    user = request.form['user']
    password = request.form['pass']
    email = request.form['user_email']
    sec_question = request.form['starting_date']
    sec_answer = request.form['starting_date']
    notes = request.form['notes']
    date_applied = request.form['starting_date']

    s_email(company_name,location, Job_Profile,salary, user,password,email,sec_question,sec_answer,notes,date_applied)
    return render_template('home.html', data=data, upcoming_events=upcoming_events, user=user)

@app.route('/student/send_Profile',methods=['GET','POST'])
def send_Profile():
    emailID = request.form['emailID']
    s_profile(data,upcoming_events, profile,emailID)

    print("Email Notification Sent")
    '''data_received = request.args.get('data')
    print('data_receivedddd->>>> ', data_received)
    user = find_user(str(data_received))
    print('Userrrrrr', user)'''
    user_id = request.form['user_id']
    user = request.form['user_id']
    print('==================================================================', user)
    
    user = find_user(str(user),database)

    data_received = request.args.get('data')
    user = find_user(str(data_received),database)

    return render_template('home.html', data=data, upcoming_events=upcoming_events, user=user)


@app.route('/student/job_profile_analyze', methods=['GET', 'POST'])
def job_profile_analyze():
    if request.method == 'POST':
        job_profile = request.form['job_profile']
        skills = extract_skills(job_profile)
        skills_text = ', '.join(skills)
        return render_template('job_profile_analyze.html', skills_text=skills_text, job_profile=job_profile)
    return render_template('job_profile_analyze.html', skills_text='', job_profile='')

@app.route("/student/upload", methods=['POST'])
def upload():
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(APP_ROOT, 'Controller', 'resume')

    if not os.path.isdir(target):
        os.makedirs(target)

    existing_files = os.listdir(target)
    if existing_files:
        os.remove(os.path.join(target, existing_files[0]))

    for file in request.files.getlist("file"):
        filename = file.filename
        destination = os.path.join(target, filename)
        file.save(destination)

    user_id = request.form['user_id']
    user = find_user(str(user_id), database)
    return render_template("home.html", data=data, upcoming_events=upcoming_events, user=user)


@app.route('/student/analyze_resume', methods=['GET'])
def view_ResumeAna():
    return render_template('resume_analyzer.html')

@app.route('/student/companiesList', methods=['GET'])
def view_companies_list():
    return render_template('companies_list.html')


@app.route('/student/analyze_resume', methods=['POST'])
def analyze_resume():
    jobtext = request.form['jobtext']
    os.chdir(os.getcwd()+"/Controller/resume/")
    output = resume_analyzer(jobtext, str(os.listdir(os.getcwd())[0]))
    os.chdir("..")
    os.chdir("..")
    return render_template('resume_analyzer.html', data = output)

@app.route("/student/display/", methods=['POST','GET'])
def display():
    path = os.getcwd()+"/Controller/resume/"
    filename = os.listdir(path)
    if filename:
        return send_file(path+str(filename[0]),as_attachment=True)
    else:
        user = request.form['user_id']
        user = find_user(str(user),database)
        return render_template('home.html', user=user, data=data, upcoming_events=upcoming_events)



@app.route('/chat_gpt_analyzer/', methods=['GET'])
def chat_gpt_analyzer():
    files = os.listdir(os.getcwd()+'/Controller/resume')
    pdf_path = os.getcwd()+'//Controller/resume/'+files[0]
    text_path = os.getcwd()+'//Controller/temp_resume/'+files[0][:-3]+'txt'
    with open(text_path, 'w'):
        pass
    pdf_to_text(pdf_path, text_path)
    suggestions = chatgpt(text_path)
    flag = 0
    final_sugges_send = []
    final_sugges = ""

    # Initialize an empty string to store the result
    result_string = ""
    if suggestions is None:
        raise ValueError("Failed to get suggestions from the API.")
        return render_template('chat_gpt_analyzer.html', suggestions=None, pdf_path=pdf_path, section_names = section_names)
    else:

        # Iterate through each character in the original string
        for char in suggestions:
            # If the character is not a newline character, add it to the result string
            if char != '\n':
                final_sugges += char
        sections = final_sugges.split("Section")
        for section in sections:
            section = section.strip()  # Remove leading and trailing whitespace
            # if section:  # Check if the section is not empty (e.g., due to leading/trailing "Section")
            #     print("Section:", section)
        sections = sections[1:]
        section_names = ['Education', 'Experience','Skills', 'Projects']
        sections[0] = sections[0][3:]
        sections[1] = sections[1][3:]
        sections[2] = sections[2][3:]
        sections[3] = sections[3][3:]
        return render_template('chat_gpt_analyzer.html', suggestions=sections, pdf_path=pdf_path, section_names = section_names)


@app.route('/student/job_search')
def job_search():
    return render_template('job_search.html')

@app.route('/student/job_search/result', methods=['POST'])
def search():
    job_role = request.form['job_role']
    adzuna_url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=575e7a4b&app_key=35423835cbd9428eb799622c6081ffed&what_phrase={job_role}"
    try:
        response = requests.get(adzuna_url)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('results', [])
            return render_template('job_search_results.html', jobs=jobs)
        else:
            return "Error fetching job listings"
    except requests.RequestException as e:
        logging.error(f"Error fetching job listings: {e}")
        return "An internal error has occurred while fetching job listings."

@app.route('/findJobs')
def find_jobs():
    files = os.listdir(os.getcwd()+'/Controller/resume')
    if not files:
        flash('No resumes available to analyze.', 'error')
        return redirect(url_for('index'))

    pdf_path = os.getcwd() + '//Controller/resume/' + files[0]
    text_path = os.getcwd() + '//Controller/temp_resume/' + files[0][:-3] + 'txt'
    pdf_to_text(pdf_path, text_path)
    job_roles = extract_top_job_roles(text_path)

    if job_roles is None:
        flash('Failed to extract job roles from resume.', 'error')
        return redirect(url_for('index'))

    print(f"Recommended Job Roles: {job_roles}")

    job_query = ','.join(job_roles).replace(' ', '%20')
    adzuna_url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=575e7a4b&app_key=35423835cbd9428eb799622c6081ffed&what_or={job_query}"

    try:
        response = requests.get(adzuna_url)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('results', [])
            return render_template('job_recommendation_results.html', jobs=jobs)
        else:
            flash('Error fetching job listings from Adzuna.', 'error')
    except requests.RequestException as e:
        logging.error(f"Error fetching job listings from Adzuna: {e}")
        flash('An internal error has occurred while fetching job listings from Adzuna.', 'error')

    return redirect(url_for('index'))



# New Resume Builder Routes
@app.route('/resume_builder')
def resume_builder():
    return render_template('resume_builder_index.html')

@app.route('/get_all_resumes', methods=['GET'])
def get_all_resumes():
    resumes = Resume.query.all()
    resume_list = [{"resume_name": resume.resume_name, "name": resume.name} for resume in resumes]
    return jsonify(resume_list)

@app.route('/save_resume', methods=['POST'])
def save_resume():
    data = request.get_json()
    existing_resume = Resume.query.filter_by(resume_name=data['resume_name']).first()
    if existing_resume:
        try:
            for key, value in data.items():
                setattr(existing_resume, key, value)
            db.session.commit()
            return jsonify({"message": "Resume updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating resume: {str(e)}")
            return jsonify({"message": "An internal error has occurred."}), 500

    else:
        try:
            resume = Resume(**data)
            db.session.add(resume)
            db.session.commit()
            return jsonify({"message": "Resume saved successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving resume: {str(e)}")
            return jsonify({"message": "An internal error has occurred."}), 500


@app.route('/delete_resume', methods=['DELETE'])
def delete_resume():
    resume_name = request.args.get('resume_name')
    resume = Resume.query.filter_by(resume_name=resume_name).first()
    if resume:
        try:
            db.session.delete(resume)
            db.session.commit()
            return jsonify({"message": "Resume deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()

            app.logger.error(f"Error deleting resume: {str(e)}")
            return jsonify({"message": "An internal error has occurred."}), 500

    else:
        return jsonify({"message": "Resume not found"}), 404

@app.route('/retrieve_resume', methods=['GET'])
def retrieve_resume():
    resume_name = request.args.get('resume_name')
    resume = Resume.query.filter_by(resume_name=resume_name).first()
    if resume:
        return jsonify({
            "resume_name": resume.resume_name,
            "name": resume.name,
            "email": resume.email,
            "mobile": resume.mobile,
            "linkedin": resume.linkedin,
            "education": resume.education,
            "experience": resume.experience,
            "skills": resume.skills
        }), 200
    else:
        return jsonify({"message": "Resume not found"}), 404

@app.route('/download_resume', methods=['GET'])
def download_resume():
    resume_name = request.args.get('resume_name')
    resume = Resume.query.filter_by(resume_name=resume_name).first()
    if resume:
        pdf_buffer = create_pdf(resume)
        return send_file(
            pdf_buffer,
            download_name=f"{resume_name}_resume.pdf",
            mimetype='application/pdf',
            as_attachment=True
        )
    else:
        return jsonify({"message": "Resume not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    app.run(debug=debug_mode)
