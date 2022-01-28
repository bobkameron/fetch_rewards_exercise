from django.shortcuts import render

# Create your views here.

import json 
from datetime import datetime 
from dateutil import parser 

from math import inf 

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.db.models import Q, Sum , Model 
from django.views.decorators.csrf import csrf_exempt

from .models import Payer, Transaction 

def get_payer_points_sum(payer = None):
    '''
    Input: payer must be a string or None 

    Returns the nonnegative sum of the unspent points associated with payer. If payer is None,
    then returns the sum of all unspent points for all payers. 
    '''
    if payer is None:
        transactions = Transaction.objects.all()
    else:
        transactions = Transaction.objects.filter(payer = payer)

    points =  transactions.aggregate(Sum('points'))['points__sum']

    if points is None:
        return 0
    else:
        return points 


def add_transaction(data):
    '''
    Input: data must be a dict

    Returns a JsonResponse of status code 2xx indicating successful creation of a new transaction,
    or JsonResponse of status code 4xx indicating failure to create a new transaction as the request
    was invalid.
    '''

    try:
        payer_name , points, timestamp  = data['payer'].strip(), \
            int(data ['points']), parser.parse(data['timestamp'].strip())
    except KeyError:
        return  JsonResponse( {"error": "Request must have keys 'payer', 'points', and 'timestamp'"}, status = 400)
    except parser.ParserError:
        return JsonResponse( {"error": "Unable to parse timestamp. Should be in format 'YYYY-MM-DDTHH:MM:SSZ'"},\
             status = 400)
    except ValueError:
        return JsonResponse( {"error": "value for key 'points' should be an integer"}, status = 400)
    except:
        return JsonResponse( {"error": "payer should be a string"}, status = 400)


    if points == 0: 
        return JsonResponse( {"error": "Transaction should have non-zero points"}, status = 400)
    if len(payer_name) == 0 :
        return JsonResponse( {"error": "payer should have at least one non whitespace character"}, status = 400)

    try:
        payer = Payer.objects.get(name = payer_name)
    except:
        if points < 0:
            return JsonResponse( {"error": "No payer's balance may go negative"}, status = 400)
        payer = Payer (name = payer_name)
        payer.save()

    current_points = get_payer_points_sum(payer)
    
    if current_points + points < 0: 
        return JsonResponse( {"error": "No payer's balance may go negative"}, status = 400)

    transaction = Transaction ( payer = payer , points = points, timestamp = timestamp )

    transaction.save()

    return JsonResponse({'success': "Successfully added transaction"}, status = 201) 


def spend_points(data):
    '''
    Input: data must be a dict

    Returns a JsonResponse of status code 2xx for successfully spending a nonnegative number of points,
    or a JsonResponse of status code 4xx for failure to spend points (invalid request).

    For a successful request, a JSON array is sent back to the client in the body of the http response
    with information about how many points were spent from each payer that had a transaction that was spent. 
    '''

    try:
        spend_amount = int(data['points'])
    except KeyError:
        return JsonResponse( {"error": "Request must be JSON object with key 'points'"}, status = 400)
    except ValueError:
        return JsonResponse( {"error": "Value associated with 'points' must be an integer"}, status = 400)

    if spend_amount < 0:
        return JsonResponse( {"error": "Cannot spend a negative amount"}, status = 400)
    if spend_amount == 0:
        return JsonResponse( [], status = 200, safe = False)

    sum_points = get_payer_points_sum()

    if spend_amount > sum_points:
        return JsonResponse( {"error": "Cannot spend a negative amount of points"}, status = 400)

    transactions = Transaction.objects.filter().order_by('timestamp')
    
    result = {}

    for transaction in transactions:
        '''
        Loop through all transactions, spending each of them and deleting the oldest one until
        the amount left to spend is 0. 
        '''
        if spend_amount == 0:
            break 
        points = transaction.points 
        payer_name = transaction.payer.name

        if points < 0:
            to_spend = points 
            transaction.delete()
        if points >= 0:
            to_spend = min(spend_amount, points )
            if to_spend == points:
                transaction.delete()
            else:
                transaction.points = points - to_spend
                transaction.save()

        if payer_name not in result:
            result[payer_name] = -to_spend 
        else:
            result[payer_name] -= to_spend 

        spend_amount -= to_spend 

    return_value = []

    for payer in result:
        return_value.append( { 'payer':  payer, 'points': result[payer]} )

    return JsonResponse(return_value, safe = False, status = 201 )
    

def get_balance():
    '''
    Returns a JSONResponse indicating the balance associated with all payers. 
    The balance of each payer is nonnegative and could be 0.
    
    '''

    payers = Payer.objects.all()
    result = dict() 

    for payer in payers:
        result [payer.name] = get_payer_points_sum(payer)
    return JsonResponse( result , status = 200 ) 


@csrf_exempt
def index ( request):
    '''
    See the README for details on the specification. 
    The README has detailed specifications for the expected input/output of every valid request.
    '''
    method = request.method 

    if method == "PUT" or method == "DELETE":
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # Any PUT/DELETE request must have its body be a single JSON string. 
            return JsonResponse( {"error": "Request must be in JSON format"}, status = 400)

        if method == "PUT":
            return add_transaction(data)
        else:
            return spend_points(data)

    elif method == 'GET':
        return get_balance()

    else:
        return JsonResponse( {"error": "Invalid Request Method"}, status = 405)
