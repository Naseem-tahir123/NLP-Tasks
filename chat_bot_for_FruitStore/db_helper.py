import mysql.connector

# Establish a global connection
cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="fruit_store"
)

def insert_order_item(fruit_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # calling the store procedure
        cursor.callproc("insert_fruit_item", (fruit_item,quantity,order_id))
 

        cnx.commit()

        print("Order added successfully")
        return 1
    
    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        cnx.rollback()

        cursor.close()
        cnx.close()
        return -1

    except Exception as e:
        print(f"An error occurred: {e}")

        # Rollback changes if necessary
        cnx.rollback()

        cursor.close()
        cnx.close()
        return -1


# def insert_order_tracking(order_id, status):
#     cursor = cnx.cursor()

#     # Insert into order_tracking table
#     query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
#     cursor.execute(query, (order_id, status))

#     cnx.commit()

#     cursor.close()


def get_total_order_price(order_id):
    cursor = cnx.cursor()

    # Query to get the price per unit for the fruit
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)


    result = cursor.fetchone()[0]
    cursor.close()
 
    return result


def get_next_order_id():
    cursor = cnx.cursor()

    # Query to get the next available order_id
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)

    result = cursor.fetchone()[0] 
    cursor.close()

    if result is None:
        return 1
    else:
        return result + 1
