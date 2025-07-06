# fitness_studio_booking_api
This is an evaluation submission for Fitness Studio booking API calls


# How to run
## Windows
 - I would recommend to use a python virtual environment, to do that create a project directory and in console type "python -m venv venv".
 - Start the virtual environment ".\venv\Scripts\activate",  this should run your virtual environment you just created.
 - Install Flask "pip install Flask".
 - Clone the directory and run the app.py using "python app.py",  this should start the server on 127.0.0.1:5000
 - To test wether the APIs are working or not, I have provided test_app.py, which should run on a different console window using "pytest"

 - There are other ways to test using Postman (read postman documentations)
 - I'll provide some URLs to help you test using curl and the same can be used to test in Postman as well
   - curl http://127.0.0.1:5000/classes
   - curl -X POST -H "Content-Type: application/json" -d "{ \"class_id\": \"<class_id>\", \"client_name\": \"John Doe\", \"client_email\": \"john.doe@example.com\" }" http://127.0.0.1:5000/book        // Replace <class_id> with the class id we got from above command
   - curl "http://127.0.0.1:5000/bookings?client_email=john.doe@example.com"
