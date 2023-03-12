from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from datetime import datetime as dt
from datetime import timedelta
from pymongo import MongoClient
from bson import ObjectId
import smtplib
from email.mime.text import MIMEText
from django.core.mail import send_mail
import bson
import datetime


# Create your views here.

def read_data_from_json(dpath='overview/static/itemsdata.json'):

    with open(dpath) as f:
        data = json.load(f)
    return data


def connect_mongo(db_name='test'):
    client=MongoClient('mongodb+srv://test_db_user:wy1d3VNenoBmkfx5@cluster0.ohz7z5a.mongodb.net/?retryWrites=true&w=majority')
    db=client[db_name]

    return client,db

@api_view(['GET'])
def overview(request):
    client,db = connect_mongo()
    collection = db['items']

    all_items = collection.find()
    data = []
    for item in all_items:
        
        date_str = item["date"]
        item['price']=int(item['price'])
        #date_obj=dt.strftime(date_str,"%Y-%m-%d") #string formate date
        date_obj=dt.strptime(date_str,"%Y-%m-%d") #date formate
        collection.update_one({"_id": item["_id"]}, {"$set": {"date": date_obj}})
        item['_id'] = str(item['_id'])
        data.append(item)

    client.close()
    return Response(data)


@api_view(['GET'])
def category_data(request):
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    catg_data = []
    for item in all_items:
        item['_id']= str(item['_id'])

        catg_data.append(item)
        # if item['category'] in catg_data:
        #     [catg_data[item['category']]].append(item)
        # else:
        #     catg_data[item['category']]=(item)
    client.close()

    # print(catg_data)      
    return render(request, 'overview/catg.html', {'catg_data': catg_data[:10]})          


@api_view(['GET'])
def date_wise_data(request):
    date = request.GET.get('date')
    date_obj=dt.strptime(date,"%Y-%m-%d")
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    date_data = list()
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['date']==date_obj:
            date_data.append(item)  
    client.close()        
    return Response((date_data))        


@api_view(['GET'])
def date_catg_wise_data(request):
    date, catg = request.GET.get('date'), request.GET.get('catg')
    date_obj=dt.strptime(date,"%Y-%m-%d")
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    date_catg_data = list()
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['date'] == date_obj and item['category'] == catg:
            date_catg_data.append(item)
    client.close()        
    return Response(date_catg_data)         


@api_view(['POST'])
def add_new_item(request):
    data = read_data_from_json()
    new_item = {
        "_id": len(data)+1,
        "item": "Vimbar",
        "category": "daily use",
        "price": "1000",
        "date": "2022-12-30"
    },
    data.append(new_item)
    with open('overview/static/itemsdata.json', 'w') as f:
        f.write(json.dumps(data))
    return Response(new_item)

@api_view(['POST']) #Sending Email Add item
def add_item(request):

    client,db = connect_mongo()
    collection = db['items']

    new_item = request.data['item']
    collection.insert_one(new_item)

    send_mail(
        'New Add item', #Subject
        f":{new_item}",  #body
        'rachitsingh06938@gmail.com',  #username
        ['mukeshsingh08082002@gmail.com'], #jis pe mail send karna hai
        fail_silently=False,
    )
    print("send email successfully")
    new_item["_id"]=str(new_item["_id"])
    client.close() 
    return Response({'added_item':new_item})


@api_view(['PATCH'])
def update_item(request):

    client,db = connect_mongo()
    collection = db['items']
    
    update_item= request.data.get('update_item')
    id=update_item['_id']
    del update_item['_id']

    result=collection.update_one({'_id':ObjectId(id)},{"$set":update_item})
    client.close()
    return Response(result.modified_count) 


@api_view(['GET']) # Date ke item ka maximum price.
def date_max_itm_price(request):
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    max=0
    itm=''
    date= request.GET.get('date')
    date_obj=dt.strptime(date,"%Y-%m-%d")
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['date']==date_obj and int(item['price'])>max:
            max=int(item['price'])
            itm=item['item']
            category=item['category']
    client.close()        
    return Response({category:{'item':itm,'Maximum_Price':max}})


@api_view(['GET']) #Count item and price
def count_itm(request):
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    count_dict=dict()
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['item'] in count_dict:
            count_dict[item['item']]['count']+=1
            count_dict[item['item']]['price']+=int(item['price'])
        else:
            count_dict[item['item']]={'count':1,'price':int(item['price'])}
    client.close()             
    return Response(count_dict)
                                   
@api_view(['GET']) #Count item_price and latest_date
def cunt_itm_price(request):
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    latest_date=dict()
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['item'] in latest_date:
            latest_date[item['item']]['count']+=1
            latest_date[item['item']]['price']+=int(item['price'])
            latest_date[item['item']]['date']=max(dt.strptime(latest_date[item['item']]['date'],'%Y-%m-%d'),
                                                   dt.strptime(item['date'],'%Y-%m-%d')).strftime('%Y-%m-%d')
        else:
            latest_date[item['item']]={'count':1,'price':int(item['price']),
                                        'date':item['date']}
    client.close()                                    
    return Response(latest_date)                                                                               


@api_view(['GET']) # latest_date and item
def latest_date(request):
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['date']<=dt.strftime(dt.today(),'%Y-%m-%d'):
            l_d={item['date']:[{'item':item['item'],'price':item['price']}]}
    client.close()        
    return Response(l_d)
                                      

@api_view(['GET']) #Particular_date_data
def Particular_date_data(request):
    date = request.GET.get('date')
    date_obj=dt.strptime(date,"%Y-%m-%d")
    client,db = connect_mongo()
    collection = db['items']

    all_items=collection.find()
    parti_det=dict()
    for item in all_items:
        item['_id']= str(item['_id'])
        if item['date']==date_obj:
            if item['date'] in parti_det:
                parti_det[item['date']]['item'].append([item['item']])
                parti_det[item['date']]['total_item']+=1
                parti_det[item['date']]['total_price']+=int(item['price'])
            else:
                parti_det[item['date']]={'total_item':1,
                                          'total_price':int(item['price']),
                                         'item':[item['item']],}
    client.close()                                     
    return Response(parti_det)                                         


@api_view(['GET'])
def filter_catg(request):#filter_catg
    catg = request.data.get('catg_filter',[])
    if not catg:
        return Response({"error": "category data not received"})

    client, db = connect_mongo()
    collection = db['items']
    result = {}
    
    all_items = collection.find({'category': {'$in': catg}})
    for item in all_items:
        item['_id'] = str(item['_id'])
        result[item['_id']] = item
        
    client.close()
    return Response(result)

# new
# def connect_mongo(db_name='hisabkitab'):
#     client=MongoClient('mongodb://localhost:27017')
#     db=client[db_name]

#     return client,db

@api_view(["GET", "POST", "PATCH"])
def user_registrations(request):
    client,db = connect_mongo()
    collection = db['user_resistation']
    if request.method == "GET":
        # handle GET request
        users = collection.find()
        user_list = []
        for user in users:
            user["_id"] = str(user['_id'])
            user["signup_date"] = str(user["signup_date"])
            user_list.append(user)
        return Response(user_list)
    
    elif request.method == "POST":
        # handle POST request
        try:
            now = datetime.datetime.utcnow()
            username = request.data.get("username")
            password = request.data.get("password")
            email = request.data.get("email")
            signup_date = bson.ObjectId.from_datetime(now)
            user_name = collection.find_one({"username":username})
            user_email = collection.find_one({"email":email})
            if user_name:
                return Response({"error": "That username is taken. Try another"})
            elif user_email:
                return Response({"error": "That email is taken. Try another"})
            else:
                user ={"_id":email,
                    "username": username,
                    "password": password,
                    "email": email,
                    "signup_date": signup_date}
                status = collection.insert_one(user)
                if status.acknowledged:
                    #collection = db["user_data"]
                    #cont= db.collection.aggregate([{"$match": { "_id": username}},{"$project": {"dataSize": { "$size": { "$objectToArray": "$data" } }}}])
                    #items = {}


                    user_items = {"_id":username,"data":{}}
                    user_status=db["user_data"].insert_one(user_items)
                    if user_status.acknowledged:
                        return Response({"message": "new user inserted with id " + str(status.inserted_id)})


                #return Response({"message": "new user inserted with id " + str(status.inserted_id)})

        except Exception as e:
            return Response({"error": str(e)})
    
    elif request.method == "PATCH":
        # handle PATCH request
        email = request.data.get("email")
        password = request.data.get("password")
        count = collection.count_documents({"email":email})
        if count == 0:
            return Response({"error": "User not found"})
        else:
            collection.update_one({"email":email}, {"$set": {"password": password}})
            return Response({"message": "User password updated"})
    client.close()
    return Response({"message":"somthing is wrong"})
#for new database
def connect_mongo_1(db_name='Multiuserdb'):
    client=MongoClient('mongodb+srv://12mukesh:mukesh12@cluster0.ho3xvso.mongodb.net/test')
    db=client[db_name]

    return client,db


@api_view(["GET", "POST", "PATCH"])
def user_data(request):

    client,db = connect_mongo_1()
    collection = db["users"]
    if request.method == "GET":
        # handle GET request
        users = collection.find()
        user_list = []
        for user in users:
            user["_id"] = str(user['_id'])
            user["signup_date"] = str(user["signup_date"])
            user_list.append(user)
        return Response(user_list)
    
    elif request.method == "POST":
        # handle POST request
        try:
            now = datetime.datetime.utcnow()
            username = request.data.get("username")
            password = request.data.get("password")
            email = request.data.get("email")
            users_id =[]
            users_id.append(username)
            bank_name = request.data.get("bank_name")
            signup_date = bson.ObjectId.from_datetime(now)
            user_name = collection.find_one({"username":username})
            user_email = collection.find_one({"email":email})
            if user_name:
                return Response({"error": "That username is taken. Try another"})
            elif user_email:
                return Response({"error": "That email is taken. Try another"})
            else:
                user ={"_id":email,
                    "username": username,
                    "password": password,
                    "email": email,
                    "users_id": users_id,
                    "account": {bank_name:2600,"HDFC":1000},
                    "signup_date": signup_date}
                status = collection.insert_one(user)
                # if status == "success":
                #     collection = db["users data"]
                #     user_items = {"_id":username,"data":{"_id":}}
                if status.acknowledged: 
                    user_items = {"_id":username,"data":{}}
                    user_status=db["user_data"].insert_one(user_items)
                    if user_status.acknowledged:
                        return Response({"message": "new user inserted with id " + str(status.inserted_id)})


                return Response({"message": "new user inserted with id " + str(status.inserted_id)})

        except Exception as e:
            return Response({"error": str(e)})
    
    elif request.method == "PATCH":
        # handle PATCH request
        email = request.data.get("email")
        password = request.data.get("password")
        count = collection.count_documents({"email":email})
        if count == 0:
            return Response({"error": "User not found"})
        else:
            collection.update_one({"email":email}, {"$set": {"password": password}})
            return Response({"message": "User password updated"})
    client.close()
    return Response({"message":"somthing is wrong"})

def connect_mongo_2(db_name='hisabkitab_practice'):
    client=MongoClient('mongodb://localhost:27017')
    db=client[db_name]

    return client,db
        

@api_view(["POST", "GET"])
def add_members(request):
    client, db = connect_mongo_2()
    collection = db["users"]
    
    member_username = request.data.get("member_username")
    name_of_member = request.data.get("name_of_member")
    your_username = request.data.get("your_username")
    your_name = request.data.get("your_name")
    status = "Approved"

    request_data ={"your_name": your_name, "status": status}
    send_data = {"member_username": member_username, "name_of_member": name_of_member, "status": status}

    try:
        if status == "pending":
            status_message = collection.update_one({"username": member_username}, {"$set": {"members.pending."+your_username: request_data}})
            status_message_1 = collection.update_one({"username": your_username}, {"$set": {"family_admin": {"pending": {member_username: send_data}}}})
            if status_message.acknowledged:
                return Response({"message": "Member request added successfully."})
            else:
                return Response({"message": "Member request"})
        else:
            status_message = collection.update_one({"username": member_username}, {"$set": {"members.Approved."+your_username: request_data}})
            status_message_1 = collection.update_one({"username": your_username}, {"$set": {"family_admin.Approved."+member_username: send_data}})
            status_message_2 = collection.update_one({"username": member_username}, {"$unset": {"members.pending."+your_username: ""}})
            status_message_3 = collection.update_one({"username": your_username}, {"$unset": {"family_admin.pending."+member_username: ""}})
            if status_message.acknowledged and status_message_1.acknowledged and status_message_2.acknowledged and status_message_3.acknowledged:
                return Response({"message": "Member request approved successfully."})
            else:
                return Response({"message": "Failed to approve member request."})
    except Exception as e:
        return Response({"message": str(e)})
    finally:
        client.close()


#add new database
def connect_mongo_1(db_name='Multiuserdb'):
    client=MongoClient("mongodb+srv://12mukesh:mukesh12@cluster0.ho3xvso.mongodb.net/test")
    db=client[db_name]

    return client,db

counter=0
def generate_id():
    global counter
    counter+=1
    return "id_"+str(counter)
 
def update_account_balance(price, bnk,user_data):
    account_balance =user_data["account"].get(bnk,0) # current account balance for the given bank
    new_balance = account_balance - price  # calculate the new balance after subtracting the price
    user_data["account"][bnk] = new_balance  # update the balance for the given bank
    return new_balance

@api_view(['POST'])
def add_item_update_balance(request):
    client,db = connect_mongo_1()
    collection = db['users']
    data_collection=db['user_data']

    new_item = request.data['item']
    price = int(new_item['price'])
    new_item['date']=dt.strptime(new_item['date'],"%Y-%m-%d") #date formate
    bnk=request.data.get("item").get("bank_name")
     
    user_data=collection.find_one({"email":"mithilesh129@gmail.com"})
    update_account_balance(price,bnk,user_data)
    
    #collection.update_one({"email":"mithilesh129@gmail.com"},{"$set":{"account":user_data["account"]}})
    collection.update_one({"email":"mithilesh129@gmail.com"},{"$inc":{f"account.{bnk}":-price}})

    new_id=generate_id()
    status = data_collection.update_one({"_id":'mithilesh1234'},{"$set":{"data."+new_id:new_item}})
    send_mail(
        'New Add item', #Subject
        f"{new_item} Current Account Balance:{user_data}",  #body
        'rachitsingh06938@gmail.com',  #username
        ['mukeshsingh08082002@gmail.com'], #jis pe mail send karna hai
        fail_silently=False,
    )
    print("send email successfully")
    client.close()
    return Response({'added_item':new_item, 'account_balance':user_data["account"]}) 

