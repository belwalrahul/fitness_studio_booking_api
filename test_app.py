# test_app.py
import pytest
import requests
import json
from app import app 

# Base URL for the Flask application
BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture(autouse=True)
def reset_data_before_each_test():
    """
    Fixture to reset the in-memory data in the Flask application
    before each test by calling a dedicated test endpoint.
    This ensures tests are independent and reproducible.
    """
    response = requests.post(f"{BASE_URL}/test/reset_data")
    assert response.status_code == 200, f"Failed to reset data: {response.json()}"
    # Small delay to ensure server processes the reset, if necessary (usually not for local)
    # import time
    # time.sleep(0.05)


def test_get_all_fitness_classes():
    """
    Test case for GET /classes endpoint.
    Verifies that all initially loaded classes are returned by the running app.
    """
    response = requests.get(f"{BASE_URL}/classes")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # We can't assert len(data) == len(app.classes) directly,
    # because app.classes is in a different process.
    # Instead, we just check if it returns a list of classes.

    assert len(data) > 0 # Assumes there's at least one class initialized in app.py

def test_book_a_fitness_class_success():
    """
    Test case for POST /book endpoint - successful booking.
    Verifies that a booking can be made and available slots decrease.
    """
    response_classes = requests.get(f"{BASE_URL}/classes")
    assert response_classes.status_code == 200
    current_classes = response_classes.json()

    if not current_classes:
        pytest.fail("No classes found in the running Flask app to book.")

    class_to_book = current_classes[0] # Take the first available class
    initial_available_slots = class_to_book['available_slots']
    class_id = class_to_book['id']

    booking_payload = {
        "class_id": class_id,
        "client_name": "Test Client",
        "client_email": "test@example.com"
    }

    response = requests.post(f"{BASE_URL}/book", json=booking_payload)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "booking_details" in data
    assert data["booking_details"]["class_id"] == class_id
    assert data["booking_details"]["client_name"] == "Test Client"
    assert data["class_remaining_slots"] == initial_available_slots - 1

    # Verify state change on the server by fetching classes again
    response_classes_after_booking = requests.get(f"{BASE_URL}/classes")
    updated_class_on_server = next(cls for cls in response_classes_after_booking.json() if cls['id'] == class_id)
    assert updated_class_on_server['available_slots'] == initial_available_slots - 1

    # Verify a booking record was created (by checking bookings endpoint for this email)
    bookings_response = requests.get(f"{BASE_URL}/bookings?client_email={booking_payload['client_email']}")
    assert bookings_response.status_code == 200
    assert len(bookings_response.json()) > 0
    assert bookings_response.json()[0]['class_id'] == class_id


def test_book_a_fitness_class_missing_fields():
    """
    Test case for POST /book endpoint - missing required fields.
    """
    # This test doesn't strictly need a valid class_id as it fails early.
    booking_payload = {
        "class_id": "any-id", # ID doesn't matter for this specific error case
        "client_name": "Test Client"
        # Missing client_email
    }
    response = requests.post(f"{BASE_URL}/book", json=booking_payload)
    assert response.status_code == 400
    assert "Missing required fields" in response.json().get("error")

def test_book_a_fitness_class_not_found():
    """
    Test case for POST /book endpoint - class not found.
    """
    booking_payload = {
        "class_id": "non-existent-id", # This is explicitly meant to not be found
        "client_name": "Test Client",
        "client_email": "test@example.com"
    }
    response = requests.post(f"{BASE_URL}/book", json=booking_payload)
    assert response.status_code == 404
    assert "not found" in response.json().get("error")

def test_book_a_fitness_class_fully_booked():
    """
    Test case for POST /book endpoint - class fully booked.
    """
    # 1. Get current classes from the running Flask app
    response_classes = requests.get(f"{BASE_URL}/classes")
    assert response_classes.status_code == 200
    current_classes = response_classes.json()

    if not current_classes:
        pytest.fail("No classes found in the running Flask app to test full booking.")

    class_to_book = current_classes[0] # Take the first class
    class_id = class_to_book['id']

    # 2. Book all available slots for this class to make it fully booked
    initial_slots = class_to_book['available_slots']
    for i in range(initial_slots):
        book_payload = {
            "class_id": class_id,
            "client_name": f"Client {i}",
            "client_email": f"client{i}@example.com"
        }
        book_res = requests.post(f"{BASE_URL}/book", json=book_payload)
        assert book_res.status_code == 201 # Ensure each booking succeeds

    # 3. Try to book one more time (which should now fail)
    booking_payload_fail = {
        "class_id": class_id,
        "client_name": "Overbooked Client",
        "client_email": "overbooked@example.com"
    }
    response_fail = requests.post(f"{BASE_URL}/book", json=booking_payload_fail)
    assert response_fail.status_code == 409 # Expecting 409 Conflict
    assert "fully booked" in response_fail.json().get("error")

    # Optional: Verify slots are still 0 on server
    response_classes_after_full = requests.get(f"{BASE_URL}/classes")
    fully_booked_class_on_server = next(cls for cls in response_classes_after_full.json() if cls['id'] == class_id)
    assert fully_booked_class_on_server['available_slots'] == 0


def test_get_client_bookings_by_email_success():
    """
    Test case for GET /bookings endpoint - successful retrieval.
    """
    # 1. Get current classes from the running Flask app
    response_classes = requests.get(f"{BASE_URL}/classes")
    assert response_classes.status_code == 200
    current_classes = response_classes.json()

    if not current_classes:
        pytest.fail("No classes found in the running Flask app to create bookings for.")

    class_id = current_classes[0]['id']
    client_email_for_test = "test@example.com"

    # 2. Book a class first to have some data associated with this email
    booking_payload = {
        "class_id": class_id,
        "client_name": "Test Client For Email Search",
        "client_email": client_email_for_test
    }
    book_response = requests.post(f"{BASE_URL}/book", json=booking_payload)
    assert book_response.status_code == 201 # Ensure booking was successful

    # 3. Now query for bookings for that email
    response = requests.get(f"{BASE_URL}/bookings?client_email={client_email_for_test}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Should have at least one booking now
    assert data[0]["client_email"].lower() == client_email_for_test.lower()
    assert data[0]["class_id"] == class_id


def test_get_client_bookings_by_email_no_bookings():
    """
    Test case for GET /bookings endpoint - no bookings for email.
    """
    response = requests.get(f"{BASE_URL}/bookings?client_email=nonexistent@example.com")
    assert response.status_code == 200
    assert "No bookings found" in response.json().get("message")

def test_get_client_bookings_by_email_missing_param():
    """
    Test case for GET /bookings endpoint - missing client_email parameter.
    """
    response = requests.get(f"{BASE_URL}/bookings") # No client_email param
    assert response.status_code == 400
    assert "Please provide a 'client_email'" in response.json().get("error")