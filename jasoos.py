import requests
import csv
import sys
import io
import time
import re
from urllib.parse import urlparse

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === CONFIGURATION ===
API_KEY = "90fe9a9b51538cd2fb2a4ac882dec6471108bbbbe46114f41acdd018df4e74a7"

# Search strategy: 3 targeted API calls per product for maximum accuracy
# - API Call 1: Image + "brand site:myntra.com"
# - API Call 2: Image + "brand site:slikk.club"
# - API Call 3: Image + "brand site:brandsite.com" (if brand has own site)
# Then apply comprehensive local filtering to all results

COVERAGE_THRESHOLD = 0.50  # 50% - for reporting only

# Primary sites - Always search these
PRIMARY_SITES = ["myntra", "slikk"]

# Target shopping sites - Primary 2 + Brand sites
SHOPPING_SITES = {
    # ═══════════════════════════════════════════════════════════════════
    # PRIMARY MARKETPLACES
    # ═══════════════════════════════════════════════════════════════════
    "myntra": ["myntra.com"],
    "slikk": ["slikk.club"],
    
    # ═══════════════════════════════════════════════════════════════════
    # BRAND SITES (A-Z by slug)
    # ═══════════════════════════════════════════════════════════════════
    "asian": ["asianfootwears.com"],
    "atom": [],  # Marketplace only
    "avant": ["avantgardeoriginal.com"],
    "bad_and_boujee": ["badandboujee.in"],
    "bauge": ["baugebags.com"],
    "beeglee": ["beeglee.in"],
    "bersache": ["bersache.com"],
    "bewakoof": ["bewakoof.com"],
    "blackberrys": ["blackberrys.com"],
    "bummer": ["bummer.in"],
    "campus_sutra": ["campussutra.com"],
    "chapter_2": ["chapter2drip.com"],
    "chumbak": ["chumbak.com"],
    "chupps": ["chupps.com"],
    "color_capital": ["colorcapital.in"],
    "crazybee": ["mavinclub.com"],
    "cult": [],  # Marketplace only
    "ecoright": ["ecoright.com"],
    "freehand": [],  # Sub-brand of TIGC, marketplace only
    "guns_and_sons": ["gunsnsons.com"],
    "haute_sauce": ["buyhautesauce.com"],
    "highlander": [],  # Marketplace only
    "indian_garage_co": ["tigc.in"],
    "jar_gold": [],  # Marketplace only
    "jockey": ["jockey.in"],
    "just_lil_things": ["justlilthings.in"],
    "kedias": [],  # Marketplace only
    "klydo_x_revolte": ["klydo.in"],
    "lancer": [],  # Marketplace only
    "levis": ["levi.in"],
    "locomotive": [],  # Marketplace only
    "main_character": ["maincharacterindia.com"],
    "minute_mirth": [],  # Marketplace only
    "mydesignation": ["mydesignation.com"],
    "mywishbag": ["mywishbag.com"],
    "nailinit": ["nailin.it"],
    "palmonas": ["palmonas.com"],
    "pinacolada": ["buypinacolada.com"],
    "puma": ["in.puma.com"],
    "qissa": ["shopqissa.com"],
    "rapidbox": ["rapidbox.in"],
    "recast": ["recast.co.in"],
    "salty": ["salty.co.in"],
    "sassafras": ["sassafras.in"],
    "silisoul": ["silisoul.com"],
    "styli": ["stylishop.com", "styli.in"],
    "the_bear_house": ["thebearhouse.com", "bearhouseindia.com", "thebearhouse.in"],
    "the_indian_garage_co": ["tigc.in"],  # Alias for indian_garage_co
    "the_kurta": ["thekurtacompany.com"],
    "theater": ["theater.xyz"],
    "thela_gaadi": ["thelagaadi.com"],
    "tokyo_talkies": [],  # Marketplace only
    "untung": ["untung.in"],
    "vara_vishudh": [],  # Marketplace only
    "vishudh": [],  # Marketplace only
    "xyxx": ["xyxxcrew.com"],
    
    # ═══════════════════════════════════════════════════════════════════
    # SASSAFRAS SUB-BRANDS (all map to sassafras.in)
    # ═══════════════════════════════════════════════════════════════════
    "mascln_sassafras": ["sassafras.in"],
    "shae_by_sassafras": ["sassafras.in"],
    "pink_paprika_by_sassafras": ["sassafras.in"],
    "sassafras_basics": ["sassafras.in"],
    "sassafras_worklyf": ["sassafras.in"],
    
    # Legacy aliases (keep for backward compatibility)
    "bearhouse": ["thebearhouse.com", "bearhouseindia.com", "thebearhouse.in"],
    "bearcompany": ["bearcompany.in", "thebearcompany.com"],
}

def get_brand_site(brand_name):
    """
    Get the brand's own website (if exists)
    Returns: brand_site_key or None
    
    ROBUST: Handles all Sassafras sub-brands (Shae, MASCLN, Pink Paprika)
    and maps them to sassafras.in
    """
    # Convert brand name to lowercase for matching
    # Remove ALL spaces, hyphens, and underscores for consistent matching
    brand_lower = brand_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Enhanced brand mapping with more variations
    brand_mapping = {
        # ══════════════════════════════════════════════════════════
        # A-Z BRANDS
        # ══════════════════════════════════════════════════════════
        
        # ASIAN
        "asian": "asian",
        "asianfootwear": "asian",
        "asianfootwears": "asian",
        
        # ATOM (marketplace only)
        "atom": "atom",
        
        # Avant
        "avant": "avant",
        "avantgarde": "avant",
        "avantgardeoriginal": "avant",
        
        # Bad & Boujee
        "badboujee": "bad_and_boujee",
        "badandboujee": "bad_and_boujee",
        "bad&boujee": "bad_and_boujee",
        
        # Bauge
        "bauge": "bauge",
        "baugebags": "bauge",
        
        # BEEGLEE
        "beeglee": "beeglee",
        
        # Bersache
        "bersache": "bersache",
        
        # Bewakoof
        "bewakoof": "bewakoof",
        "bwkf": "bewakoof",
        
        # Blackberrys
        "blackberrys": "blackberrys",
        "blackberry": "blackberrys",
        
        # Bummer
        "bummer": "bummer",
        
        # Campus Sutra
        "campussutra": "campus_sutra",
        "campus": "campus_sutra",
        
        # Chapter 2
        "chapter2": "chapter_2",
        "chaptertwo": "chapter_2",
        
        # Chumbak
        "chumbak": "chumbak",
        
        # CHUPPS
        "chupps": "chupps",
        
        # Color Capital
        "colorcapital": "color_capital",
        
        # Crazybee
        "crazybee": "crazybee",
        "mavinclub": "crazybee",
        "mavin": "crazybee",
        
        # CULT (marketplace only)
        "cult": "cult",
        
        # Ecoright
        "ecoright": "ecoright",
        "eco right": "ecoright",
        
        # Freehand (TIGC sub-brand)
        "freehand": "freehand",
        "free hand": "freehand",
        
        # Guns & Sons
        "gunsandsons": "guns_and_sons",
        "gunssons": "guns_and_sons",
        "gunsnsons": "guns_and_sons",
        "guns&sons": "guns_and_sons",
        
        # Haute Sauce
        "hautesauce": "haute_sauce",
        
        # HIGHLANDER (marketplace only)
        "highlander": "highlander",
        
        # Jar Gold (marketplace only)
        "jargold": "jar_gold",
        
        # Jockey
        "jockey": "jockey",
        
        # Just Lil Things
        "justlilthings": "just_lil_things",
        "just lil things": "just_lil_things",
        
        # KEDIAS (marketplace only)
        "kedias": "kedias",
        
        # Klydo X Revolte
        "klydoxrevolte": "klydo_x_revolte",
        "klydo": "klydo_x_revolte",
        "revolte": "klydo_x_revolte",
        
        # LANCER (marketplace only)
        "lancer": "lancer",
        
        # Levi's
        "levis": "levis",
        "levi": "levis",
        "levis": "levis",
        
        # LOCOMOTIVE (marketplace only)
        "locomotive": "locomotive",
        
        # Main Character
        "maincharacter": "main_character",
        
        # MINUTE MIRTH (marketplace only)
        "minutemirth": "minute_mirth",
        
        # MyDesignation
        "mydesignation": "mydesignation",
        "designation": "mydesignation",
        
        # MYWISHBAG
        "mywishbag": "mywishbag",
        
        # nailinit
        "nailinit": "nailinit",
        "nail in it": "nailinit",
        
        # PALMONAS
        "palmonas": "palmonas",
        
        # PINACOLADA
        "pinacolada": "pinacolada",
        
        # Puma
        "puma": "puma",
        
        # QISSA
        "qissa": "qissa",
        
        # RapidBox
        "rapidbox": "rapidbox",
        "rapid box": "rapidbox",
        
        # Recast
        "recast": "recast",
        
        # Salty
        "salty": "salty",
        
        # Sassafras and sub-brands
        "sassafras": "sassafras",
        "sassafrasbasics": "sassafras",
        "sassafrasworklyf": "sassafras",
        # MASCLN variants
        "masclnsassafras": "mascln_sassafras",
        "masclnsassafras": "mascln_sassafras",
        "mascln": "mascln_sassafras",
        "masclnbysassafras": "mascln_sassafras",
        # Shae variants
        "shaebysassafras": "shae_by_sassafras",
        "shaebysassafras": "shae_by_sassafras",
        "shae": "shae_by_sassafras",
        "shaesassafras": "shae_by_sassafras",
        # Pink Paprika variants
        "pinkpaprikabysassafras": "pink_paprika_by_sassafras",
        "pinkpaprikabysassafras": "pink_paprika_by_sassafras",
        "pinkpaprika": "pink_paprika_by_sassafras",
        "pinkpaprikasassafras": "pink_paprika_by_sassafras",
        
        # SILISOUL
        "silisoul": "silisoul",
        
        # Styli
        "styli": "styli",
        "stylishop": "styli",
        
        # The Bear House
        "bearhouse": "the_bear_house",
        "thebearhouse": "the_bear_house",
        "bearhouseindia": "the_bear_house",
        "thebearhouseindia": "the_bear_house",
        
        # Bear Company (legacy)
        "bearcompany": "bearcompany",
        "thebearcompany": "bearcompany",
        "bear": "bearcompany",
        "bearco": "bearcompany",
        
        # The Indian Garage Co
        "indiangarageco": "indian_garage_co",
        "indiangaragecompany": "indian_garage_co",
        "theindiangaragecompany": "indian_garage_co",
        "theindiangaragecom": "indian_garage_co",
        "theindiangarageco": "indian_garage_co",
        "theindiangarage": "indian_garage_co",
        "tigc": "indian_garage_co",
        "indiangarage": "indian_garage_co",
        
        # THE KURTA COMPANY
        "thekurta": "the_kurta",
        "thekurtacompany": "the_kurta",
        "kurta": "the_kurta",
        
        # Theater
        "theater": "theater",
        "theatre": "theater",
        
        # Thela Gaadi
        "thelagaadi": "thela_gaadi",
        "thela gaadi": "thela_gaadi",
        
        # Tokyo Talkies (marketplace only)
        "tokyotalkies": "tokyo_talkies",
        
        # Untung
        "untung": "untung",
        
        # Vara By Vishudh (marketplace only)
        "varabyvishudh": "vara_vishudh",
        "vara": "vara_vishudh",
        
        # Vishudh (marketplace only)
        "vishudh": "vishudh",
        
        # XYXX
        "xyxx": "xyxx",
        "xyxxcrew": "xyxx",
    }
    
    # Get brand's own site if it exists in our database
    brand_site = brand_mapping.get(brand_lower)
    if brand_site and brand_site in SHOPPING_SITES:
        return brand_site
    
    # FALLBACK: Check if brand contains sassafras-related keywords
    # This ensures ALL Sassafras sub-brands map to sassafras.in
    sassafras_keywords = ['sassafras', 'mascln', 'shae', 'paprika']
    if any(keyword in brand_lower for keyword in sassafras_keywords):
        if "sassafras" in SHOPPING_SITES:
            return "sassafras"
    
    return None

def extract_domain(url):
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        return domain
    except:
        return ""

def identify_site(url):
    """Identify which shopping site the URL belongs to"""
    domain = extract_domain(url)
    url_lower = url.lower()
    
    for site_key, site_patterns in SHOPPING_SITES.items():
        for pattern in site_patterns:
            if pattern in domain or pattern in url_lower:
                return site_key
    return None

def extract_price_from_match(match_data):
    """
    Extract price from match data - handles all possible price formats from SerpAPI
    Returns only numeric values without currency symbols
    """
    price_info = match_data.get("price", {})
    
    # Case 1: Price is a dictionary with 'value' and/or 'extracted_value'
    if isinstance(price_info, dict):
        # Try 'value' first (formatted string like "₹660*")
        price_value = price_info.get("value", "")
        if price_value and price_value not in ["N/A", "", "null"]:
            # Clean the price value
            cleaned = re.sub(r'[₹Rs.,\s*INR]', '', price_value, flags=re.IGNORECASE)
            if cleaned and cleaned.replace('.', '').isdigit():
                return cleaned
        
        # Try 'extracted_value' (usually numeric)
        extracted = price_info.get("extracted_value", "")
        if extracted and str(extracted) not in ["N/A", "", "null"]:
            return str(extracted)
    
    # Case 2: Price is a string
    elif isinstance(price_info, str):
        if price_info and price_info not in ["N/A", "", "null"]:
            cleaned = re.sub(r'[₹Rs.,\s*INR]', '', price_info, flags=re.IGNORECASE)
            if cleaned and cleaned.replace('.', '').isdigit():
                return cleaned
    
    return "Price not displayed in listing"

def extract_colors_from_title(title):
    """Extract color keywords from title"""
    colors = [
        'black', 'white', 'blue', 'red', 'green', 'yellow', 'pink', 'purple', 
        'orange', 'brown', 'grey', 'gray', 'beige', 'navy', 'olive', 'maroon',
        'silver', 'gold', 'cream', 'khaki', 'tan', 'teal', 'burgundy', 'mint',
        'lavender', 'coral', 'peach', 'mustard', 'charcoal', 'rose'
    ]
    
    title_lower = title.lower()
    found_colors = [c for c in colors if c in title_lower]
    return found_colors

def check_brand_relaxed_match(match, target_brand, site_key):
    """
    RELAXED brand verification with site-specific rules
    - Brand's own site: Accept all (site presence = brand verified)
    - Marketplaces: Require brand in title OR URL
    Returns True if brand match is acceptable
    """
    title = match.get("title", "").lower()
    link = match.get("link", "").lower()
    source = match.get("source", "").lower()
    
    # If product is on brand's own website, skip brand verification
    if site_key and site_key not in ['myntra', 'slikk']:
        return True
    
    # For marketplaces, check brand presence
    target_lower = target_brand.lower()
    
    # Generate brand variations to check
    brand_keywords = target_lower.replace("-", " ").replace("_", " ").split()
    
    brand_variations = [
        target_lower.replace(" ", ""),
        target_lower.replace(" ", "-"),
        target_lower.replace(" ", "_"),
        target_lower,
    ]
    
    if len(brand_keywords) > 1:
        combined = "".join(brand_keywords)
        brand_variations.append(combined)
        
        if brand_keywords[0] in ["the"]:
            without_the = " ".join(brand_keywords[1:])
            brand_variations.append(without_the)
            brand_variations.append(without_the.replace(" ", ""))
    
    # Special brand-specific variations (A-Z)
    if "asian" in target_lower:
        brand_variations.extend(["asian", "asian footwear", "asianfootwears"])
    
    if "avant" in target_lower:
        brand_variations.extend(["avant", "avant garde", "avantgarde"])
    
    if "bad" in target_lower and "boujee" in target_lower:
        brand_variations.extend(["bad boujee", "bad and boujee", "bad & boujee"])
    
    if "bauge" in target_lower:
        brand_variations.extend(["bauge", "bauge bags"])
    
    if "beeglee" in target_lower:
        brand_variations.extend(["beeglee", "bee glee"])
    
    if "bersache" in target_lower:
        brand_variations.extend(["bersache"])
    
    if "bewakoof" in target_lower:
        brand_variations.extend(["bewakoof", "bwkf"])
    
    if "blackberrys" in target_lower or "blackberry" in target_lower:
        brand_variations.extend(["blackberrys", "blackberry"])
    
    if "bummer" in target_lower:
        brand_variations.extend(["bummer"])
    
    if "campus" in target_lower:
        brand_variations.extend(["campussutra", "campus sutra", "campus"])
    
    if "chapter" in target_lower:
        brand_variations.extend(["chapter2", "chapter 2", "chapter two"])
    
    if "chumbak" in target_lower:
        brand_variations.extend(["chumbak"])
    
    if "chupps" in target_lower:
        brand_variations.extend(["chupps"])
    
    if "color" in target_lower and "capital" in target_lower:
        brand_variations.extend(["color capital", "colorcapital"])
    
    if "crazybee" in target_lower or "mavin" in target_lower:
        brand_variations.extend(["crazybee", "mavin", "mavinclub"])
    
    if "ecoright" in target_lower:
        brand_variations.extend(["ecoright", "eco right"])
    
    if "freehand" in target_lower:
        brand_variations.extend(["freehand", "free hand"])
    
    if "guns" in target_lower or "sons" in target_lower:
        brand_variations.extend(["guns", "sons", "gunsnsons", "guns & sons", "guns and sons"])
    
    if "haute" in target_lower and "sauce" in target_lower:
        brand_variations.extend(["haute sauce", "hautesauce"])
    
    if "jockey" in target_lower:
        brand_variations.extend(["jockey"])
    
    if "just" in target_lower and "lil" in target_lower:
        brand_variations.extend(["just lil things", "justlilthings"])
    
    if "klydo" in target_lower or "revolte" in target_lower:
        brand_variations.extend(["klydo", "revolte", "klydo x revolte"])
    
    if "levi" in target_lower:
        brand_variations.extend(["levis", "levi", "levi's"])
    
    if "main" in target_lower and "character" in target_lower:
        brand_variations.extend(["main character", "maincharacter"])
    
    if "mydesignation" in target_lower or "designation" in target_lower:
        brand_variations.extend(["mydesignation", "my designation", "designation"])
    
    if "mywishbag" in target_lower:
        brand_variations.extend(["mywishbag", "my wish bag"])
    
    if "nailinit" in target_lower or "nail" in target_lower:
        brand_variations.extend(["nailinit", "nail in it"])
    
    if "palmonas" in target_lower:
        brand_variations.extend(["palmonas"])
    
    if "pinacolada" in target_lower or "pina" in target_lower:
        brand_variations.extend(["pinacolada", "pina colada"])
    
    if "puma" in target_lower:
        brand_variations.extend(["puma"])
    
    if "qissa" in target_lower:
        brand_variations.extend(["qissa"])
    
    if "rapidbox" in target_lower or "rapid" in target_lower:
        brand_variations.extend(["rapidbox", "rapid box"])
    
    if "recast" in target_lower:
        brand_variations.extend(["recast"])
    
    if "salty" in target_lower:
        brand_variations.extend(["salty"])
    
    if "sassafras" in target_lower or "mascln" in target_lower or "shae" in target_lower or "pink paprika" in target_lower or "basics" in target_lower or "worklyf" in target_lower:
        brand_variations.extend([
            "sassafras", "mascln", "shae", "pink paprika", "sassafras basics", "sassafras worklyf"
        ])
    
    if "silisoul" in target_lower:
        brand_variations.extend(["silisoul"])
    
    if "styli" in target_lower:
        brand_variations.extend(["styli", "stylishop"])
    
    if "bear" in target_lower:
        brand_variations.extend([
            "bear", "bearhouse", "bear house", "thebearhouse", "the bear house",
            "bearcompany", "bear company", "thebearcompany", "the bear company",
        ])
    
    if "indian" in target_lower and "garage" in target_lower:
        brand_variations.extend(["indiangarage", "indian garage", "tigc", "the indian garage co"])
    
    if "kurta" in target_lower:
        brand_variations.extend(["kurta", "the kurta", "the kurta company"])
    
    if "theater" in target_lower or "theatre" in target_lower:
        brand_variations.extend(["theater", "theatre"])
    
    if "thela" in target_lower or "gaadi" in target_lower:
        brand_variations.extend(["thela gaadi", "thelagaadi"])
    
    if "tokyo" in target_lower and "talkies" in target_lower:
        brand_variations.extend(["tokyo talkies", "tokyotalkies"])
    
    if "untung" in target_lower:
        brand_variations.extend(["untung"])
    
    if "vara" in target_lower or "vishudh" in target_lower:
        brand_variations.extend(["vara", "vishudh", "vara by vishudh"])
    
    if "xyxx" in target_lower:
        brand_variations.extend(["xyxx", "xyxx crew"])
    
    # Check if ANY brand variation exists in title, link, or source
    combined_text = f"{title} {link} {source}"
    
    for variation in brand_variations:
        if variation and len(variation) > 2 and variation in combined_text:
            return True
    
    return False

def is_valid_product_url(url):
    """
    STRICT URL validation - reject category/collection/search pages
    Returns True for actual product pages only
    """
    url_lower = url.lower()
    
    # Invalid patterns - these indicate non-product pages
    invalid_patterns = [
        '/collections/', '/collection/', '/category/', '/categories/',
        '/search', '?search=', '/s?', '/find/',
        '/brand/', '/brands/', '/sale/', '/deals/',
        '/all-products', '/shop?',
        '/filter', '/sort=',
        '?page=', '&page=',  # Pagination
        '/men/', '/women/', '/kids/', '/unisex/',
        '/clothing/', '/accessories/', '/footwear/'
    ]
    
    # Check for invalid patterns
    for pattern in invalid_patterns:
        if pattern in url_lower:
            return False
    
    # Site-specific validations
    # Marketplaces
    if 'myntra.com' in url_lower:
        return '/buy' in url_lower or '/p/' in url_lower
    elif 'slikk.club' in url_lower:
        return True  # Accept all Slikk URLs after invalid pattern check
    
    # Brand sites (A-Z)
    elif 'asianfootwears.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'avantgardeoriginal.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'badandboujee.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'baugebags.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'beeglee.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'bersache.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'bewakoof.com' in url_lower:
        return '/p/' in url_lower or '/product/' in url_lower or '/buy' in url_lower
    elif 'blackberrys.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'bummer.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'campussutra.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'chapter2drip.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'chumbak.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'chupps.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'colorcapital.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'mavinclub.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'ecoright.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'gunsnsons.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'buyhautesauce.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'jockey.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'justlilthings.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'klydo.in' in url_lower:
        return '/product/' in url_lower
    elif 'levi.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower or '/in-en/p/' in url_lower
    elif 'maincharacterindia.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'mydesignation.com' in url_lower:
        return '/products/' in url_lower
    elif 'mywishbag.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'nailin.it' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'palmonas.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'buypinacolada.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'in.puma.com' in url_lower or 'puma.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower or '/in/en/' in url_lower
    elif 'shopqissa.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'rapidbox.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'recast.co.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'salty.co.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'sassafras.in' in url_lower:
        return '/products/' in url_lower
    elif 'silisoul.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'stylishop.com' in url_lower or 'styli.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'bearhouse' in url_lower or 'bearcompany' in url_lower or 'thebearhouse' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'tigc.in' in url_lower:
        return '/products/' in url_lower
    elif 'thekurtacompany.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'theater.xyz' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'thelagaadi.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'untung.in' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    elif 'xyxxcrew.com' in url_lower:
        return '/products/' in url_lower or '/product/' in url_lower
    
    # Generic validation: Accept URLs with 3+ meaningful path segments
    path_segments = [s for s in url_lower.split('/') if s and not s.startswith('?')]
    return len(path_segments) >= 3

def search_image_on_serpapi(image_url):
    """
    Search for visually similar products using SerpAPI Google Lens
    PURE IMAGE SEARCH - No text query
    FRESH DATA - No cache
    """
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": API_KEY,
        "country": "in",
        "hl": "en",
        "no_cache": "true"
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API Error: {str(e)}")
        return None

def search_image_with_query_on_serpapi(image_url, query_text):
    """
    Search with Image + Query
    FRESH DATA - No cache
    """
    params = {
        "engine": "google_lens",
        "url": image_url,
        "q": query_text,
        "api_key": API_KEY,
        "country": "in",
        "hl": "en",
        "no_cache": "true"
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API Error: {str(e)}")
        return None

def calculate_match_score(match, product_data):
    """
    Calculate comprehensive match score based on multiple factors:
    - Brand match (30 points)
    - Category match (20 points)
    - Color match (15 points)
    - Price similarity (20 points)
    - Title similarity (15 points)
    Returns score from 0-100
    """
    score = 0
    title = match.get("title", "").lower()
    source = match.get("source", "").lower()
    link = match.get("link", "").lower()
    
    brand = product_data.get('brand', '').lower()
    category = product_data.get('category', '').lower()
    original_title = product_data.get('product_title', '').lower()
    original_price = product_data.get('min_price_rupees', '')
    
    # 1. Brand Match (30 points)
    brand_keywords = brand.replace("-", " ").replace("_", " ").split()
    brand_found = any(keyword in title or keyword in source or keyword in link 
                     for keyword in brand_keywords if len(keyword) > 2)
    if brand_found:
        score += 30
    
    # 2. Category Match (20 points)
    if category:
        category_keywords = category.lower().split()
        category_found = any(keyword in title for keyword in category_keywords if len(keyword) > 3)
        if category_found:
            score += 20
    
    # 3. Color Match (15 points)
    colors = ['black', 'white', 'blue', 'red', 'green', 'yellow', 'pink', 'purple', 
              'orange', 'brown', 'grey', 'gray', 'beige', 'navy', 'olive', 'maroon',
              'silver', 'gold', 'cream', 'khaki', 'tan', 'teal', 'burgundy', 'mint',
              'lavender', 'coral', 'peach', 'mustard', 'charcoal', 'rose']
    
    orig_colors = [c for c in colors if c in original_title]
    found_colors = [c for c in colors if c in title]
    
    if orig_colors and found_colors:
        if any(c in found_colors for c in orig_colors):
            score += 15  # Matching color
    elif not orig_colors:
        score += 10  # No color specified, give partial points
    
    # 4. Price Similarity (20 points) - Lenient ±30% range
    try:
        if original_price:
            orig_price_val = float(str(original_price).replace(',', ''))
            match_price = extract_price_from_match(match)
            
            if match_price and match_price not in ["Price not displayed in listing", "Product not available on site", "Check site for price"]:
                found_price_val = float(str(match_price).replace(',', ''))
                
                # Calculate price difference percentage
                price_diff_pct = abs(orig_price_val - found_price_val) / orig_price_val * 100
                
                # Lenient scoring - ±30% is acceptable
                if price_diff_pct <= 10:
                    score += 20  # Within 10% - perfect match
                elif price_diff_pct <= 30:
                    score += 18  # Within 30% - good match (acceptable range)
                elif price_diff_pct <= 50:
                    score += 12  # Within 50% - moderate match
                elif price_diff_pct <= 100:
                    score += 5   # Within 100% - loose match
    except:
        pass
    
    # 5. Title Keyword Overlap (15 points)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'men', 'women', 'mens', 'womens'}
    
    orig_keywords = set([w for w in re.findall(r'\b\w+\b', original_title) 
                        if w not in stop_words and len(w) > 2])
    found_keywords = set([w for w in re.findall(r'\b\w+\b', title) 
                         if w not in stop_words and len(w) > 2])
    
    if orig_keywords:
        overlap = len(orig_keywords & found_keywords) / len(orig_keywords)
        score += int(overlap * 15)
    
    return min(100, score)

def extract_product_info(visual_matches, product_data, allowed_sites):
    """
    Extract product URLs with COMPREHENSIVE MULTI-FACTOR SCORING
    Uses 5-factor scoring: Brand (30%) + Category (20%) + Color (15%) + Price (20%) + Title (15%)
    Minimum score: 30/100 to accept matches
    """
    results = {}
    for site_key in allowed_sites:
        results[site_key] = {
            "url": "Not Found",
            "price": "Product not available on site",
        }
    
    if not visual_matches:
        return results, 0, 0
    
    brand_matches = 0
    rejected = 0
    
    # Process each match and collect candidates
    candidates = {site_key: [] for site_key in allowed_sites}
    
    for idx, match in enumerate(visual_matches, 1):
        link = match.get("link", "")
        match_title = match.get("title", "")
        
        if not link:
            continue
        
        site_key = identify_site(link)
        if not site_key or site_key not in allowed_sites:
            continue
        
        # STRICT URL validation
        if not is_valid_product_url(link):
            continue
        
        # Calculate comprehensive match score (0-100)
        match_score = calculate_match_score(match, product_data)
        
        # Accept matches with score >= 30 (at least brand match OR good overall similarity)
        if match_score < 30:
            rejected += 1
            continue
        
        # Extract price
        price = extract_price_from_match(match)
        
        # Add to candidates
        candidates[site_key].append({
            "url": link,
            "price": price,
            "score": match_score,
            "visual_rank": idx,
            "title": match_title
        })
    
    # Select best candidate for each site (highest score)
    for site_key in allowed_sites:
        if candidates[site_key]:
            # Sort by score (highest first)
            best_match = max(candidates[site_key], key=lambda x: x['score'])
            
            results[site_key] = {
                "url": best_match["url"],
                "price": best_match["price"]
            }
            
            brand_matches += 1
            
            # Display result
            site_display = site_key.upper().replace("_", " ")
            score = best_match["score"]
            price_display = f"₹{best_match['price']}" if best_match["price"] not in ["Price not displayed in listing", "Product not available on site", "Check site for price"] else "Check site"
            
            print(f"      ✓ {site_display}: Match {score:.0f}% | Price: {price_display}")
    
    return results, brand_matches, rejected

def process_single_product(product, product_idx, total_products):
    """
    Process a single product with TRIPLE-API-CALL strategy for maximum accuracy
    Makes 3 separate API calls (Myntra, Slikk, Brand) with local filtering
    Returns: dict with site_results
    """
    print(f"\n[{product_idx}/{total_products}] {product['product_title'][:60]}... ({product['brand']})")
    
    if not product['image']:
        print("  ⚠ No image URL - Skipping")
        return {'product': product, 'site_results': {}, 'brand_site': None}
    
    # Determine which sites to search for this product
    brand_site = get_brand_site(product['brand'])
    allowed_sites = PRIMARY_SITES.copy()
    if brand_site:
        allowed_sites.append(brand_site)
    
    print(f"  🔍 3 Targeted searches: {', '.join([s.upper() for s in allowed_sites])}")
    
    # Initialize combined results
    all_visual_matches = []
    
    # === API CALL 1: MYNTRA ===
    print(f"  🔍 [1/3] Myntra: Image + '{product['brand']} site:myntra.com'")
    search_myntra = search_image_with_query_on_serpapi(
        product['image'], 
        f"{product['brand']} site:myntra.com"
    )
    if search_myntra:
        myntra_matches = search_myntra.get("visual_matches", [])
        all_visual_matches.extend(myntra_matches)
        print(f"      → {len(myntra_matches)} results")
    else:
        print(f"      → No results")
    
    time.sleep(0.5)  # Small delay between API calls
    
    # === API CALL 2: SLIKK ===
    print(f"  🔍 [2/3] Slikk: Image + '{product['brand']} site:slikk.club'")
    search_slikk = search_image_with_query_on_serpapi(
        product['image'], 
        f"{product['brand']} site:slikk.club"
    )
    if search_slikk:
        slikk_matches = search_slikk.get("visual_matches", [])
        all_visual_matches.extend(slikk_matches)
        print(f"      → {len(slikk_matches)} results")
    else:
        print(f"      → No results")
    
    time.sleep(0.5)  # Small delay between API calls
    
    # === API CALL 3: BRAND SITE (if exists) ===
    if brand_site:
        # Get brand domain for site targeting
        brand_domains = SHOPPING_SITES.get(brand_site, [])
        if brand_domains:
            brand_domain = brand_domains[0]
            print(f"  🔍 [3/3] {brand_site.upper()}: Image + '{product['brand']} site:{brand_domain}'")
            search_brand = search_image_with_query_on_serpapi(
                product['image'], 
                f"{product['brand']} site:{brand_domain}"
            )
            if search_brand:
                brand_matches = search_brand.get("visual_matches", [])
                all_visual_matches.extend(brand_matches)
                print(f"      → {len(brand_matches)} results")
            else:
                print(f"      → No results")
    
    # === LOCAL FILTERING: Apply comprehensive scoring to ALL results ===
    print(f"  🔬 Local filtering: {len(all_visual_matches)} total results")
    
    if not all_visual_matches:
        print("  ⚠ No results from any API call")
        return {'product': product, 'site_results': {}, 'brand_site': brand_site}
    
    # Extract with comprehensive multi-factor scoring
    site_results, brand_matches, rejected = extract_product_info(
        all_visual_matches, 
        product,  # Pass entire product data for comprehensive scoring
        allowed_sites
    )
    
    sites_found = sum(1 for site_data in site_results.values() if site_data["url"] != "Not Found")
    print(f"  💾 Found on {sites_found}/{len(allowed_sites)} site(s) | Rejected: {rejected}")
    
    return {'product': product, 'site_results': site_results, 'brand_site': brand_site}

def process_products(input_csv, output_csv):
    """
    MULTI-BRAND PROCESSING with GENERIC OUTPUT SCHEMA
    - Handles multiple brands in a single CSV
    - Outputs generic columns: brand_price, brand_url (instead of brand-specific names)
    - Maintains myntra and slikk columns as-is
    """
    # Read input CSV
    products = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                'style_id': row.get('style_id', ''),
                'brand': row.get('brand', ''),
                'product_title': row.get('product_title', ''),
                'gender': row.get('gender', ''),
                'category': row.get('category', ''),
                'min_price_rupees': row.get('min_price_rupees', ''),
                'image': row.get('first_image_url', '')
            })
    
    # Get unique brands
    unique_brands = list(set(p['brand'] for p in products))
    
    print(f"\n{'='*80}")
    print(f"🔍 MULTI-BRAND PRODUCT SEARCH v7.0 - MAXIMUM ACCURACY")
    print(f"{'='*80}")
    print(f"Input: {input_csv} → Output: {output_csv}")
    print(f"✅ 3 Targeted API calls per product:")
    print(f"   • Myntra: Image + 'brand site:myntra.com'")
    print(f"   • Slikk: Image + 'brand site:slikk.club'")
    print(f"   • Brand: Image + 'brand site:brandsite.com'")
    print(f"✅ Local filtering: Brand (30%) + Category (20%) + Color (15%) + Price (20%) + Title (15%)")
    print(f"✅ Minimum threshold: 30/100 | Price range: ±30%")
    print(f"✅ Generic output schema: brand_price, brand_url")
    print(f"{'='*80}")
    print(f"\n📦 Processing {len(products)} products from {len(unique_brands)} brand(s):")
    for brand in sorted(unique_brands):
        count = sum(1 for p in products if p['brand'] == brand)
        print(f"   • {brand}: {count} product(s)")
    print()
    
    # Fixed output schema with generic brand columns
    fieldnames = [
        'style_id', 'brand', 'product_title', 'gender', 'category',
        'klydo_price', 'myntra_price', 'slikk_price', 'brand_price',
        'klydo_url', 'myntra_url', 'slikk_url', 'brand_url'
    ]
    
    all_results = []
    
    print(f"{'='*80}")
    print("PROCESSING PRODUCTS")
    print(f"{'='*80}")
    
    # Process each product individually
    for idx, product in enumerate(products, 1):
        result = process_single_product(product, idx, len(products))
        all_results.append(result)
        
        # Rate limiting between products
        if idx < len(products):
            time.sleep(1)
    
    # WRITE RESULTS
    print(f"\n{'='*80}")
    print("WRITING RESULTS")
    print(f"{'='*80}\n")
    
    with open(output_csv, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for result_entry in all_results:
            product = result_entry['product']
            site_results = result_entry['site_results']
            brand_site = result_entry['brand_site']
            
            # Extract prices and URLs
            myntra_data = site_results.get('myntra', {"url": "Not Found", "price": "Product not available on site"})
            slikk_data = site_results.get('slikk', {"url": "Not Found", "price": "Product not available on site"})
            
            # Get brand site data (if exists)
            if brand_site:
                brand_data = site_results.get(brand_site, {"url": "Not Found", "price": "Product not available on site"})
            else:
                brand_data = {"url": "Not Found", "price": "Product not available on site"}
            
            row_data = {
                'style_id': product['style_id'],
                'brand': product['brand'],
                'product_title': product['product_title'],
                'gender': product['gender'],
                'category': product['category'],
                'klydo_price': product['min_price_rupees'],
                'myntra_price': myntra_data['price'],
                'slikk_price': slikk_data['price'],
                'brand_price': brand_data['price'],
                'klydo_url': f"https://klydo.in/product/{product['style_id']}",
                'myntra_url': myntra_data['url'],
                'slikk_url': slikk_data['url'],
                'brand_url': brand_data['url']
            }
            
            writer.writerow(row_data)
    
    # Final coverage report
    print(f"\n✅ Processed {len(products)} products")
    print(f"\n{'='*80}")
    print("COVERAGE SUMMARY")
    print(f"{'='*80}")
    
    myntra_count = sum(1 for r in all_results if r['site_results'].get('myntra', {}).get('url') != "Not Found")
    slikk_count = sum(1 for r in all_results if r['site_results'].get('slikk', {}).get('url') != "Not Found")
    
    # Count brand site coverage (each product may have different brand site)
    brand_count = 0
    for r in all_results:
        brand_site = r['brand_site']
        if brand_site and r['site_results'].get(brand_site, {}).get('url') != "Not Found":
            brand_count += 1
    
    myntra_pct = (myntra_count / len(products) * 100) if products else 0
    slikk_pct = (slikk_count / len(products) * 100) if products else 0
    brand_pct = (brand_count / len(products) * 100) if products else 0
    
    myntra_status = "✅" if myntra_pct >= 50 else "⚠️"
    slikk_status = "✅" if slikk_pct >= 50 else "⚠️"
    brand_status = "✅" if brand_pct >= 50 else "⚠️"
    
    print(f"{myntra_status} MYNTRA: {myntra_count}/{len(products)} ({myntra_pct:.0f}%)")
    print(f"{slikk_status} SLIKK: {slikk_count}/{len(products)} ({slikk_pct:.0f}%)")
    print(f"{brand_status} BRAND SITES: {brand_count}/{len(products)} ({brand_pct:.0f}%)")
    
    print(f"\n✅ Output saved: {output_csv}")
    print("📄 Schema: style_id, brand, ..., myntra_price, slikk_price, brand_price, myntra_url, slikk_url, brand_url")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    INPUT_FILE = "sample.csv"
    OUTPUT_FILE = "mar.csv"
    
    process_products(INPUT_FILE, OUTPUT_FILE)
    
    print("\n✅ ALL DONE!")
    print(f"📄 Check: {OUTPUT_FILE}")
#taylor se thoda advance sassafras mapping h isme multiple brand support bhi 