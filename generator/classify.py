"""Category, cuisine and area for a place, from the sources only. Nothing here is a guess the page then states as fact:
an unknown cuisine renders as 'not listed yet', not as a made-up one. A health-department establishment whose name
carries no food signal is NOT listed (it goes to data/work/unsorted.json for a person to look at)."""
import re

CATEGORIES = {
    "restaurant": "Restaurants", "bar": "Bars & pubs", "cafe": "Coffee, tea & bakeries", "brewery": "Breweries & taprooms",
    "winery": "Wineries", "fast_food": "Fast food & counter service", "dessert": "Dessert & ice cream",
    "deli": "Delis & markets", "hotel_bar": "Hotel bars & dining", "entertainment": "Games, lanes & screens",
    "lounge": "Lounges", "other": "Other food service",
}
CATEGORY_ORDER = ["restaurant", "bar", "cafe", "fast_food", "dessert", "brewery", "winery", "deli", "entertainment",
                  "lounge", "hotel_bar", "other"]

CUISINE_LABEL = {
    "mexican": "Mexican", "tex-mex": "Tex-Mex", "american": "American", "pizza": "Pizza", "burger": "Burgers",
    "chinese": "Chinese", "japanese": "Japanese", "sushi": "Sushi", "thai": "Thai", "indian": "Indian",
    "italian": "Italian", "vietnamese": "Vietnamese", "mediterranean": "Mediterranean", "greek": "Greek",
    "barbecue": "Barbecue", "bbq": "Barbecue", "seafood": "Seafood", "steak_house": "Steakhouse", "steak": "Steakhouse",
    "sandwich": "Sandwiches", "coffee_shop": "Coffee", "chicken": "Chicken", "asian": "Asian", "breakfast": "Breakfast & brunch",
    "korean": "Korean", "ramen": "Ramen", "noodle": "Noodles", "irish": "Irish pub", "french": "French", "cajun": "Cajun & Creole",
    "donut": "Doughnuts", "doughnut": "Doughnuts", "ice_cream": "Ice cream", "dessert": "Dessert", "bubble_tea": "Bubble tea",
    "tea": "Tea", "juice": "Juice & smoothies", "bakery": "Bakery", "deli": "Deli", "wings": "Wings", "hot_dog": "Hot dogs",
    "salad": "Salads", "poke": "Poke", "hawaiian": "Hawaiian", "german": "German", "spanish": "Spanish", "tapas": "Tapas",
    "latin_american": "Latin American", "caribbean": "Caribbean", "middle_eastern": "Middle Eastern", "lebanese": "Lebanese",
    "turkish": "Turkish", "persian": "Persian", "soul_food": "Soul food", "southern": "Southern", "diner": "Diner",
    "grill": "Grill", "fish": "Fish", "crepe": "Crepes", "pretzel": "Pretzels", "frozen_yogurt": "Frozen yogurt",
    "bagel": "Bagels", "cake": "Cakes", "pasta": "Pasta", "chili": "Chili", "fried_chicken": "Fried chicken",
    "fish_and_chips": "Fish & chips", "oysters": "Oysters", "regional": "Regional", "international": "International",
    "brewpub": "Brewpub", "pub": "Pub food", "taco": "Tacos", "filipino": "Filipino", "ethiopian": "Ethiopian", "african": "African",
    "nepalese": "Nepalese", "himalayan": "Himalayan", "pakistani": "Pakistani", "wine": "Wine", "cocktails": "Cocktails",
    "buffet": "Buffet", "arab": "Arab", "pancake": "Pancakes", "smoothie": "Juice & smoothies", "bubble tea": "Bubble tea",
}

# name -> cuisine (first hit wins). Checked against the whole Norman list, not a sample.
NAME_CUISINE = [
    (r"\b(taco|tacos|cantina|mexi\w*|taqueria|burrito|mezcal|tequila|chelino|casa blanca|mama roja|mamaveca|tarahumara|belmar|michoacana|el rincon|chapin|juan del fuego|fortaleza|del taco|taco mayo|qdoba|chipotle|fuzzy|torchy|yo pablo|pepe delgado|rosa mezcal|el toro|el huevo|el sombrero|el chico|velvet taco|groovy mule|tamale|tamales)\b", "Mexican"),
    (r"\b(del rancho|classic 50|shake shack|fat shack|greene turtle|van.?s pig|pig stand|pit and pie)\b", "American"),
    (r"\b(china|panda garden|happy family|happy garden|wu.?s panda)\b", "Chinese"), (r"\b(shawarma|sky european)\b", "Mediterranean"),
    (r"\b(sharetea|swig|stella nova|starbuck)\b", "Coffee & tea"), (r"\b(snow shepherd|shaved n|sno\b)\b", "Ice cream & shaved ice"),
    (r"\b(italian|ristorante|pasta|pizza|pizzeria|gaberino|benvenuti|othello|sergio|victoria.?s the pasta|doni|volare|amy.?s italian|olive garden|cici|mazzio|marco|domino|papa john|little caesars|hideaway|pizza hut|mr\.? gatti|manna wood|carlo & luigi)\b", "Italian"),
    (r"\b(sushi|ramen|hibachi|japanese|yamato|koto|tatsumaki|tamashii|ichiban|volcano sushi|moon sushi|teriyaki|poke|fuji san|mai sushi|isushi)\b", "Japanese"),
    (r"\b(thai|thawan|panang|kitchen 21)\b", "Thai"), (r"\b(india|indian|masala|curry|tandoor)\b", "Indian"),
    (r"\b(china|chinese|pei wei|p\.f\. chang|happy monk|panda express|golden chef|happy family|happy garden|kingdom chinese|fantasy chinese|china wonder|crimson panda)\b", "Chinese"),
    (r"\b(pho\b|banh mi|vietnam)\b", "Vietnamese"), (r"\b(cupbop|korean|bibimbap)\b", "Korean"),
    (r"\b(hawaiian|mo.?bettah|mamaka|poke)\b", "Hawaiian"), (r"\b(gyro|kebab|kabob|doner|shawarma|mediterranean|cava\b|falafel)\b", "Mediterranean"),
    (r"\b(steakhouse|steak house|longhorn|outback steakhouse|saltgrass|ranch steakhouse|texas roadhouse)\b", "Steakhouse"),
    (r"\b(crab|catfish|oyster|lobster|seafood|dancing crab|fish\b)\b", "Seafood"), (r"\b(bbq|bar-b-q|barbecue|barbeque|rudy|billy sims|dickey|bumm)\b", "Barbecue"),
    (r"\b(burger|burgers|bad daddy|red robin|five guys|freddy|whataburger|sonic|braum|jack in the box|carl.?s jr|mcdonald|burger king|wendy|classic 50)\b", "Burgers"),
    (r"\b(chicken|chick-fil-a|chick fil a|popeye|kentucky fried|kfc|cane|zaxby|slim chickens|wing\w*|brasco)\b", "Chicken"),
    (r"\b(irish|o.?connell)\b", "Irish pub"), (r"\b(deli\b|subs?\b|sandwich|jersey mike|jimmy john|firehouse|cheba hut|schlotzsky|mcalister|pickleman|city bites|potbelly|which wich)\b", "Sandwiches"),
    (r"\b(coffee|espresso|cafe on the corner|tea cafe|7brew|dutch bros|starbucks|scooter|black rifle|grind\b|gray owl|morning flower|pointe brew)\b", "Coffee"),
    (r"\b(hteao|boba|bubble tea|tea house|teahouse)\b", "Tea"), (r"\b(hookah)\b", "Hookah"), (r"\b(daiquiri)\b", "Daiquiris"),
    (r"\b(donut|doughnut|dunkin|krispy|shipley|daylight)\b", "Doughnuts"), (r"\b(bakery|french bakery|la madeleine|baguette|bakes|cakes?\b|cupcake|bundt|cookie|crumbl|insomnia|chocolate|pretzel|auntie anne|bagel|einstein)\b", "Bakery & sweets"),
    (r"\b(custard|ice cream|creamatory|gelato|frozen yogurt|pinkberry|menchie|dippin|sno\b|shaved ice|snow cone|sno-?balls?|eskimo|kona ice|orange leaf|dairy queen|baskin|cold stone)\b", "Ice cream & shaved ice"),
    (r"\b(nutrition|smoothie|juice|protein bar|blends)\b", "Smoothies & shakes"),
    (r"\b(diner|denny|cracker barrel|neighborhood jam|interurban|cheddar|ihop|waffle|pancake|jimmy.?s egg|hatch early|breakfast|egg\b|biscuit|golden corral|boom-a-rang)\b", "American"),
    (r"\b(brewing|brewery|brewhouse|brewed|brew pub)\b", "Brewery"), (r"\b(winery|wine\b)\b", "Wine"),
]
FOOD_RX = re.compile(
    r"\b(restaurant|grill|grille|kitchen|eatery|eats|cafe|café|coffee|espresso|bistro|diner|cantina|taqueria|taco|tacos|burrito|pizza|pizzeria|"
    r"burger|burgers|bbq|bar-b-q|barbecue|barbeque|smokehouse|steak|steakhouse|seafood|catfish|crab|oyster|sushi|ramen|hibachi|teriyaki|poke|pho|banh mi|"
    r"noodle|wok|chinese|thai|japanese|korean|indian|mexican|italian|mediterranean|greek house|gyro|kebab|kabob|doner|deli|subs?|sandwich|bagel|bakery|"
    r"bakes|donut|doughnut|cake|cakes|cupcake|cookie|cookies|chocolate|pretzel|custard|gelato|ice cream|creamatory|yogurt|sno|shaved ice|snow cone|"
    r"tea|teahouse|boba|smoothie|juice|nutrition|blends|protein bar|waffle|pancake|egg|eggs|breakfast|brunch|chicken|wings|wing|hot dog|dog|"
    r"bowl|bowls|bites|grub|food|foods|fresh|express|hut|house|bar|pub|tavern|saloon|lounge|taproom|brewing|brewery|brewhouse|brew|cocktail|"
    r"club|social|winery|cuisine|buffet|fry|fries|fried|roast|roastery|bake|baked|market cafe|cafeteria|canteen|"
    r"mcdonald|burger king|wendy|sonic|braum|whataburger|taco bell|taco mayo|del taco|arby|kfc|kentucky fried|popeye|chick-fil-a|chick fil a|"
    r"raising cane|zaxby|slim chickens|jack in the box|carl.?s jr|five guys|freddy|andy|panda express|subway|jimmy john|jersey mike|firehouse|"
    r"cheba hut|panera|einstein|dunkin|starbucks|dutch bros|7brew|scooter|little caesars|domino|papa john|marco|pizza hut|cici|mazzio|hideaway|"
    r"chipotle|qdoba|cava|cupbop|hawaiian bros|mo.?bettah|mamaka|chicken salad chick|city bites|schlotzsky|mcalister|pickleman|potbelly|which wich|"
    r"auntie anne|crumbl|insomnia|nothing bundt|great american cookie|menchie|pinkberry|dippin|kona ice|eskimo|bahama buck|dairy queen|baskin|"
    r"cold stone|il dolce|hteao|golden corral|ihop|denny|cracker barrel|olive garden|red lobster|longhorn|outback steakhouse|saltgrass|cheddar|"
    r"red robin|bj.?s|buffalo wild wings|wingstop|chili.?s|applebee|texas roadhouse|jimmy.?s egg|hatch early|daylight|krispy|shipley|"
    r"apple tree|amy cakes|doughnuttery|gambill|magic masala|kebabish|brasco|leviity|dara marie|pink pig|lohmann|better bites|baked bear|"
    r"cool beans|bookmark|avara|earth natural|flying cow|fowler honda-caf|kaizen|opuluck|joey|hasslers|fusion|"
    r"delish|hot chicken|moes|golden chef|old #9|old number|mrhui|juan del fuego|fortaleza|"
    r"el rincon|doner street|crimson panda|baja fresh|la divina|la monarca|michoacana|homestead steaks|praise and pop|floof|fruit pop|bougie bunny|"
    r"3 squares|pony express|china|panda garden|happy family|happy garden|classic 50|del rancho|dominos|fat shack|baguette|pit and pie|"
    r"press and plow|plow|quiznos|shake shack|sharetea|shaved|winebar|wine bar|gourmet|sweet shop|snacks|snow|starbuck|stella nova|swig|"
    r"tamale|tamales|brown bag|greene turtle|pig stand|van.?s pig|shawarma|grind|grindz|soonercade)(?:'?s|z)?\b", re.I)
NONFOOD_RX = re.compile(
    r"\b(school|elementary|middle school|high school|academy|daycare|day care|child|children|learning|preschool|head start|nursing|rehab|"
    r"hospital|medical|clinic|health\b|healthplex|senior|living|retirement|church|ministry|ministries|fraternity|sorority|greek\s*-|dormitor|"
    r"housing|cafeteria|concession|concessions|commissary|food truck|vending|corrections|jail|detention|ymca|pool\b|stadium|arena|"
    r"field house|motel|camp\b|country club|golf club|snack bar|snack shack|lions club|vfw|american legion|elks|moose|museum|library|"
    r"theater|theatre|cinema|bingo|casino|supermarket|supermart|grocery|grocers|food mart|food store|quick stop|express mart|short stop|"
    r"you stop|murphy usa|fina stop|c-express|harp.?s|abarrotes|international store|international pantry|quality meats|butcher|meat market|"
    r"pure water|water & ice|thunderbird ice|marina|memorial park|fairgrounds|community works|food and shelter|salvation army|aging service|"
    r"loveworks|recovery center|mccarty center|gift shop|public schools|nps -|pack shack|technology center|life sciences|ihub|nextep|bosch|"
    r"hitachi|holdings|franchising|premier sports|optimist|goode ideas|cube b|atwoods|barnes & noble|five below|hobby lobby|homegoods|"
    r"hot topic|old navy|ollie|michaels|gnc\b|hallmark|furniture|planet fitness|dispensary|cannabis|releaf|kanna|420|high society|"
    r"how high|bee high|dank|chronic|mr\.? green|green doctor|moqana|green buffalo|next elevation|outback cannabis|king kanna|"
    r"mango cannabis|gladiator|buddies|wine & spirits|spirits|liquor|tobacco|vape|smoke|pharmacy|walgreens|cvs|walmart|target|homeland|"
    r"crest|sprouts|aldi|dollar|7-eleven|circle k|oncue|on cue|casey|love.?s|conoco|phillips|shell|valero|sinclair|catering|caterer|"
    r"beer trailer|beer pushcart|beer puchcart|pushcart|push cart|pushchart|seasonal|trailer|kiosk|cart\b|tent\b|grab & go|grab and go|"
    r"prepackaged|redzone|boomarang|santee|kickoff|upper deck|west floor|east club|south club|club south|north ada|heisman|goal line|"
    r"lnc\b|^ms\b|ms \d|ms [a-z]|levy|ou baseball|ou softball|ou gray|ou life|cross a|cross c|couch restaurants|cate ala carte|"
    r"little axe|exhibit|norman - aging|norman optimist|central kitchen|canteen|mai franchising|no hit|hitachi|jci|blue sky|"
    r"bazaar|legends times two|regal|amc\b|next gen sports|oklahoma premier|nutrition|protein bar|supplement|hebrews)\b", re.I)
IN_BUILDING_RX = re.compile(r"\b(rm|room|bldg|building|floor|fl)\b\.?\s*\w*", re.I)   # '1406 Asp Ave Rm 207a': a counter inside a building, not a storefront
GREEK_RX = re.compile(r"\b(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega)\b.*"
                      r"\b(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega)\b", re.I)
VENUE_ADDRESSES = re.compile(r"^(180 W BROOKS|2900 S? ?JENKINS|401 W? ?IMHOFF|300 W IMHOFF|2500 S JENKINS|333 4TH ST|1000 ASP|1200 ASP|33\d CATE CENTER|"
                             r"1695 ASP|2000 168TH|3300 HEALTHPLEX|5005 YORK|1800 E IMHOFF|1800 N INTERSTATE DR, SUITE|100 E LINDSEY)", re.I)

EXCLUDE_NAMES = [
    (r"\blevy restaurants\b|mccasland field house", "concessions operator for OU venues, not a public restaurant"),
    (r"\bauto spa\b|\bcar wash\b", "a car wash"), (r"\briverwind beverage\b", "the casino's beverage licence, not a venue of its own"),
    (r"\bpinot.?s palette\b", "a paint-and-sip studio"), (r"\bcatering\b", "a caterer, no dining room"),
    (r"\bregal cinemas\b|\bamc\b", "a cinema"), (r"\bnext gen sports\b", "a sports complex"),
    (r"\bstonehill norman\b", "a senior-living community (members only)"), (r"\bmidway grocery & market\b", "the grocery's caterer licence (see Midway Deli)"),
]
HOTEL_RX = re.compile(r"\b(hotel|inn\b|courtyard|embassy suites|residence inn|hilton|marriott|conference center|bed & breakfast|garner hotel|noun hotel|nced)\b", re.I)
ENT_RX = re.compile(r"\b(bowling|lanes|golf|main event|heyday|entertainment|chuck e|arcade|soonercade|top ?golf|five iron|axe|pickleball|escape|trails golf|westwood park|thunderbird entertainment)\b", re.I)
LOUNGE_RX = re.compile(r"\b(hookah|cigar|pipe & tobacco|social club|lounge)\b", re.I)
BAR_RX = re.compile(r"\b(bar\b|pub\b|tavern|saloon|taproom|tap room|daiquiri|club\b|heist|barracuda|baracuda|mont\b|opolis|prohibition|the garage|the standard|red brick|rock house|blue ?bonnet|roxy|logie|stepbrothers|library|sideline|maverick|coaches|happy monk|old number 9|old #9|the deli\b|volare|mickey|royal pipe|elegance|maximillian|the wagon|porch\b|nompton|press & plow|sooner station|flight club)\b", re.I)
NOT_A_BAR_RX = re.compile(r"\b(protein bar|juice bar|smoothie bar|salad bar|sushi bar|oyster bar|coffee bar|snack bar|nutrition|bar-b-q|barbecue|bar & grill|bar and grill|burger bar)\b", re.I)
BREW_RX = re.compile(r"\b(brewing|brewery|brewer|brewhouse|brewed|taproom)\b", re.I)
WINE_RX = re.compile(r"\b(winery|vineyard|sabatia|native spirits)\b", re.I)
CAFE_RX = re.compile(r"\b(coffee|cafe|café|espresso|tea\b|hteao|boba|bakery|bakes|donut|doughnut|dunkin|bagel|juice|smoothie|nutrition|blends|protein bar|7brew|dutch bros|starbucks|scooter|grind\b|roastery|brews &|bookmark|daylight|krispy|shipley)\b", re.I)
DESSERT_RX = re.compile(r"\b(custard|ice cream|creamatory|gelato|frozen yogurt|pinkberry|menchie|dippin|sno\b|shaved ice|snow cone|eskimo|kona ice|cookie|cookies|crumbl|insomnia|chocolate|bundt|cakes?\b|cupcake|cotton candy|fruit pop|great american cookie|il dolce|orange leaf|dairy queen|baskin|cold stone|amy cakes|apple tree)\b", re.I)
FAST_RX = re.compile(r"\b(mcdonald|burger king|wendy|sonic|braum|whataburger|taco bell|taco mayo|del taco|arby|kfc|kentucky fried|popeye|chick-fil-a|chick fil a|raising cane|zaxby|slim chickens|jack in the box|carl.?s jr|five guys|freddy|andy.?s frozen|panda express|subway|jimmy john|jersey mike|firehouse|cheba hut|panera|einstein|little caesars|domino|papa john|marco.?s|cici|chipotle|qdoba|cava\b|cupbop|hawaiian bros|mo.?bettah|chicken salad chick|city bites|schlotzsky|mcalister|potbelly|which wich|auntie anne|pretzel|del rancho|wingstop|chicken express|hteao|golden chef|moes hot chicken|pizza shuttle|mazzio|express\b|drive thru|drive-thru)\b", re.I)
DELI_RX = re.compile(r"\b(deli and grocery|forward foods|cheese|la baguette|artisan|market\b)\b", re.I)
UNIT_RX = re.compile(r"\s*(?:,\s*)?(?:#\s*[\w-]+|(?:ste|suite|unit|bldg|rm|room|spc|space)\.?\s*#?\s*[\w-]+)\s*$", re.I)


def exclusion_reason(name, street=""):
    for rx, why in EXCLUDE_NAMES:
        if re.search(rx, name, re.I):
            return why
    if GREEK_RX.search(name) or re.search(r"\bgreek\s*-", name, re.I):
        return "a fraternity or sorority house kitchen"
    if VENUE_ADDRESSES.match((street or "").upper()):
        return "a concession stand, campus dining hall or staff canteen"
    if IN_BUILDING_RX.search(street or ""):
        return "a counter inside a building (a room number in the address), not a storefront"
    if NONFOOD_RX.search(name):
        return "not a restaurant or bar (a store, dispensary, institution, stand or service kitchen)"
    return None


def has_food_signal(name):
    return bool(FOOD_RX.search(name))


def cuisine_labels(place):
    osm = place.get("osm")
    labels = []
    if osm and osm.get("cuisine"):
        for c in re.split(r"[;,]", osm["cuisine"]):
            c = c.strip().lower()
            if c:
                labels.append(CUISINE_LABEL.get(c, c.replace("_", " ").capitalize()))
    if not labels:
        for rx, lab in NAME_CUISINE:
            if re.search(rx, place["name"], re.I):
                labels.append(lab)
                break
    out = []
    for l in labels:
        if l not in out:
            out.append(l)
    return out[:3]


def category(place):
    name = place["name"]
    osm = place.get("osm") or {}
    kind = osm.get("kind", "")
    lic = set(place.get("licence_types") or [])
    if exclusion_reason(name, place.get("street", "")):
        return "excluded"
    if kind == "brewery" or BREW_RX.search(name) or lic & {"Small Brewer", "Brew Pub"}:
        return "brewery"
    if WINE_RX.search(name) or "Small Farm Winery" in lic:
        return "winery"
    if HOTEL_RX.search(name) and kind not in ("restaurant", "bar", "pub", "cafe") and not re.search(r"eatery|starbucks|pony express|grill|kitchen", name, re.I):
        return "hotel_bar"
    if ENT_RX.search(name):
        return "entertainment"
    if LOUNGE_RX.search(name) and kind not in ("restaurant",):
        return "lounge"
    if kind in ("bar", "pub", "nightclub"):
        return "bar"
    if kind in ("ice_cream",) or (kind == "" and DESSERT_RX.search(name) and not re.search(r"bakery|cafe|coffee", name, re.I)):
        return "dessert"
    if kind == "cafe" or (kind == "" and CAFE_RX.search(name) and not (BAR_RX.search(name) and not NOT_A_BAR_RX.search(name))):
        return "cafe"
    if kind in ("fast_food",) or (kind == "" and FAST_RX.search(name)):
        return "fast_food"
    if kind in ("deli", "bakery") or DELI_RX.search(name):
        return "deli"
    if kind == "restaurant":
        return "restaurant"
    if BAR_RX.search(name) and not NOT_A_BAR_RX.search(name) and not re.search(r"grill|kitchen|restaurant|eatery|cafe|pizza|taco|steak|bistro|bbq", name, re.I):
        return "bar"
    if lic & {"Mixed Beverage Combination", "Beer and Wine"} or cuisine_labels(place):
        return "restaurant"
    if "Mixed Beverage" in lic:
        if re.search(r"grill|kitchen|restaurant|eatery|cafe|pizza|taco|steak|bistro|bbq|sushi|ramen|diner|cantina|house", name, re.I):
            return "restaurant"
        return "bar"
    if has_food_signal(name):
        return "restaurant"
    return "other"


# Norman areas by position: ordered rules, first hit wins. Boxes were read off the map, not from any listing.
AREAS = [
    ("campus-corner", "Campus Corner", lambda la, lo: 35.2100 <= la <= 35.2190 and -97.4505 <= lo <= -97.4395),
    ("ou-campus", "OU campus", lambda la, lo: 35.1900 <= la < 35.2100 and -97.4560 <= lo <= -97.4330),
    ("downtown", "Downtown & Main Street", lambda la, lo: 35.2190 < la <= 35.2290 and -97.4640 <= lo <= -97.4280),
    ("lindsey", "Lindsey Street", lambda la, lo: 35.1960 <= la <= 35.2060 and -97.4850 <= lo < -97.4560),
    ("west-norman", "West Norman & I-35", lambda la, lo: lo < -97.4640 and 35.1900 <= la <= 35.2600),
    ("north-norman", "North Norman", lambda la, lo: la > 35.2290 and -97.4640 <= lo <= -97.4200),
    ("east-norman", "East Norman", lambda la, lo: lo > -97.4280 and 35.1800 <= la <= 35.2600 and lo <= -97.3700),
    ("south-norman", "South Norman", lambda la, lo: la < 35.1960 and lo <= -97.3700),
    ("far-east", "Highway 9 & Lake Thunderbird", lambda la, lo: lo > -97.3700),
]
AREA_LABEL = {k: v for k, v, _ in AREAS}


def area_for(lat, lon, street=""):
    if lat is not None and lon is not None:
        for key, label, fn in AREAS:
            if fn(lat, lon):
                return key
    s = (street or "").lower()
    if re.search(r"\b(asp|buchanan|boyd|white st|eufaula)\b", s):
        return "campus-corner"
    if re.search(r"\b(main st|gray st|crawford|peters|james garner|jones ave)\b", s) and not re.search(r"\b(2\d{3}|3\d{3}) w main", s):
        return "downtown"
    if re.search(r"\b(ed noble|interstate|24th ave|24th avenue|copperfield|conference|legacy park|banker|medical park|market pl|mt williams|mount williams)\b", s):
        return "west-norman"
    if re.search(r"\blindsey\b", s):
        return "lindsey"
    if re.search(r"\b(12th ave|alameda|classen|porter|hal muldrow|opportunity)\b", s):
        return "east-norman"
    if re.search(r"\b(highway ?9|hwy 9|state highway|day dr|selah|e lindsey)\b", s):
        return "far-east"
    if re.search(r"\b(robinson|tecumseh|36th)\b", s):
        return "north-norman"
    return "elsewhere"
