import googlemaps

# Google Maps API key
API_KEY = '<ENTER YOUR GMAPS API KEY>'

# Address to search near
LAT_LONG = '<ENTER LAT/LONG>'  # e.g. '35.997723, -86.796276'  # Brentwood
SEARCH_RADIUS = 1 * 1000  # meters

# Constants
PRICE_PER_MILE = 0.5  # Cost per mile (e.g. 0.50)
TIME_VALUE = 30.0  # Value of time per hour (e.g. 10.0)

# Bayesian constants
useFixedPrior = True
fixedPriorRating = 4.2
fixedPriorNumRatings = 25


class Business:
    def __init__(self, name, address, rating, num_ratings, bayesian_average, distance, travel_time, place_id):
        self.name = name
        self.address = address
        self.rating = rating
        self.num_ratings = num_ratings
        self.bayesian_average = bayesian_average
        self.distance = distance
        self.travel_time = travel_time
        self.place_id = place_id


class BusinessSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.businesses = []
        self.prior_rating = 0
        self.prior_num_ratings = 0

    def download_businesses(self, search_string):
        # Perform the search
        results = self.gmaps.places(query=search_string, location=LAT_LONG, radius=SEARCH_RADIUS)

        # Extract the relevant information from the results
        for result in results['results']:
            name = result['name']
            address = result.get('formatted_address', 'N/A')
            rating = result.get('rating', 'N/A')
            num_ratings = result.get('user_ratings_total', 'N/A')
            place_id = result.get('place_id', 'N/A')  # Get place_id
            bayesian_average = None  # Placeholder for now
            distance = None  # Placeholder for now
            travel_time = None  # Placeholder for now
            business = Business(name, address, rating, num_ratings, bayesian_average, distance, travel_time, place_id)
            self.businesses.append(business)

    def calculate_bayesian_averages(self):
        for business in self.businesses:
            business.bayesian_average = self.calculate_bayesian_average(
                business.rating, business.num_ratings, self.prior_rating, self.prior_num_ratings
            )

    @staticmethod
    def calculate_bayesian_average(rating, num_ratings, prior_rating, prior_num_ratings):
        bayesian_average = ((prior_rating * prior_num_ratings) + (rating * num_ratings)) / (prior_num_ratings + num_ratings)
        return bayesian_average

    @staticmethod
    def calculate_prior_rating_and_num_ratings(businesses):
        total_rating = sum(business.rating * business.num_ratings for business in businesses)
        total_num_ratings = sum(business.num_ratings for business in businesses)

        prior_rating = total_rating / total_num_ratings if total_num_ratings > 0 else 0
        prior_num_ratings = total_num_ratings

        return prior_rating, prior_num_ratings

    def calculate_distances_and_travel_times(self):
        origins = [LAT_LONG]
        destinations = [business.address for business in self.businesses]

        # Call the Google Maps Distance Matrix API
        response = self.gmaps.distance_matrix(origins, destinations, units="imperial")

        # Extract and update the distances and travel times in the businesses
        for i, element in enumerate(response['rows'][0]['elements']):
            if element['status'] == 'OK':
                distance = element['distance']['text']
                travel_time = element['duration']['text']
                self.businesses[i].distance = distance
                self.businesses[i].travel_time = travel_time


    def convert_travel_time_to_float(self, travel_time):
        parts = travel_time.split()
        total_hours = 0.0

        for i in range(0, len(parts), 2):  # Process in pairs (value, unit)
            value = float(parts[i])
            unit = parts[i + 1]

            if unit in ['hour', 'hours']:
                total_hours += value
            elif unit in ['min', 'mins']:
                total_hours += value / 60  # Convert minutes to hours

        return total_hours


    def calculate_travel_cost(self, business):
        distance = float(business.distance.split()[0])  # Extract the numeric value from the distance string
        travel_time = self.convert_travel_time_to_float(business.travel_time)
        cost = distance * PRICE_PER_MILE + travel_time * TIME_VALUE * 2
        return cost

    def print_businesses(self):
        print("Prior Rating: {:.2f}".format(self.prior_rating))
        print("Prior Number of Ratings:", self.prior_num_ratings)
        print("\n{:<28} {:<40} {:<10} {:<10} {:<10} {:<10} {:<15} {:<15}".format("Place ID", "Name", "Bayes", "Rating", "Reviews", "Distance", "Travel Time", "Travel Cost"))
        print("-" * 141)
        for business in self.businesses:
            bayesian_avg = round(business.bayesian_average, 2)
            distance = business.distance
            reviews = business.num_ratings
            travel_time = business.travel_time
            travel_cost = self.calculate_travel_cost(business)

            # Truncate business name to 30 characters if it's longer
            business_name = business.name[:40] if len(business.name) > 40 else business.name

            print("{:<28} {:<40} {:<10} {:<10} {:<10} {:<15} {:<15}".format(
                business.place_id, business_name, bayesian_avg, business.rating, reviews, distance, travel_time,
                travel_cost
            ))

def main():
    # Create BusinessSearch object with API key
    business_search = BusinessSearch(API_KEY)

    # User input for the search string
    search_string = input("Enter the search string: ")

    # Download businesses
    business_search.download_businesses(search_string)

    # Calculate prior rating and prior number of ratings
    if useFixedPrior:
        business_search.prior_rating = fixedPriorRating
        business_search.prior_num_ratings = fixedPriorNumRatings
    else:
        business_search.prior_rating, business_search.prior_num_ratings = BusinessSearch.calculate_prior_rating_and_num_ratings(business_search.businesses)

    # Calculate Bayesian averages
    business_search.calculate_bayesian_averages()

    # Calculate distances and travel times
    business_search.calculate_distances_and_travel_times()

    # Sort businesses based on Bayesian Average
    business_search.businesses.sort(key=lambda x: x.bayesian_average, reverse=True)

    # Print the list of businesses
    business_search.print_businesses()


if __name__ == "__main__":
    main()
