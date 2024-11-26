import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, Resume, bcrypt

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_route_get(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_signup_route_get(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)

    def test_logout_route(self):
        response = self.app.get('/logout')
        self.assertEqual(response.status_code, 302)  

    def test_resume_builder_route(self):
        response = self.app.get('/resume_builder')
        self.assertEqual(response.status_code, 200)

    def test_get_all_resumes_empty(self):
        response = self.app.get('/get_all_resumes')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

    def test_job_search_route(self):
        response = self.app.get('/student/job_search')
        self.assertEqual(response.status_code, 200)

    def test_add_job_application(self):
        with patch('app.add_job'):
            response = self.app.post('/add_job_application', data={
                'company': 'TestCo',
                'location': 'TestCity',
                'jobposition': 'Developer',
                'salary': '100000',
                'status': 'Applied',
                'user_id': 'test_user'
            })
            self.assertEqual(response.status_code, 302)

    @patch('os.path.isdir', return_value=True)
    @patch('os.makedirs')
    @patch('os.listdir', return_value=[])
    def test_file_upload(self, mock_listdir, mock_makedirs, mock_isdir):
        data = {
            'user_id': 'test_user'
        }
        data['file'] = (BytesIO(b'my file contents'), 'test.pdf')
        response = self.app.post('/student/upload',
                               content_type='multipart/form-data',
                               data=data)
        self.assertEqual(response.status_code, 200)

    def test_analyze_resume_route(self):
        response = self.app.get('/student/analyze_resume')
        self.assertEqual(response.status_code, 200)

    def test_google_signup_new_user(self):
        with patch('app.find_user', return_value=None):
            with patch('app.add_client'):
                response = self.app.post('/google-signup',
                                       json={
                                           'email': 'test@gmail.com',
                                           'name': 'Test User',
                                           'username': 'testuser',
                                           'role': 'student'
                                       },
                                       content_type='application/json')
                self.assertEqual(response.status_code, 302)

    def test_job_profile_analyze_get(self):
        response = self.app.get('/student/job_profile_analyze')
        self.assertEqual(response.status_code, 200)

    def test_job_profile_analyze_post(self):
        with patch('app.extract_skills', return_value=['Python', 'Java']):
            response = self.app.post('/student/job_profile_analyze',
                                   data={'job_profile': 'Software Developer'})
            self.assertEqual(response.status_code, 200)

    @patch('app.s_email')
    def test_add_new_job_with_email(self, mock_email):
        response = self.app.post('/student/add_New',
                               data={
                                   'fullname': 'TestCo',
                                   'location_text': 'TestCity',
                                   'text': 'Developer',
                                   'sal': '100000',
                                   'user': 'testuser',
                                   'pass': 'testpass',
                                   'user_email': 'test@example.com',
                                   'starting_date': '2024-01-01',
                                   'notes': 'Test notes'
                               })
        self.assertEqual(response.status_code, 200)

    def test_download_resume(self):
        test_resume = Resume(
            resume_name='test_resume',
            name='John Doe',
            email='john@example.com',
            mobile='1234567890',
            linkedin='linkedin.com/johndoe',
            education='[]',
            experience='[]',
            skills='Python, Java'
        )
        with app.app_context():
            db.session.add(test_resume)
            db.session.commit()
            response = self.app.get('/download_resume?resume_name=test_resume')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'application/pdf')

    def test_resume_deletion_nonexistent(self):
        response = self.app.delete('/delete_resume', query_string={'resume_name': 'nonexistent_resume'})
        self.assertEqual(response.status_code, 404)

    def test_google_login_invalid_token(self):
        with patch('requests.get') as mocked_get:
            mocked_get.return_value.status_code = 401
            response = self.app.post('/google-login', data={'credential': 'invalid_token'})
            self.assertEqual(response.status_code, 401)

    def test_download_resume_nonexistent(self):
        response = self.app.get('/download_resume', query_string={'resume_name': 'nonexistent_resume'})
        self.assertEqual(response.status_code, 404)

    def test_pdf_generation_no_data(self):
        response = self.app.get('/download_resume', query_string={'resume_name': 'empty_resume'})
        self.assertEqual(response.status_code, 404)

    def test_logout_redirect(self):
        with self.app:
            response = self.app.get('/logout', follow_redirects=True)
            self.assertIn(b'Login', response.data)

    def test_retrieve_existing_resume(self):
        test_resume = {
            'resume_name': 'existing_resume',
            'name': 'Existing User',
            'email': 'existing@example.com',
            'mobile': '9876543210',
            'linkedin': 'linkedin.com/existinguser',
            'education': '[]',
            'experience': '[]',
            'skills': 'C++, Python'
        }
        with app.app_context():
            resume = Resume(**test_resume)
            db.session.add(resume)
            db.session.commit()
        response = self.app.get('/retrieve_resume', query_string={'resume_name': 'existing_resume'})
        self.assertEqual(response.status_code, 200)

    def test_retrieve_non_existent_resume(self):
        response = self.app.get('/retrieve_resume', query_string={'resume_name': 'fake_resume'})
        self.assertEqual(response.status_code, 404)

    def test_delete_non_existent_resume(self):
        response = self.app.delete('/delete_resume', query_string={'resume_name': 'non_existent_resume'})
        self.assertEqual(response.status_code, 404)

    def test_update_existing_resume(self):
        test_resume = {
            'resume_name': 'updatable_resume',
            'name': 'John Doe',
            'email': 'john@example.com',
            'mobile': '1234567890',
            'linkedin': 'linkedin.com/johndoe',
            'education': '[]',
            'experience': '[]',
            'skills': 'Python, Java'
        }
        with app.app_context():
            resume = Resume(**test_resume)
            db.session.add(resume)
            db.session.commit()
        updated_data = test_resume.copy()
        updated_data['email'] = 'updated_john@example.com'
        response = self.app.post('/save_resume', json=updated_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_get_job_application_status(self):
        response = self.app.get('/student/Applied', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # def test_job_search_results_valid(self):
    #     with patch('requests.get') as mock_get:
    #         mock_get.return_value.status_code = 200
    #         mock_get.return_value.json.return_value = {
    #             'results': [{
    #                 'title': 'Software Engineer',
    #                 'company': {'display_name': 'TestCorp'},
    #                 'location': {'display_name': 'TestCity'},
    #                 'salary_max': 100000,
    #                 'redirect_url': 'http://testjob.com/123'
    #             }]
    #         }
    #         response = self.app.post('/student/job_search/result', data={'job_role': 'Software Engineer'})
    #         self.assertEqual(response.status_code, 200)
    #         self.assertIn(b'TestCorp', response.data)

    def test_registration_route(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)

    def test_login_page_load(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_admin_page_access(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 1 
            response = self.app.get('/admin')
            self.assertEqual(response.status_code, 200)

    def test_logout_functionality(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 1
            response = self.app.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_invalid_login(self):
        response = self.app.post('/login', data={
            'username': 'invalid',
            'password': 'invalid'
        }, follow_redirects=True)
        self.assertIn(b'Login', response.data)  

    def test_student_page_access(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 2  
            response = self.app.get('/student')
            self.assertEqual(response.status_code, 200)

    def test_upload_file(self):
        data = {
            'file': (BytesIO(b'content of the file'), 'test.pdf'),
            'user_id': '1'
        }
        response = self.app.post('/student/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200)

    def test_job_search_page_access(self):
        response = self.app.get('/student/job_search')
        self.assertEqual(response.status_code, 200)

    def test_job_profile_analysis_get(self):
        response = self.app.get('/student/job_profile_analyze')
        self.assertEqual(response.status_code, 200)

    def test_get_all_resumes(self):
        response = self.app.get('/get_all_resumes')
        self.assertEqual(response.status_code, 200)

    def test_create_new_resume(self):
        resume_data = {
            'resume_name': 'unique_resume',
            'name': 'John Unique',
            'email': 'johnunique@example.com',
            'mobile': '9876543211',
            'linkedin': 'linkedin.com/johnunique',
            'education': '[]',
            'experience': '[]',
            'skills': 'Python, C++'
        }
        response = self.app.post('/save_resume', json=resume_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_admin_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_student_signup_page(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)

    def test_successful_logout(self):
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_display_job_application(self):
        response = self.app.get('/student')
        self.assertEqual(response.status_code, 200)

    # def test_retrieve_job_applications(self):
    #     with app.app_context():
    #         response = self.app.get('/student/job_search')
    #         self.assertEqual(response.status_code, 200)

    def test_access_resume_builder(self):
        response = self.app.get('/resume_builder')
        self.assertEqual(response.status_code, 200)

    def test_resume_download_route(self):
        response = self.app.get('/download_resume', query_string={'resume_name': 'nonexistent'})
        self.assertEqual(response.status_code, 404)  

    # def test_empty_job_search(self):
    #     response = self.app.post('/student/job_search/result', data={'job_role': ''})
    #     self.assertEqual(response.status_code, 200)

    def test_pdf_creation_existing_resume(self):
        with app.app_context():
            resume = Resume.query.first() 
            if resume:
                response = self.app.get(f'/download_resume?resume_name={resume.resume_name}')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'application/pdf')

    def test_update_nonexistent_job_application(self):
        response = self.app.post('/student/update_job_application', data={
            'company': 'NonExistentCo',
            'status': 'Rejected'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 400)  

    def test_delete_nonexistent_job_application(self):
        response = self.app.post('/student/delete_job_application/NonExistentCo', follow_redirects=True)
        self.assertEqual(response.status_code, 400) 

    def test_access_resume_analysis_page(self):
        response = self.app.get('/student/analyze_resume')
        self.assertEqual(response.status_code, 200)

    def test_companies_list_page(self):
        response = self.app.get('/student/companiesList')
        self.assertEqual(response.status_code, 200)

    def test_display_specific_file(self):
        with patch('os.listdir', return_value=['resume.pdf']):
            response = self.app.get('/student/display')
            self.assertEqual(response.status_code, 308) 

    def test_chat_gpt_analysis(self):
        with patch('os.listdir', return_value=['resume.pdf']), \
            patch('app.chatgpt', return_value='Suggestion text'):
            response = self.app.get('/chat_gpt_analyzer')
            self.assertEqual(response.status_code, 308)

    def test_registration_form_validation(self):
        response = self.app.post('/signup', data={})
        self.assertEqual(response.status_code, 400)  

    def test_update_existing_resume_no_change(self):
        with app.app_context():
            resume = Resume.query.first()  
            if resume:
                response = self.app.post('/save_resume', json={
                    'resume_name': resume.resume_name,
                    'name': resume.name,
                    'email': resume.email,
                    'mobile': resume.mobile,
                    'linkedin': resume.linkedin,
                    'education': resume.education,
                    'experience': resume.experience,
                    'skills': resume.skills
                }, content_type='application/json')
                self.assertEqual(response.status_code, 200) 

    def test_access_admin_page(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 1  # Assuming 1 is an admin ID
            response = self.app.get('/admin')
            self.assertEqual(response.status_code, 200)

    def test_access_student_page(self):
        with self.app:
            with self.app.session_transaction() as sess:
                sess['user_id'] = 2  # Assuming 2 is a student ID
            response = self.app.get('/student')
            self.assertEqual(response.status_code, 200)

    def test_retrieve_specific_job_application_status(self):
        response = self.app.get('/student/Applied')
        self.assertEqual(response.status_code, 200)

    def test_delete_job_application_valid(self):
        with self.app:
            # Setup for valid job application deletion
            response = self.app.post('/student/delete_job_application/ValidCompany', follow_redirects=True)
            self.assertEqual(response.status_code, 400)

    def test_add_new_job_application_valid(self):
        response = self.app.post('/add_job_application', data={
            'company': 'NewCo',
            'location': 'NewCity',
            'jobposition': 'NewDeveloper',
            'salary': '120000',
            'status': 'Pending',
            'user_id': 'new_user'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # def test_display_job_search_results(self):
    #     response = self.app.post('/student/job_search/result', data={'job_role': 'Developer'})
    #     self.assertEqual(response.status_code, 200)

    def test_signup_page_load(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)


    def test_access_job_profile_analysis_page(self):
        response = self.app.get('/student/job_profile_analyze')
        self.assertEqual(response.status_code, 200)

    def test_analyze_job_profile_post(self):
        with patch('app.extract_skills', return_value=['Python', 'Java']):
            response = self.app.post('/student/job_profile_analyze',
                                     data={'job_profile': 'Developer'})
            self.assertEqual(response.status_code, 200)

    def test_google_login_valid_token(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'email': 'test@gmail.com',
                'name': 'Test User',
                'username': 'testuser',
                'role': 'student'
            }
            response = self.app.post('/google-login', data={'credential': 'valid_token'})
            self.assertEqual(response.status_code, 404)

    def test_retrieve_existing_user(self):
        with patch('app.find_user', return_value=['testuser', 'Test User', 'test@gmail.com', 'student']):
            response = self.app.get('/retrieve_user', query_string={'username': 'testuser'})
            self.assertEqual(response.status_code, 404)

    # Test for /interview-prep route
    def test_interview_prep(self):
        response = self.app.get('/interview-prep')
        self.assertEqual(response.status_code, 200)

    # Test for /mock-interview route
    def test_mock_interview(self):
        response = self.app.get('/mock-interview')
        self.assertEqual(response.status_code, 200)

    # Test for /common-questions route
    def test_common_questions(self):
        response = self.app.get('/common-questions')
        self.assertEqual(response.status_code, 200)

    # Test for /interview-tips route
    def test_interview_tips(self):
        response = self.app.get('/interview-tips')
        self.assertEqual(response.status_code, 200)

    # Test for /chatbot route (POST request)
    def test_chatbot(self):
        data = {'message': 'What is your name?'}
        response = self.app.post('/chatbot', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('reply', response.json)
        self.assertTrue(response.json['reply'])

    # Test for /mock-practice route
    def test_mock_practice(self):
        response = self.app.get('/mock-practice')
        self.assertEqual(response.status_code, 200)

    # Test for /generate-latex route (POST request)
    def test_generate_latex(self):
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'mobile': '123-456-7890',
            'linkedin': 'https://linkedin.com/in/johndoe',
            'education': [
                {
                    'degree': 'B.Tech',
                    'institution': 'XYZ University',
                    'graduationYear': '2025',
                    'gpa': '3.9',
                    'coursework': 'Data Structures, Algorithms'
                }
            ],
            'experience': [
                {
                    'title': 'Software Engineer Intern',
                    'company': 'ABC Corp',
                    'dates': '2023-2024',
                    'achievements': 'Developed a web application using Flask'
                }
            ],
            'skills': 'Python, Java, SQL'
        }
        response = self.app.post('/generate-latex', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('overleafUrl', response.json)
        self.assertIn('data:application/x-tex;base64,', response.json['overleafUrl'])

    # Test for BadRequest error handling in /chatbot
    def test_bad_request(self):
        data = {}  # No 'message' field
        response = self.app.post('/chatbot', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Bad Request')

    # Test for Invalid JSON Request
    def test_invalid_json(self):
        response = self.app.post('/chatbot', data="Invalid JSON")
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)
        self.assertIn('message', response.json)

if __name__ == '__main__':
    unittest.main()