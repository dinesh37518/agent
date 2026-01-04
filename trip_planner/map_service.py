class MapService:
    def __init__(self):
        # Predefined simple routes between some popular city -> hill-station pairs
        self.routes = {
            ("chennai", "ooty"): [
                "Start from Chennai.",
                "Take NH32 towards Villupuram.",
                "Continue on NH79 and then NH544 towards Coimbatore.",
                "From Coimbatore, take NH181 via Mettupalayam and Coonoor.",
                "Reach Ooty and check into your hotel.",
            ],
            ("chennai", "kodaikanal"): [
                "Start from Chennai.",
                "Take NH38 towards Trichy.",
                "Continue on NH83 towards Dindigul.",
                "From Dindigul, take the ghat road to Kodaikanal.",
                "Reach Kodaikanal and check into your hotel.",
            ],
            ("chennai", "munnar"): [
                "Start from Chennai.",
                "Take NH32 towards Villupuram.",
                "Continue via Trichy and Madurai towards Theni.",
                "From Theni, take the ghat road towards Munnar.",
                "Reach Munnar and check into your hotel.",
            ],
            ("bangalore", "ooty"): [
                "Start from Bangalore.",
                "Take NICE Road to connect to Mysore Road (NH275).",
                "Drive to Mysore and then towards Gundlupet.",
                "From Gundlupet, take the ghat road via Bandipur and Masinagudi.",
                "Reach Ooty and check into your hotel.",
            ],
            ("bangalore", "coorg"): [
                "Start from Bangalore.",
                "Take NH75 or Mysore Road towards Mandya.",
                "Continue towards Kushalnagar and then Madikeri.",
                "Reach Coorg (Madikeri) and check into your hotel.",
            ],
            ("bangalore", "kodaikanal"): [
                "Start from Bangalore.",
                "Take NH44 towards Salem.",
                "Continue towards Dindigul.",
                "From Dindigul, take the ghat road to Kodaikanal.",
                "Reach Kodaikanal and check into your hotel.",
            ],
            ("hyderabad", "ooty"): [
                "Start from Hyderabad.",
                "Take NH44 towards Kurnool and Anantapur.",
                "Continue towards Bangalore and then Mysore.",
                "From Mysore, proceed via Gundlupet and Bandipur to Ooty.",
                "Reach Ooty and check into your hotel.",
            ],
            ("hyderabad", "munnar"): [
                "Start from Hyderabad.",
                "Take NH44 towards Kurnool and Anantapur.",
                "Continue towards Bangalore and then Salem.",
                "Proceed towards Dindigul, Theni, and then up the ghat road to Munnar.",
                "Reach Munnar and check into your hotel.",
            ],
            ("mumbai", "mahabaleshwar"): [
                "Start from Mumbai.",
                "Take Mumbai–Pune Expressway to Pune.",
                "From Pune, take NH48 towards Satara.",
                "Turn towards Mahabaleshwar at Wai.",
                "Reach Mahabaleshwar and check into your hotel.",
            ],
            ("mumbai", "manali"): [
                "Start from Mumbai.",
                "Travel via Gujarat towards Delhi (NH48).",
                "From Delhi, take NH44 towards Chandigarh.",
                "Continue via Mandi and Kullu to reach Manali.",
                "Reach Manali and check into your hotel.",
            ],
            ("delhi", "manali"): [
                "Start from Delhi.",
                "Take NH44 towards Chandigarh.",
                "Continue towards Bilaspur, Mandi, and Kullu.",
                "Proceed along the Beas river valley to Manali.",
                "Reach Manali and check into your hotel.",
            ],
            ("delhi", "shimla"): [
                "Start from Delhi.",
                "Take NH44 towards Chandigarh.",
                "From Chandigarh, take NH5 via Kalka and Solan.",
                "Drive up the hills to Shimla.",
                "Reach Shimla and check into your hotel.",
            ],
        }

        # Basic information about some places
        self.places_info = {
            "chennai": {
                "name": "Chennai",
                "description": "A coastal city in Tamil Nadu known for its beaches, temples, and rich culture.",
                "highlights": [
                    "Marina Beach",
                    "Kapaleeshwarar Temple",
                    "Santhome Church",
                ],
            },
            "bangalore": {
                "name": "Bangalore",
                "description": "Capital of Karnataka, known as the Garden City and IT hub of India.",
                "highlights": [
                    "Cubbon Park",
                    "Lalbagh Botanical Garden",
                    "Vidhana Soudha",
                ],
            },
            "mumbai": {
                "name": "Mumbai",
                "description": "Financial capital of India, famous for Bollywood and the Gateway of India.",
                "highlights": [
                    "Marine Drive",
                    "Gateway of India",
                    "Elephanta Caves",
                ],
            },
            "hyderabad": {
                "name": "Hyderabad",
                "description": "Capital of Telangana, known for Charminar and Hyderabadi biryani.",
                "highlights": [
                    "Charminar",
                    "Golconda Fort",
                    "Hussain Sagar Lake",
                ],
            },
            "delhi": {
                "name": "Delhi",
                "description": "Capital city of India with a mix of historic monuments and modern life.",
                "highlights": [
                    "Red Fort",
                    "India Gate",
                    "Qutub Minar",
                ],
            },
            "ooty": {
                "name": "Ooty",
                "description": "Ooty (Udhagamandalam) is a popular hill station in Tamil Nadu known for its cool climate and tea gardens.",
                "highlights": [
                    "Ooty Lake boat ride",
                    "Doddabetta Peak",
                    "Nilgiri Mountain Railway toy train",
                ],
            },
            "kodaikanal": {
                "name": "Kodaikanal",
                "description": "Kodaikanal is a scenic hill station in Tamil Nadu, often called the 'Princess of Hill Stations'.",
                "highlights": [
                    "Kodaikanal Lake",
                    "Coaker's Walk",
                    "Pine forests",
                ],
            },
            "munnar": {
                "name": "Munnar",
                "description": "Munnar is a hill station in Kerala known for tea plantations, valleys, and cool weather.",
                "highlights": [
                    "Tea gardens",
                    "Eravikulam National Park",
                    "Mattupetty Dam",
                ],
            },
            "coorg": {
                "name": "Coorg",
                "description": "Coorg (Kodagu) is a hill station in Karnataka known for coffee estates and misty hills.",
                "highlights": [
                    "Coffee plantations",
                    "Abbey Falls",
                    "Raja's Seat viewpoint",
                ],
            },
            "manali": {
                "name": "Manali",
                "description": "Manali is a famous hill station in Himachal Pradesh, popular for snow and adventure sports.",
                "highlights": [
                    "Solang Valley",
                    "Rohtang Pass (seasonal)",
                    "Hadimba Temple",
                ],
            },
            "shimla": {
                "name": "Shimla",
                "description": "Shimla is the capital of Himachal Pradesh, once the summer capital of British India.",
                "highlights": [
                    "The Ridge",
                    "Mall Road",
                    "Jakhoo Temple",
                ],
            },
            "mahabaleshwar": {
                "name": "Mahabaleshwar",
                "description": "Mahabaleshwar is a hill station in Maharashtra known for viewpoints and strawberries.",
                "highlights": [
                    "Arthur's Seat",
                    "Venna Lake",
                    "Strawberry farms (seasonal)",
                ],
            },
        }

    def get_route(self, origin, destination):
        origin_key = origin.strip().lower()
        dest_key = destination.strip().lower()
        key = (origin_key, dest_key)
        if key in self.routes:
            return self.routes[key]

        # Generic fallback route description
        steps = [
            f"Start from {origin}.",
            f"Head towards {destination} following the main highway.",
            "Follow road signs and navigation instructions on your preferred map app.",
            f"Arrive at {destination}.",
        ]
        return steps

    def describe_place(self, place_name):
        key = place_name.strip().lower()
        info = self.places_info.get(key)
        if not info:
            return {
                "name": place_name,
                "description": f"{place_name} is a nice place to visit. You can explore local attractions, food, and culture.",
                "highlights": [],
            }
        return info

