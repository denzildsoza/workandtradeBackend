from flask import Flask, jsonify, request
from threading import Thread
from multiprocessing import Process
from utils import FilteredSymbolList,ThreadRapper,CreateOrderData
from fyers_api import fyersModel
from fyers_api.Websocket import ws
from fyers_api import accessToken
from os import getcwd

#create instance of flask
app = Flask(__name__)

#constants
orderDetails = {}
orders = []
process = {}
fyers = None
fyersSocket = None
message = ''
client_id="3H021OQ8ZI-100"
secret_key="PPEJLUL3HA"
# redirect_uri="https://trade.fyers.in/api-login/redirect-uri/index.html"http://127.0.0.1:5000
redirect_uri="https://algowice.tech/createsession"
response_type="code"
grant_type="authorization_code"
state="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9sdfhioehskdfjhsurhs.eyJpc3MiOiJhcGkubG9naskjhekshfksdhfsheufW4uZnllcnMuaW4iLCJpYXQiskdfjhskefksuefsfOjE2OTA3Mjk0MzQsImV4cCI6MTY5MDc1OTQzNCwibmJmIjoxNjkwNzI4ODM0LCJhdWQiOiJbXCJ4OjBcIiwgXCJ4OjFcIiwgXCJ4OjJcIiwgXCJkOjFcIiwgXCJkOjJcIiwgXCJ4OjFcIiwgXCJ4OjBcIl0iLCJzdWIiOiJhdXRoX2NvZGUiLCJkaXNwbGF5X25hbWUiOiJYRDA4Njg1Iiwib21zIjoiSzEiLCJoc21fa2V5IjoiYjVkOTdlYTE1YmY5MWRhMzUxOTJmODUzZTNiNWQ2YTEwMGQyYzc2OTEwMTk3MjIyZWVlZjY5ZjIiLCJub25jZSI6IiIsImFwcF9pZCI6IjNIMDIxT1E4WkkiLCJ1dWlkIjoiMzJjZDI1MDEzNWEyNDc3NWI5YzI1NzY2MGUyZGNiZWYiLCJpcEFkZHIiOiIwLjAuMC4wIiwic2NvcGUiOiIifQ._vG9oFXxZfzl1Ux0G6-timgKcG046U7hbnH8Q"
auth = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.easdasdasyJpc3MiOiJhcGkubG9naW4uZnllcnMasduaW4iLCJpYXQiOjE2OTA3Mjk0MzQsImV4cCI6MTY5MDc1OTQzNCwibmJmIjoxNjkwNzI4ODM0LCJhdWQiOiJbXCJ4OjBcIiwgXCJ4OjFcIiwgXCJ4OjJcIiwgXCJkOjFcIiwgXCJkOjJcIiwgXCJ4OjFcIiwgXCJ4OjBcIl0iLCJzdWIiOiJhdXRoX2NvZGUiLCJkaXNwbGF5X25hbWUiOiJYRDA4Njg1Iiwib21zIjoiSzEiLCJoc21fa2V5IjoiYjVkOTdlYTE1YmY5MWRhMzUxOTJmODUzZTNiNWQ2YTEwMGQyYzc2OTEwMTk3MjIyZWVlZjY5ZjIiLCJub25jZSI6IiIsImFwcF9pZCI6IjNIMDIxT1E4WkkiLCJ1dWlkIjoiMzJjZDI1MDEzNWEyNDc3NWI5YzI1NzY2MGUyZGNiZWYiLCJpcEFkZHIiOiIwLjAuMC4wIiwic2NvcGUiOiIifQ.sasadsadsad.sadsad-_vG9oFXxZfzl1Ux0G6-timgKcG046U7hbnH8QXXujsY"
#Interceptor for authentication
@app.before_request
def before_request_func():
    if request.path.startswith('/createsession') :
        stateRes = request.args.get('state')
        if stateRes == state:
            return request 
        else:
            return jsonify({'message':'not authenticated'}),404
    authTocken = request.headers.get('Authorization')
    if authTocken != auth :
        return jsonify({'message':'not authenticated'}),404

#Define the api end points
# Create fyers object
@app.route('/createsession')
def createFyersObject():
    try:
        global fyers,fyersSocket
        try:
            auth_code = request.args.get('auth_code')
        except:
            return jsonify({'message':'could not find auth code'}),404
        session=accessToken.SessionModel(client_id=client_id,secret_key=secret_key,redirect_uri=redirect_uri, response_type=response_type, grant_type=grant_type,state=state)
        response = session.generate_authcode()  
        session.set_token(auth_code)
        response = session.generate_token()
        access_token = response["access_token"]
        wsAccessToken = f"3H021OQ8ZI-100:{access_token}"
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,log_path=f"{getcwd()}")
        fyersSocket = ws.FyersSocket(access_token=wsAccessToken,run_background=False,log_path=f"{getcwd()}")
        return jsonify({'message':'Success created a session'}),200
    except:
        return jsonify({'message':'Error occured while authenticating'}),404



# API endpoint to get all orders
@app.route('/orders', methods=['GET'])
def getOrders():
    try:
        global orders
        return jsonify(orders),200
    except:
        return jsonify({'message':'Error occured while fetching orders'}),404



# API endpoint to add a new order
@app.route('/placeorder', methods=['POST'])
def PlaceOrders():
    req = request.json
    print(req)
    global message
    message = 'pending'
    try:
        global orderDetails
        req = request.json
        orderDetails = req
        while True:
            if message != 'pending': 
                print(message)
                break
                
        if message == 'success':
            message = ''
            orders.append(req)
            return jsonify({'message':'Successfully placed the Order'}),200
        else:
            message = ''
            return jsonify({'message':'Error occured while placing orders'}),404
    except:
        message = ''
        return jsonify({'message':'Error occured while placing orders'}),404


# API endpoint to delete a order
@app.route('/orders/<orderId>', methods=['DELETE'])
def deleteOrders(orderId):
    global orders
    try:
        process[orderId].terminate()
        orders = [m for m in orders if m['id'] != orderId]
        return jsonify(orders),200
    except:
        return jsonify({'message':'Error occured while deleting the order'}),404 
        

if __name__ == '__main__':
    filteredSymbolList = FilteredSymbolList()
    Thread(target=lambda:app.run()).start()
    while True:
        if(orderDetails):
            try:
                print(type(orderDetails))
                orderDataObject = CreateOrderData(filteredSymbolList,orderDetails)
                p = Process(target=ThreadRapper, args=(orderDataObject,fyers,fyersSocket,))
                p.start()
                process[orderDetails['id']] = p
                p = None
                orderDetails = {}
                message = 'success'
            except Exception as error:
                message = 'error'
                orderDetails = {}
                p = None
                print(error)













            # API endpoint to get a specific book
# @app.route('/Orderss/<int:book_id>', methods=['GET'])
# def getOrdersById(book_id):
#     book = next((book for book in orders if book['id'] == book_id), None)
#     if book:
#         return jsonify(book)
#     else:
#         return jsonify({"error": "Book not found"}), 404

# API endpoint to update a order
# @app.route('/orders/<int:book_id>', methods=['PUT'])
# def updateOrders(book_id):
#     book = next((book for book in orders if book['id'] == book_id), None)
#     if book:
#         book['title'] = request.json.get('title')
#         book['author'] = request.json.get('author')
#         return jsonify(book)
#     else:
#         return jsonify({"error": "Book not found"}), 404