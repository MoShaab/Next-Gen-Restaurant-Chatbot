from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

import db_helper
import generic_helper
inprogress_orders={}
app = FastAPI()

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        'order.add-context:ongoing-order': add_to_order,
     #   'order.remove-context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking':track_order
    }

    return intent_handler_dict[intent](parameters, session_id)

def add_to_order(parameters:dict, session_id: str):
    food_items = parameters["food-item"]
    quantities = parameters["number"]
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities?"
    else:
        new_food_dict = dict(zip(food_items, quantities))
        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"so far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I am having a problem placing your order. Please place a new order"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I could not place your order due to a backend error."\
                                "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order"\
                               f"Here is your order id # {order_id}."\
                               f"Your total is {order_total} which you can pay at the time of delivery!"
        del inprogress_orders[session_id]

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })


def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )
        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id

def track_order(parameters: dict):
    order_id = int(parameters['number'])
    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"the order status for order_id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order_id {order_id}"

    return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

#  inprogress_orders ={
#     'session_id_1': {"pizza": 2, "samosa": 1, "anjera": 1},
#     'session_id_2': {"biryani": 2, "meat": 1, "anjera": 1}
# }
