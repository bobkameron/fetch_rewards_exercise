from django.test import TestCase, RequestFactory , Client 

import json 
from django.urls import reverse 

from .views import index 

# Create your tests here.


 
def get_balance(client):
    return client.get(reverse("points"))

  
def add_transaction(client , payer, points, timestamp):
    return client.put(reverse("points"),content_type='application/json', \
            data = json.dumps({'payer':payer, 'points':points, 'timestamp': timestamp }))

def spend( client, points):
    return client.delete(reverse('points'), content_type='application/json',\
        data = json.dumps({'points':points}))

class TestPoints (TestCase):


    '''
    Unit Testing strategy: 

    We will test each of the partitions in at least one test case, without guaranteeing that
    each partition will be tested in its own test case. 

    Testing partitions for HTTP GET (returning the balance), PUT (adding a new transaction), and 
    DELETE (spending points) requests to the url '/points/':

    Partitions for GET:

        Partition by number of different payers in our database:
        1. 0
        2. 1
        3. Multiple different payers 

        Partition by value of each payer's point balance:
        1. 0
        2. A positive integer


    Partitions for PUT:

        Partition by if a transaction for same payer had previously been added:
        1. True
        2. False 

        Partition by number of points in the transaction:
        1. < 0 
        2. = 0 (should return http error)
        3. > 0 

        Partition by the sum of new payer's point balance including the new transaction:
        1. sum < 0 (should not add the transaction and instead return http error)
        2. sum = 0 
        3. sum > 0 
        

    Partitions for DELETE:

        Partition by amount that is spent:
        1. 0 points
        2. Positive number of points. 

        Partition by total sum of all payers' balances after spending the number of points:
        1. Sum < 0 (points should not be spent and an error should be returned)
        2. Sum = 0 
        3. Sum > 0
    

    Testing functions strategy:

    
        Test no transactions

        Test one added transaction with spends and balance requests (add, get, spend, get, spend, get ) - all valid requests 
        
        Test unsuccessfully adding a transaction

        Test unsuccessfully spending more than the sum of all payers' balance 

        Test multiple valid transactions added to the same payer

        Test multiple valid transactions added to different payers 

    '''

    def test_no_transactions(self):
        c = Client() 
        response = get_balance(c)
        self.assertEqual(response.status_code, 200 )

        data = json.loads( response.content )
        self.assertEqual (len(data), 0 )

    def test_one_transaction(self):
        c = Client()
        
        payer = 'dannon'
        amount = 1000

        response_add = add_transaction(c, payer , amount,"2020-11-02T14:00:00Z" ) 
        result_add = get_balance(c)

        self.assertEqual(response_add.status_code, 201)

        data = json.loads(result_add.content)

        self.assertEqual(len(data),1 )
        self.assertEqual ( data[payer], amount )

        spend_nothing = spend(c, 0)
        self.assertEqual(spend_nothing.status_code, 200)
        data1 = json.loads(get_balance(c).content)
        self.assertEqual( data1[payer], amount )
        

        spend_amount = 500
        response_delete = spend(c, spend_amount )
        self.assertEqual(response_delete.status_code, 201)
        
        data_delete = json.loads(response_delete.content)

        self.assertEqual( len(data_delete), 1 )
        self.assertEqual(data_delete[0], { "payer": payer, "points": -spend_amount }, )
        
        response_spend_all = spend(c, spend_amount)
        self.assertEqual(response_spend_all.status_code, 201 )
        data_spend_all = json.loads(response_spend_all.content)

        self.assertEqual(len(data_spend_all), 1)
        self.assertEqual( data_spend_all[0], { "payer": payer, "points": -spend_amount }  )

        result_spend_all = get_balance(c)
        get_data = json.loads(result_spend_all.content)
        self.assertEqual(len(get_data),1 )
        self.assertEqual(get_data[payer], 0)
    
    def test_invalid_add_transaction(self):
        c = Client()
        payer = 'dannon'
        amount = 1000
        timestamp1 = "2020-11-02T14:00:00Z"
        timestamp2 = "2020-12-03T14:00:00Z"

        _ = add_transaction(c, payer , amount,timestamp1 )
        invalid_add = add_transaction( c, payer, - (amount * 2), timestamp2)
        print(invalid_add.status_code, 'invalid add transaction status code')

        self.assertTrue(  399 <  invalid_add.status_code < 500 )
        final_balance = get_balance(c)
        data = json.loads(final_balance.content)
        self.assertTrue( len(data) == 1 and data[payer] == amount  )

        invalid_add_zero = add_transaction(c, payer, 0, timestamp2)
        self.assertTrue(399 < invalid_add_zero.status_code < 500)
        data = json.loads(get_balance(c).content)
        self.assertTrue (len(data) == 1 and data[payer] == amount)
        
    def test_invalid_spend (self):
        c = Client()
        payer = 'toyota'
        amount = 2000
        timestamp1 = "2021-11-02T14:00:00Z"

        invalid_spend =  spend ( c, amount)
        self.assertTrue ( 399 <  invalid_spend.status_code < 500 )
        _ = add_transaction(c, payer, amount, timestamp1 )
        
        invalid_spend2 = spend (c, amount + 1)
        self.assertTrue(399 < invalid_spend2.status_code < 500)

        result = get_balance(c)
        data = json.loads(result.content)
        self.assertTrue(len(data) == 1 and data [payer] == amount)

    def test_multiple_valid_add_transactions_same_payer(self):
        c = Client()
        payer = 'toyota'
        amount = 2000
        timestamp1 = "2021-11-02T14:00:00Z"
        timestamp2 = "2022-12-02T14:00:00Z"

        add_transaction ( c, payer, amount, timestamp1)
        add_transaction ( c, payer, amount, timestamp2)
        add_transaction ( c, payer, amount, timestamp1)

        result = get_balance(c)
        data = json.loads(result.content)

        self.assertTrue( len(data) == 1 and data['toyota'] == amount * 3)

        result_spend = spend(c, amount * 3)
        data_spend = json.loads(result_spend.content)

        self.assertTrue(result_spend.status_code == 201 and len(data_spend) == 1 \
            and data_spend[0]['payer'] == payer and data_spend[0]['points'] == - 3 * amount   )

        result_final = get_balance(c)
        data= json.loads(result_final.content)
        print(data, '  data  ')
        self.assertTrue (len(data) == 1 and data[payer] == 0 )

    def test_multiple_valid_add_transactions_different_payers(self):
        c = Client() 

        payer1 = 'DANNON'
        payer2 = 'UNILEVER'
        payer3 = 'MILLER COORS'

        payers = [ payer1, payer2, payer1, payer3, payer1 ]
        

        timestamp1 = "2020-11-02T14:00:00Z"
        timestamp2 = "2020-10-31T11:00:00Z"
        timestamp3 = "2020-10-31T15:00:00Z" 
        timestamp4 = "2020-11-01T14:00:00Z"
        timestamp5 = "2020-10-31T10:00:00Z"
        
        timestamps = [ timestamp1, timestamp2, timestamp3, timestamp4, timestamp5 ]
        points = [ 1000, 200, -200 , 10000, 300]

        for i in range (len(payers)):
            add_transaction(c,payers[i], points[i], timestamps[i])
        
        spend_amount = 5000 
        result_spend = spend(c, spend_amount )

        expected = [
            { "payer": "DANNON", "points": -100 },
            { "payer": "UNILEVER", "points": -200 },
            { "payer": "MILLER COORS", "points": -4700 }
        ]

        self.assertEquals(result_spend.status_code, 201)
        data_spend = json.loads(result_spend.content)
        self.assertEquals( len(data_spend), 3)

        for dic in expected:
            assert( dic in data_spend)

        balance = get_balance(c)
        data = json.loads(balance.content)
        self.assertEquals(data, {
            "DANNON": 1000,
            "UNILEVER": 0,
            "MILLER COORS": 5300
        })

        spend_amount2 = 6300 
        result_spend2 = spend(c, spend_amount2 )

        expected2 = [
            { "payer": "DANNON", "points": -1000 },
            { "payer": "MILLER COORS", "points": -5300 }
        ]

        data_spend2 = json.loads(result_spend2.content)
        self.assertEquals(len(data_spend2), 2)
        for dic in expected2:
            assert (dic in data_spend2)

        balance2 = get_balance(c)
        data2 = json.loads(balance2.content)
        self.assertEquals(data2, {
            "DANNON": 0,
            "UNILEVER": 0,
            "MILLER COORS": 0
        })


        