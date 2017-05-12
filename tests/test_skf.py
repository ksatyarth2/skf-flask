import os, json, unittest, tempfile, skf
from skf import settings
from skf.api.security import log, val_num, val_float, val_alpha, val_alpha_num
from skf.db_tools import init_db, connect_db, init_md_knowledge_base, init_md_checklists, init_md_code_examples
from skf.app import app


class TestRestPlusApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        with app.app_context():
            settings.TESTING = True
            skf.app.initialize_app(app)


    def test_get_status(self):
        """Test if the API GUI is available"""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)
        assert b'OWASP-SKF API' in response.data


    def test_activate_user(self):
        """Test if the activate user call is working"""
        payload = {'accessToken': 1234, 'email': 'example@owasp.org', 'password': 'admin', 'repassword': 'admin', 'username': 'admin'}
        headers = {'content-type': 'application/json'}
        response = self.client.put('/api/user/activate/1', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertTrue(response_dict.get('message'))


    def test_login(self):
        """Test if the login call is working"""
        payload = {'username': 'admin', 'password': 'admin'}
        headers = {'content-type': 'application/json'}
        response = self.client.post('/api/user/login/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertTrue(response_dict.get('Authorization token'))


    def test_login_create(self):
        """Test if the login create call is working"""
        jwt = self.login('admin', 'admin')
        payload = {'email': 'test_user@owasp.org', 'privilege': 1}
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.put('/api/user/create/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['email'], "test_user@owasp.org")


    def login(self, username, password):
        """Login method needed for testing"""
        payload = {'username': ''+username+'', 'password': ''+password+''}
        headers = {'content-type': 'application/json'}
        response = self.client.post('/api/user/login/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        return response_dict.get('Authorization token')


    def test_get_checklist(self):
        """Test if the get checklist items call is working"""
        response = self.client.get('/api/checklist/items/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict[0]['checklist_items_checklistID'], "1.0")


    def test_get_checklist_item_10(self):
        """Test if the get specific checklist item call is working"""
        response = self.client.get('/api/checklist/items/10.0')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['checklist_items_checklistID'], "10.0")


    def test_get_checklist_items_level(self):
        """Test if the get specific checklist item by level call is working"""
        jwt = self.login('admin', 'admin')
        payload = {'level': '1'}
        headers = {'content-type': 'application/json'}
        response = self.client.post('/api/checklist/items/level', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict[0]['checklist_items_content'], "Architecture, design and threat modelling")
        self.assertEqual(response_dict[0]['checklist_items_level'], "0")


    def test_get_kb(self):
        """Test if the get kb items call is working"""
        response = self.client.get('/api/kb/items/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][1]['title'], "External DTD parsing")


    def test_get_kb_item_10(self):
        """Test if the get specific kb item call is working"""
        response = self.client.get('/api/kb/items/10')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['title'], "Repudiation attack")


    def test_update_kb(self):
        """Test if the update kb items call is working"""
        jwt = self.login('admin', 'admin')        
        payload = {'content': 'Unit test content update', 'title': 'Unit test title update'}
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.put('/api/kb/items/update/1', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['message'], "KB item successfully updated")
        response = self.client.get('/api/kb/items/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][0]['title'], "Unit test title update")


    def test_create_project(self):
        """Test if the create new project call is working"""
        jwt = self.login('admin', 'admin')        
        payload = {'description': 'Unit test description project', 'name': 'Unit test name project', 'version': 'version 1.0'}
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.put('/api/project/items/new', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['message'], "Project successfully created")


    def test_project_items(self):
        """Test if the project items call is working"""
        jwt = self.login('admin', 'admin') 
        headers = {'Authorization': jwt}
        response = self.client.get('/api/project/items/', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][0]['projectName'], "Unit test name project")


    def test_project_item(self):
        """Test if the project item call is working"""
        jwt = self.login('admin', 'admin') 
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.get('/api/project/items/2', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['projectName'], "Unit test name project")


    def test_update_project_item(self):
        """Test if the project update call is working"""
        jwt = self.login('admin', 'admin') 
        payload = {'description': 'Unit test description project update', 'name': 'Unit test name project update', 'version': 'version 1.1'}
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.put('/api/project/items/update/2', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['message'], "Project successfully updated")
        response = self.client.get('/api/project/items/2', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['projectName'], "Unit test name project update")


    def test_delete_project_item(self):
        """Test if the delete project item call is working"""
        jwt = self.login('admin', 'admin') 
        payload = {'description': 'Unit test description project', 'name': 'Unit test name project', 'version': 'version 1.0'}
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.put('/api/project/items/new', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['message'], "Project successfully created")
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.delete('/api/project/items/delete/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['message'], "Project successfully deleted")


    def test_get_code(self):
        """Test if the get code items call is working"""
        response = self.client.get('/api/code/items/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][1]['title'], "Anti clickjacking headers")


    def test_get_code_item_10(self):
        """Test if the get specific code item call is working"""
        response = self.client.get('/api/code/items/10')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['title'], "Enforce secure passwords")


    def test_update_code(self):
        """Test if the update code items call is working"""
        jwt = self.login('admin', 'admin')        
        payload = {'code_lang': 'php', 'content': 'Unit test content update', 'title': 'Unit test title update'}
        headers = {'content-type': 'application/json', 'Authorization': jwt}
        response = self.client.put('/api/code/items/update/1', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['message'], "Code example item successfully updated")
        response = self.client.get('/api/code/items/')
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][0]['title'], "Unit test title update")


    def test_get_code_item_lang_php(self):
        """Test if the php language code items call is working"""
        jwt = self.login('admin', 'admin')
        payload = {'code_lang': 'php'}
        headers = {'content-type': 'application/json'}
        response = self.client.post('/api/code/items/code_lang/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][1]['title'], "Anti clickjacking headers")


    def test_get_code_item_lang_asp(self):
        """Test if the asp language code items call is working"""
        jwt = self.login('admin', 'admin')
        payload = {'code_lang': 'asp'}
        headers = {'content-type': 'application/json'}
        response = self.client.post('/api/code/items/code_lang/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][1]['title'], "Anti clickjacking headers")


    def test_get_code_item_lang_java(self):
        """Test if the java language code items call is working"""
        jwt = self.login('admin', 'admin')
        payload = {'code_lang': 'java'}
        headers = {'content-type': 'application/json'}
        response = self.client.post('/api/code/items/code_lang/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response_dict['items'][1]['title'], "CSRF Token JSF")


    def test_assert_403_project_get(self):
        headers = {'content-type': 'application/json'}
        response = self.client.get('/api/project/items/1')
        self.assertEqual(response.status_code, 403)

    def test_assert_403_project_new(self):
        payload = {'description': 'Unit test description project', 'name': 'Unit test name project', 'version': 'version 1.0'}
        headers = {'content-type': 'application/json'}
        response = self.client.put('/api/project/items/new', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_assert_403_project_update(self):
        payload = {'description': 'Unit test description project update', 'name': 'Unit test name project update', 'version': 'version 1.1'}
        headers = {'content-type': 'application/json'}
        response = self.client.put('/api/project/items/update/1', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_assert_403_project_delete(self):
        payload = {'test': 'test'}
        headers = {'content-type': 'application/json'}
        response = self.client.delete('/api/project/items/delete/1', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_assert_403_user_create(self):
        payload = {'email': 'test_user123@owasp.org', 'privilege': 1}
        headers = {'content-type': 'application/json'}
        response = self.client.put('/api/user/create/', data=json.dumps(payload), headers=headers)
        self.assertEqual(response.status_code, 403)


class TestDB(unittest.TestCase):


    def test_init_md_knowledge_base(self):
        """Test if the init markdown of kb items is working"""
        self.assertTrue(init_md_knowledge_base())
        os.remove(os.path.join(app.root_path, 'db.sqlite_schema'))


    def test_init_md_checklists(self):
        """Test if the init markdown of checklist items is working"""
        self.assertTrue(init_md_checklists())
        os.remove(os.path.join(app.root_path, 'db.sqlite_schema'))


    def test_init_md_code_examples(self):
        """Test if the init markdown of code items is working"""
        self.assertTrue(init_md_code_examples())
        os.remove(os.path.join(app.root_path, 'db.sqlite_schema'))


    def test_init_db(self):
        """Test if the init db is working"""
        init_db()


class TestSecurity(unittest.TestCase):

    def test_val_alpha(self):
        """Test if the val_alpha method is working"""
        connect_db()
        self.assertTrue(val_alpha("woopwoop"))
        self.assertFalse(val_alpha("woop %$*@><'1337"))
        #self.assertFalse(val_alpha("woop woop 1337"))

    def test_val_num(self):
        """Test if the val_num method is working"""
        self.assertTrue(val_num(1337))
        #self.assertFalse(val_num("woopwoop"))        
        #self.assertFalse(val_num("woop woop 1337"))
        #self.assertFalse(val_num("woop %$*@><'1337"))

    def test_val_alpha_num(self):
        """Test if the val_alpha_num method is working"""
        self.assertTrue(val_alpha_num("woop woop 1337"))
        #self.assertFalse(val_alpha_num("woop %$*@><'1337"))


    def test_val_float(self):
        """Test if the val_float method is working"""
        self.assertTrue(val_float(10.11))
        #self.assertFalse(val_float(1337))
        #self.assertFalse(val_float("woop woop 1337"))
        #self.assertFalse(val_float("woop %$*@><'1337"))
    


if __name__ == '__main__':
    unittest.main()
