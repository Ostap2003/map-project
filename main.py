import math
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderServiceError


def read_file(usr_year: str) -> dict:
    """
    Reads file and writes film's name, year and location to a dict:
    key is a location, value is a list of tuples in which are present the year and the name of the film.
    """
    film_info = set()
    film_info_dict = {}
    data = open('locations_short.list', 'r', encoding='utf-8', errors='ignore')
    lines = data.readlines()[14:-1]

    for line in lines:
        line = line.split('\t')

        line = list(filter(lambda x: len(x) > 0, line))
        line = line[:2]

        start_id = line[0].find('(') + 1
        year = line[0][start_id:start_id + 4]

        if year == usr_year:
            film = line[0][0:start_id - 2]
            location = line[-1]

            if '\n' in location:
                location = line[-1][:-1]
            
            if (film, location) not in film_info:
                if location not in film_info_dict:
                    film_info_dict[location] = [(year, film)]
                else:
                    film_info_dict[location].append((year, film))
            else:
                pass

    data.close()
    return film_info_dict


def add_distance(curr_location: tuple, film_info: dict) -> dict:
    """
    Finds coordinates of each film_info key and the
    distance from curr_location to found coordinates.
    """
    film_location = {}
    cursor = 0
    for key in film_info:
        geolocator = Nominatim(user_agent="app")
        try:
            location = geolocator.geocode(key)

            if location == None:
                for i in range(1, len(key[-1].split(','))):
                    place = key[-1].split(',')
                    place = ','.join(place[i:])
                    # print('location was None, trying to find... ', place)
                    location = geolocator.geocode(place)
                    if location != None:
                        break

            coordinates = (location.latitude, location.longitude)
            dist = calculate_distance(coordinates, curr_location)
            # set coordinates and dist as a key
            film_location[(dist, coordinates)] = film_info[key]
            cursor += 1
            # print(dist, '  ', cursor)

        except (GeocoderUnavailable, GeocoderServiceError, AttributeError):
            pass

    return dict(sorted(film_location.items(), key=lambda x: x[0]))


def calculate_distance(search_point, curr_location):
    """
    Calculates the distance.
    """
    lat_origin, lon_origin = curr_location
    lat_dest, lon_dest = search_point
    radius = 6371  # km

    dif_lat = math.radians(lat_dest - lat_origin)
    dif_lon = math.radians(lon_dest - lon_origin)
    part = ((math.sin(dif_lat/2)) ** 2) + math.cos(math.radians(lat_origin)) \
        * math.cos(math.radians(lat_dest)) * ((math.sin(dif_lon/2)) ** 2)
    
    dist = 2 * radius * math.asin(math.sqrt(part))
    return dist


def unpack_info(film_info: dict) -> list:
    """
    Unpacks first 10 closest locations.
    """
    closest = []
    for key in film_info:
        for film in film_info[key]:
            if len(closest) != 10:
                closest.append((key[1], film_info[key]))
            else:
                break
    
    return closest


def main(year: str, curr_location: tuple):
    """
    Main function of the module. Generates map based on year and usr current location.
    """
    film_info_dict = read_file(year)
    film_info_dict = add_distance(curr_location, film_info_dict)
    closest = unpack_info(film_info_dict)

    # generate the map
    film_map = folium.Map(location=list(curr_location), zoom_start=10)
    fg = MarkerCluster(name='The closest films')
    lines = folium.FeatureGroup(name='Connections')
    
    # add home point
    fg.add_child(folium.Marker(location=list(curr_location), 
                               icon=folium.Icon(icon='glyphicon glyphicon-home', color='blue')))

    for film in closest:
        location = list(film[0])

        html = f'''
                   <div style='font-family: Arial;'>
                   <b>year:</b> {film[1][0][0]}
                   <br>
                   <b>Film:</b> {film[1][0][1]}
                   </div>
                '''
        iframe = folium.IFrame(html,
                            width=200,
                            height=100)

        popup = folium.Popup(iframe, max_width=250)
        fg.add_child(folium.Marker(location=location,
                                   popup=popup,
                                   icon=folium.Icon(icon='glyphicon glyphicon-map-marker', color='red')))
        lines.add_child(folium.PolyLine(locations=[list(curr_location), location], line_opacity=0.1, color='#e88000'))

    film_map.add_child(fg)
    film_map.add_child(lines)

    folium.TileLayer('cartodbdark_matter').add_to(film_map)
    folium.LayerControl().add_to(film_map)

    film_map.save(f'{year}_movies_map.html')
    return f'{year}_movies_map.html'
    

def start():
    """
    Start function of the module. Takes user's input.
    """ 
    year = input('Please enter a year you would like to have a map for: ')
    curr_location = tuple(map(lambda x: float(x), tuple(input('Please enter your location (format: lat, long): ').strip().split(','))))
    
    print('Map is generating...')
    print('Please wait...')
    film_map = main(year, curr_location)
    return f'Finished. Please have look at the map {film_map}'



if __name__ == "__main__":
    print(start())