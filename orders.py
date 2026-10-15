
"""Order processing logic."""
import database
import auth

TAX = 0.15
SEPARATOR = "=============================="

COUPONS = {
    "WELCOME10": 0.9,
    "BLACKFRIDAY": 0.5,
    "STAFF": 0.7,
}

SHIPPING_COSTS = {
    "express": 10,
    "standard": 3,
}


def process_order(token, items, coupon=None, shipping="standard", log=None):
    if log is None:
        log = []

    username = auth.sessions.get(token)

    if username is None:
        print("Invalid session")
        return None

    if not items:
        print("Empty order")
        return None

    total = 0

    for item in items:
        book = database.get_book(item["book_id"])

        if not book:
            print("Book not found")
            continue

        quantity = item["qty"]

        if quantity <= 0:
            print("Invalid quantity")
            continue

        if book[3] < quantity:
            if book[3] > 0:
                print(
                    f"Only {book[3]} units available for {book[1]}"
                )
            else:
                print(f"Book out of stock: {book[1]}")
            continue

        total += book[2] * quantity
        database.update_stock(book[0], book[3] - quantity)

    if coupon in COUPONS:
        total *= COUPONS[coupon]

    total += SHIPPING_COSTS.get(shipping, 0)
    total += total * TAX

    order_id = len(log) + 1
    database.save_order(order_id, username, total, "PENDING")
    log.append(order_id)

    return round(total, 2)

def _calculate_and_print_totals(items):
    """Helper to calculate and print totals, avoiding duplication."""
    subtotal = 0
    for item in items:
        book = database.get_book(item["book_id"])
        line_total = book[2] * item["qty"]
        subtotal += line_total
        print(
            book[1] + " x" + str(item["qty"])
            + " = " + str(line_total)
        )
    
    tax = subtotal * TAX
    print("Subtotal: " + str(round(subtotal, 2)))
    print("Tax: " + str(round(tax, 2)))
    print("Total: " + str(round(subtotal + tax, 2)))

def print_invoice(username, items):
    print(SEPARATOR)
    print("BOOKSTORE INVOICE")
    print("Customer: " + username)
    print(SEPARATOR)
    
    _calculate_and_print_totals(items)  # Call the shared function
    
    print(SEPARATOR)

def print_quote(username, items):
    print(SEPARATOR)
    print("BOOKSTORE QUOTE")
    print("Customer: " + username)
    print(SEPARATOR)
    
    _calculate_and_print_totals(items)  # Call the shared function
    
    print("This quote is valid for 7 days.")
    print(SEPARATOR)
def cancel_order(order_id):
    conn = database.get_connection()

    try:
        conn.execute(
            "UPDATE orders SET status = 'CANCELLED' WHERE id = ?",
            (order_id,),
        )
        conn.commit()
    finally:
        conn.close()
