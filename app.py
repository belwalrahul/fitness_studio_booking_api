import uuid
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# --- In-memory Data Storage for the API ---
# This data is volatile and will reset every time the Flask application restarts.
# For a production application, a persistent database (e.g., SQL, NoSQL) would be used.

# List to store all available fitness classes.
# Each dictionary represents a class with its details.


@app.route('/test/reset_data', methods=['POST'])
def reset_test_data():
    """
    POST /test/reset_data
    Resets the in-memory 'classes' and 'bookings' data to their initial state.
    This endpoint is intended for testing and development environments only
    to ensure a clean state between test runs. DO NOT use in production.
    """
    global classes, bookings # Declare global to modify the module-level lists
    
    # Re-initialize classes with fresh data
    # Ensuring datetime objects are converted to ISO format as in the initial setup
    from datetime import datetime, timedelta
    import uuid

    classes = [
        {
            "id": str(uuid.uuid4()),
            "name": "Sunrise Yoga & Meditation",
            "date_time": (datetime.now() + timedelta(days=1, hours=7, minutes=30)).isoformat(),
            "instructor": "Zen Master Yoda",
            "total_slots": 18,
            "available_slots": 18
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Power HIIT Blast",
            "date_time": (datetime.now() + timedelta(days=1, hours=17, minutes=0)).isoformat(),
            "instructor": "Captain America",
            "total_slots": 12,
            "available_slots": 12
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Groovy Zumba Fiesta",
            "date_time": (datetime.now() + timedelta(days=2, hours=18, minutes=45)).isoformat(),
            "instructor": "Beyoncé Knowles",
            "total_slots": 25,
            "available_slots": 25
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Core Strength Pilates",
            "date_time": (datetime.now() + timedelta(days=3, hours=9, minutes=0)).isoformat(),
            "instructor": "Wonder Woman",
            "total_slots": 14,
            "available_slots": 14
        }
    ]
    
    # Clear bookings
    bookings = []

    return jsonify({"message": "In-memory data reset successfully for testing."}), 200


# --- API Endpoints Implementation ---

@app.route('/classes', methods=['GET'])
def get_all_fitness_classes():
    """
    GET /classes
    Retrieves a list of all currently available fitness classes.
    Each class entry includes its unique ID, name, scheduled date/time,
    instructor, total capacity, and the current number of available slots.
    """
    # Returns the entire list of classes as a JSON array.
    return jsonify(classes), 200

@app.route('/book', methods=['POST'])
def book_a_fitness_class():
    """
    POST /book
    Handles booking requests for fitness classes.
    Requires 'class_id', 'client_name', and 'client_email' in the JSON request body.
    Validates slot availability and decrements 'available_slots' upon successful booking.
    """
    # Attempt to parse the incoming request body as JSON.
    request_data = request.get_json()

    # Validate if the request body is present and in JSON format.
    if not request_data:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # Extract required booking details from the JSON payload.
    class_id = request_data.get('class_id')
    client_name = request_data.get('client_name')
    client_email = request_data.get('client_email')

    # Ensure all mandatory fields are provided.
    if not all([class_id, client_name, client_email]):
        return jsonify({"error": "Missing required fields: 'class_id', 'client_name', 'client_email'."}), 400

    # Search for the specified class by its ID.
    target_class = None
    for cls in classes:
        if cls['id'] == class_id:
            target_class = cls
            break

    # If the class ID does not match any existing class, return a 404 Not Found.
    if not target_class:
        return jsonify({"error": f"Class with ID '{class_id}' not found."}), 404

    # Check if there are any slots left in the class.
    if target_class['available_slots'] <= 0:
        # If no slots are available, return a 409 Conflict status.
        return jsonify({"error": "This class is fully booked. No slots available."}), 409

    # If slots are available, proceed with the booking:
    # 1. Decrement the available slots for the class.
    target_class['available_slots'] -= 1

    # 2. Create a new booking record.
    new_booking_record = {
        "booking_id": str(uuid.uuid4()), # Generate a unique ID for this specific booking
        "class_id": class_id,
        "client_name": client_name,
        "client_email": client_email,
        "booking_time": datetime.now().isoformat() # Timestamp of when the booking occurred
    }
    # 3. Add the new booking record to our in-memory bookings list.
    bookings.append(new_booking_record)

    # Return a success response (201 Created) with booking details.
    return jsonify({
        "message": "Booking successfully created!",
        "booking_details": new_booking_record,
        "class_remaining_slots": target_class['available_slots']
    }), 201

@app.route('/bookings', methods=['GET'])
def get_client_bookings_by_email():
    """
    GET /bookings
    Retrieves all bookings associated with a specific client email address.
    Requires 'client_email' as a query parameter (e.g., /bookings?client_email=user@example.com).
    """
    # Get the 'client_email' from the URL query parameters.
    client_email_query = request.args.get('client_email')

    # Validate if the 'client_email' parameter was provided.
    if not client_email_query:
        return jsonify({"error": "Please provide a 'client_email' query parameter (e.g., /bookings?client_email=your.email@example.com)."}), 400

    # Filter the global bookings list to find all bookings matching the provided email.
    # The comparison is case-insensitive for email addresses.
    client_specific_bookings = [
        booking for booking in bookings
        if booking['client_email'].lower() == client_email_query.lower()
    ]

    # If no bookings are found for the email, return a message instead of an empty list.
    if not client_specific_bookings:
        return jsonify({"message": f"No bookings found for email: '{client_email_query}'."}), 200

    # Return the list of found bookings as a JSON array.
    return jsonify(client_specific_bookings), 200

# --- Application Entry Point ---
if __name__ == '__main__':
    # This block executes when the script is run directly.
    # Starts the Flask development server.
    # 'debug=True' enables automatic reloader and debugger, which is useful during development.
    # For production deployment, a robust WSGI server (like Gunicorn, uWSGI) should be used.
    app.run(debug=True, port=5000)
