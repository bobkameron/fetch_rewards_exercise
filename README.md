Fetch Rewards Points

This project 




Here is the specification of the API and routes for the project: 


/points/ GET 

Any HTTP GET request simply returns a JSON object in an HTTP response body 
that specifies the remaining balance for every payer that ever added 
a valid transaction. The JSON response is in the format:

{ "company_name": points1 , "company_name2":points2 ,  etc.  }

mapping strings of payer names (company_name) with the number of points (a non-negative integer) 
left in the payer balance. 

HTTP status code of 200 is returned along with the HTTP response. 


/points/ PUT 

A valid HTTP PUT request simply adds transactions for a specific payer and date. It should have the 'Content-Type' header set to 'application/json',
and the body of the request should be a single JSON object in the format:

{ "payer": company_name , "points": points , "timestamp": iso_datetime }

where company_name is a string referring to the unique UTF-8 case-sensitive name of the payer that the 
transaction should record, points is a non-zero integer, and iso_datetime should be a string in the format
"YYYY-MM-DDTHH:MM:SSZ" specifying the Year, month, day, hour, minute, second, and timezone that the 
transaction should be recorded. 

The string company_name should have at least one non whitespace character. Any leading or trailing
whitespace is stripped when the transaction is recorded, so "Dannon" is the same as " Dannon   ". However, this API is case-sensitive, so recording a transaction for the payer "DANNON" is different from one added for "dannon". 

Additionally, only non-zero points are allowed to be recorded in a transaction. The sum of all the previous
transactions associated with the payer + points must not be less than zero (no payer's points can go
negative).

Any valid HTTP JSON PUT request following the above specification will successfully add the transaction by adding the number of points specified at a timestamp associated with the payer, and return an HTTP response with status code 201. Otherwise, an HTTP response with error status code 4xx is returned indicating the failure to add the transaction. 


/points/ DELETE

A valid HTTP DELETE request simply spends points. The 'Content-Type' header should be set to 'application/json', and the body of the request should be a single JSON object in the format:

{ "points": points }

Here, points should be a non-negative integer indicating the number of points that the user wants to spend. The number of points that the user wants to spend must be less than or equal to the total number of points that the user has left in their balance. 

If the HTTP DELETE request follows the above specifications, then the points are spent in a manner where the oldest points are spent first (oldest based on transaction timestamp, not the order they’re received). An HTTP response of status code 204 is returned (200 if no points were spent if the client sends in a request of '{"points":0}' requesting no points to be spent ), and the body of the response is in the following format:

[
{ "payer": company_name1 , "points": points1 },
{ "payer": company_name2 , "points": points2 },
    ...
]

Which simply indicates the net change in the number of points associated with each payer for any payer that had a transaction that was spent in full or partially. 

An invalid HTTP DELETE request returns an HTTP response with status code 4xx indicating failure to spend any points. 



