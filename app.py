import requests
from datetime import datetime
import sys


# Prompt user for API key
def asking_user_key():
    your_api_key = ''
    while your_api_key == '':
        your_api_key = input('Enter your API key: ')
    return your_api_key


# Prompt user for trip destination
def asking_destination():
    destination = ''
    while destination == '':
        destination = input('Enter your destination: ')
    return destination


# Prompt user for date
def asking_date(input_date_type):
    input_date = ''
    while input_date == '':
        input_date = input(f'Enter the {input_date_type} date (dd/mm/yyyy): ')

    date_obj = validate_date_input(input_date, input_date_type)
    return date_obj


# Validate the format of the input date
def validate_date_input(input_date, input_date_type):
    # expected date format
    date_format = '%d/%m/%Y'

    # create date object with the date string
    try:
        date_obj = datetime.strptime(input_date, date_format)
    except:
        print("Date format not recognised")
        return asking_date(input_date_type)
    else:
        # convert date string to correct format
        return date_obj


# Turn date object into string format for API request
def date_tostring(date_obj, format_desired):
    return date_obj.strftime(format_desired)


# Call the function to input dates and check return date is after departing date
def asking_valid_dates():
    departing_date_obj = asking_date('departing')
    returning_date_obj = asking_date('returning')
    if departing_date_obj > returning_date_obj:
        print('Returning date is not after departing date.')
        asking_valid_dates()
    dates = {'departing': departing_date_obj.date(), 'returning': returning_date_obj.date()}
    return dates


# Request forecast to weather API
def make_request():
    # endpoint for the API request
    endpoint = ('https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/' +
                f'timeline/{DESTINATION}/{DEPARTING_DATE}/{RETURNING_DATE}?key={YOUR_API_KEY}&unitGroup=metric')

    return requests.get(endpoint)


# validate API response before converting data
def get_valid_data(forecast_request):
    # If the request has a 200 status code, the data is formatted
    if forecast_request.ok:
        print("Request successful")
        return forecast_request.json()
    # For any other response status, the program will exit with a message
    elif forecast_request.status_code == 400:
        message = "Bad request. Check your destination and date inputs."
    elif forecast_request.status_code == 401:
        message = "Your API key invalid."
    else:
        message = "An unexpected error occurred during your request."
    sys.exit(message)


# Calculate duration of trip
def calculate_duration():
    duration = trip_dates['returning'] - trip_dates['departing']
    return duration.days + 1


# Create a summary of the trip forecast
def create_summary():
    # Confirm destination and dates of the trip
    destination = forecast_data['resolvedAddress']
    # Format dates in long month version
    departing = date_tostring(trip_dates['departing'], '%d %B %Y')
    returning = date_tostring(trip_dates['returning'], '%d %B %Y')

    details = f'You are travelling to {destination} from {departing} to {returning}.\n'

    # Calculate trip duration
    total_days = calculate_duration()
    duration = f'Your trip will last {total_days} days.'
    # Use slicing for single day trip
    if total_days == 1:
        duration = duration[0:-2] + '.'

    trip_summary = '\n' + details + duration + '\n'
    return trip_summary


# Confirm the details before proceeding with program
def confirm_details(trip_summary):
    print('These are your trip details: \n' + trip_summary)
    confirmation = input('Are all details above correct? (y/n) ')
    if confirmation.lower() == 'y' or confirmation.lower() == 'yes':
        print('You confirmed the details of your trip.')
        return True
    else:
        sys.exit('You have not confirmed the details of your trip.')


# Create object with forecast data organised
def organise_forecast_data():
    max_temp = []
    min_temp = []
    precipitation = []
    cloud_cover = []

    # Collect data from each day in the forecast request
    for day in forecast_data['days']:
        max_temp.append(day['tempmax'])  # The max expected temperature for that day in Celsius
        min_temp.append(day['tempmin'])  # The min expected temperature for that day in Celsius
        precipitation.append(day['precip'])  # The mm of precipitation expected
        cloud_cover.append(day['cloudcover'])   # The % of sky covered by clouds that day

    selected_data = {
        'highest_temp': max(max_temp),
        'lowest_temp': min(min_temp),
        'precipitation': precipitation,
        'cloud_cover': cloud_cover
    }

    return selected_data


# Prepare temperature report
def report_temperature(data):
    temperature_report = ('\nTEMPERATURE \n' +
                          'During your trip, the temperature is expected to reach ' +
                          f'a maximum of {data['highest_temp']} degrees Celsius ' +
                          f'and a minimum of {data['lowest_temp']} degrees Celsius.\n')

    return temperature_report


# Analyse the weather data
def analyse_weather(data):
    # Count days with expected precipitation
    wet_days = 0
    for quantity in data['precipitation']:
        if (not quantity == None) and quantity > 0:
            wet_days += 1

    # Percentage of days during the trip which are expected to have some precipitation
    wet_percent = wet_days / len(data['precipitation']) * 100

    # Cloudy, partially cloudy and sunny days
    cloudy = 0
    part_cloudy = 0
    sunny = 0
    for record in data['cloud_cover']:
        if record > 50:
            cloudy += 1
        elif record < 10:
            sunny += 1
        else:
            part_cloudy += 1

    # Percentage of cloudy, partially cloudy and sunny days in the period observed
    cloudy_percent = cloudy / len(data['cloud_cover']) * 100
    part_cloudy_percent = part_cloudy / len(data['cloud_cover']) * 100
    sunny_percent = sunny / len(data['cloud_cover']) * 100

    # Create weather object
    weather_analysis = {
        'rain': round(wet_percent),
        'cloudy': round(cloudy_percent),
        'variable': round(part_cloudy_percent),
        'sunny': round(sunny_percent)
    }

    return weather_analysis


# Create report for the weather
def report_weather(analysis):
    # Identify trends (Weather elements that are expected more than 50% of the time)
    trends = {}
    for element in analysis:
        if analysis[element] > 99:
            trends[element] = 'all'
        elif analysis[element] > 50:
            trends[element] = 'most'
        elif analysis[element] == 0:
            trends[element] = 'none'
        else:
            trends[element] = 'some'

    rain_report = f'Rain is to be expected for {trends['rain']} of your trip.'

    cloud_report = (f'{trends['cloudy'].title()} of the time the sky is going to be largely covered in clouds. '
                    f'You can expect sunny days {trends['sunny']} of the time and '
                    f'partially clouded sky should happen for {trends['variable']} of your journey.')

    return '\nWEATHER REPORT\n' + rain_report + '\n' + cloud_report + '\n'


# Using forecast define clothing tips (appropriate for the weather expected)
def get_clothes_tips(weather, temperature):
    clothes_tips = {
        'rain': False,
        'sunny': False,
        'cold': False,
        'hot': False,
        'mild': False
    }
    if weather['rain'] > 0:
        clothes_tips['rain'] = True

    if weather['sunny'] > 0:
        clothes_tips['sunny'] = True

    if temperature['lowest_temp'] < 10 or temperature['highest_temp'] < 10:
        clothes_tips['cold'] = True

    if temperature['lowest_temp'] > 25 or temperature['highest_temp'] > 25:
        clothes_tips['hot'] = True
    else:
        clothes_tips['mild'] = True

    return clothes_tips


# Prepare a packing list for the trip
def make_packing_list():
    # Generic list of clothing items
    wardrobe = {
        'underwear': {'all': ['panties and bra / boxers / briefs', 'socks']},
        'tops': {'cold': ['long sleeves tops', 'long dresses'],
                 'mild': ['t-shirts', 'short sleeves dresses'],
                 'hot': ['sleeveless tops', 'summer dresses']},
        'layering tops': {'mild': ['shirts', 'hoodies'],
                          'cold': ['sweaters', 'cardigans']},
        'bottoms': {'all': ['jeans', 'trousers', 'leggings', 'skirts']},
        'outerwear': {'mild': ['jacket'],
                      'cold': ['coat / parka'],
                      'rain': ['waterproof jacket / coat']},
        'shoes': {'hot': ['sandals / flip-flops'],
                  'mild': ['sneakers / closed shoes'],
                  'cold': ['boots']},
        'accessories': {'cold': ['scarf', 'gloves', 'beanie'],
                        'sunny': ['sunhat, sunglasses']}
    }

    # Get appropriate tips for clothing
    clothes_tips = get_clothes_tips(weather_data, organised_data)

    # Empty packing list to populate
    packing_list = {
        'underwear': [],
        'tops': [],
        'layering tops': [],
        'bottoms': [],
        'outerwear': [],
        'shoes': [],
        'accessories': []
    }

    # Pass the relevant clothing items from the wardrobe to the packing list
    for category in wardrobe:
        for label in wardrobe[category]:
            if label == 'all' or clothes_tips[label]:
                for item in wardrobe[category][label]:
                    try:
                        packing_list[category].append(item)
                    except:
                        packing_list[category] = item

    return packing_list


# Write the weather report and packing list on txt file
def write_report_packing():
    with open('Packing_Forecast.txt', 'a') as text_file:
        text_file.write('DETAILS\n' + summary)
        text_file.write(report_temperature(organised_data))
        text_file.write(report_weather(weather_data))

        # Generate the packing list
        packing_list = make_packing_list()

        # Loop through the packing list to write on file each category
        for category in packing_list:
            category_title = '\n' + category.upper() + '\n'
            text_file.write(category_title)
            # Write each item in the category to a new line
            for item in packing_list[category]:
                list_item = ' - ' + item + '\n'
                text_file.write(list_item)

    return 'Your trip report with packing list is ready in the text file'


# Get all needed information from user
YOUR_API_KEY = asking_user_key()
DESTINATION = asking_destination()

trip_dates = asking_valid_dates()

DEPARTING_DATE = date_tostring(trip_dates['departing'], '%Y-%m-%d')
RETURNING_DATE = date_tostring(trip_dates['returning'], '%Y-%m-%d')

# Request forecast and validate the success of the request
forecast_data = get_valid_data(make_request())

# Call the function to confirm user input
summary = create_summary()

# Only continue if details are correct
if confirm_details(summary):
    organised_data = organise_forecast_data()
    weather_data = analyse_weather(organised_data)

    print(write_report_packing())
