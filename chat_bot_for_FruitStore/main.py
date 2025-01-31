from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

# In-progress cart for each session (you can use a database for production purposes)
inprogress_carts = {}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        "add.fruit- context: ongoing-order": add_to_cart,
        "remove.fruit - context: ongoing-order": remove_from_cart,
        "generate.order - context: ongoing-order": complete_order
    }
    
    return intent_handler_dict[intent](parameters, session_id)

########################################
# to check the stock in db

def get_available_stock(fruit_name: str):
    cursor = db_helper.cnx.cursor()
    query = "SELECT quantity_in_kg FROM fruit_items WHERE fruit_name = %s"
    cursor.execute(query, (fruit_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else 0

########################################


#***************************************
# Modified add to cart function
def add_to_cart(parameters: dict, session_id: str):
    fruit_items = parameters["fruit_item"]
    quantities = parameters["number"]
    
    # Ensure fruit_items and quantities are lists
    if isinstance(fruit_items, str):
        fruit_items = [fruit_items]
    if isinstance(quantities, float):
        quantities = [quantities]
    
    if len(fruit_items) != len(quantities):
        return JSONResponse(content={"fulfillmentText": "Sorry, I don't understand. Please specify fruit item and quantity."})
    
    new_fruit_dict = {}
    out_of_stock_items = []
    
    for fruit, qty in zip(fruit_items, quantities):
        available_qty = get_available_stock(fruit)
        if available_qty >= qty:
            new_fruit_dict[fruit] = qty
        else:
            out_of_stock_items.append(fruit)
    
    if session_id in inprogress_carts:
        current_fruit_dict = inprogress_carts[session_id]
        for fruit, qty in new_fruit_dict.items():
            if fruit in current_fruit_dict:
                current_fruit_dict[fruit] += qty  # Add to existing quantity
            else:
                current_fruit_dict[fruit] = qty  # Add new fruit
    else:
        inprogress_carts[session_id] = new_fruit_dict
    
    order_str = generic_helper.get_string_from_fruit_dict(inprogress_carts[session_id])
    fulfillment_text = f"So far you have {order_str}. Do you want anything else?"
    
    if out_of_stock_items:
        fulfillment_text += f" Unfortunately, {', '.join(out_of_stock_items)} is out of stock right now. Do you want anything else?"
    
    return JSONResponse(content={"fulfillmentText": fulfillment_text})

# ****************************************************************
 

def complete_order(parameters:dict, session_id:str):    
    if session_id not in inprogress_carts:
        fulfillment_text = "I am having trouble in finding your order"
    else:
        order = inprogress_carts[session_id]
        
        order_id = save_to_db(order)
        if order_id == -1:
            fulfillment_text = "Sorry counld not place the order due to backend error."
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome your order is placed. " \
                              f"Here is your order id # {order_id}. " \
                              f"your order total amount is PKR:  {order_total}"
        del inprogress_carts[session_id]
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
            

def save_to_db(order:dict):
    next_order_id = db_helper.get_next_order_id()

    for fruit_item, quantity in order.items():
        r_code = db_helper.insert_order_item(fruit_item, quantity, next_order_id)

        if r_code == -1:
            return -1
    return next_order_id

# ****************************************************************


# Modified remove from cart function

def remove_from_cart(parameters: dict, session_id: str):
    if session_id not in inprogress_carts:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    
    fruit_items = parameters["fruit_item"]
    quantities = parameters["number"]
    current_order = inprogress_carts[session_id]

    if len(fruit_items) != len(quantities):
        return JSONResponse(content={
            "fulfillmentText": "Sorry, I don't understand. Please specify fruit item and quantity."
        })

    removed_items = []
    no_such_items = []

    for item, qty in zip(fruit_items, quantities):
        if item not in current_order:
            no_such_items.append(item)
        else:
            if current_order[item] > qty:
                current_order[item] -= qty
                removed_items.append(f"{qty} kg {item}")
            else:
                removed_items.append(f"{current_order[item]} kg {item}")
                del current_order[item]

    fulfillment_text = ""
    if len(removed_items) > 0:
        fulfillment_text += f'Removed {", ".join(removed_items)} from your order! '

    if len(no_such_items) > 0:
        fulfillment_text += f' Your current order does not have {", ".join(no_such_items)}. '

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_string_from_fruit_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}. Do you want anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

# ****************************************************************
 