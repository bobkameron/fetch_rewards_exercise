from django.test import TestCase, RequestFactory , Client 

import json 
from django.urls import reverse 

from .views import index 

# Create your tests here.

class TestPoints (TestCase):
    '''
    Testing stra
    
    
    '''


    def test_get(self):
        c = Client() 
        response = c.get(reverse("points"))
        self.assertEqual(response.status_code, 200 )

        print(response.content)

        data = json.loads( response.content )
        print(data)
        self.assertEqual (len(data), 0 )

    def test_put(self):
        c = Client()
        
        response = c.put(reverse("points"),content_type='application/json', \
            data = "  " )

        print(response.content)
    
       
        
        
    