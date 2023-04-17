# Web Server for Data Analysis with Django REST Framework

This web server is built using Python with Django REST Framework. It allows users to upload CSV data containing review time, merge time, team information, and date of recording. The server provides APIs for calculating statistics such as mean, median, and mode per team from the uploaded data. Users can also create visualizations of the data using line, bar, or scatter charts and share them with other users.

## Features
* User registration and login with token-based authentication using knox
* Store CSV data in PostgreSQL database
* Calculate statistics for the stored data using numpy and pandas
* Create charts for the stored data and store them on the server: line charts, bar charts and scatter plots.
* Share charts between users
* The server is made asynchronous using asyncio

## How to Build and Run
* Clone the repository and navigate to the app directory
* Run `docker-compose build`
* Run `docker compose up`

The server should start and listen for requests at `localhost:8000`.

## Usage
To test the application using Postman, follow these steps:
1. Register a user using the `/api/v1/register/` endpoint by providing a JSON with the username and password.
2. Login the registered user using the `/api/v1/login/` endpoint by providing a JSON with the username and password.
3. After logging in, a token is provided. Copy it because it will be used to authenticate access to the rest of the endpoints.
4. Upload CSV data via the `/api/v1/csvdata/` endpoint by providing the CSV text inside the body as raw text. Add a header in the "Headers" tab with the key "Authorization" and the value "Token <the token copied in step 3>" (note the space between "Token" and the token hash).
5. Retrieve statistics for the uploaded data using the `/api/v1/csvdata/statistics/` endpoint. Note that you can also add a team query parameter to just retrieve the statistics for one team: `/api/v1/csvdata/statistics/?team=Team+A`
6. Create visualizations for the uploaded data by posting to the `/api/v1/visualizations/` endpoint. This will return the URLs to the created charts, which can be accessed via the browser. The charts will also be stored on the server in the /visualizations folder. If you want to check the charts png file on the server, run `docker-compose exec app sh` to connect to the docker container, and navingate to /visualizations folder. Each user will have a folder with the user id as the name of the folder.
7. Share visualizations with another user using the `/api/v1/visualizations/share/?username=username` endpoint. Note that you will have to register another user.

## Database design
* csvdata_csvdata table contains the csv data row by row, and it is associated to the user which uploaded it
* visualizations_visualization table contains the charts which have been created by the user. Only the path to the png file on the server is stored in the database.

## To do:
* Improve tests. Currently there are not much tests written.
* Save the plots all at once, not one at a time
* Improve the async code. Need to figure out how Django works with aync in more depth.

## Technologies Used:
* Python
* Django REST Framework
* PostgreSQL
* pandas
* numpy
* Docker
* OpenAPI

## Code info:
The Django application is structured into 3 apps, as they are called in the Django terminology. These apps can be found in the apps folder:
* users - this contains all the code for the user registration and login
* csvdata - this contains all the code for uploading csv data, and for generating statistics for the data (it has the models and the views). It's basically the implementation for /csvdata and /csvdata/statistics endpoints
* visualizations - this contains the code for creating and sharing charts for the data
The analytics_backend folder is the main django application which contains the app settings and urls.
