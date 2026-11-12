import asyncio
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path
from typing import Any, Dict, List


# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import bcrypt
from config import settings
from database import get_sync_session_factory, init_db
from models.db_models import Rating, Restaurant, User
from sqlalchemy import delete, func, select

def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

# -------------------------------------------------------------------------
# 1. 84 HARDCODED REAL-WORLD RESTAURANTS ACROSS 7 INDIAN CITIES
# -------------------------------------------------------------------------
HARDCODED_RESTAURANTS = [
    # --- DELHI ---
    {
        "name": "Bukhara",
        "cuisine": ["North Indian", "Mughlai"],
        "price_range": "Fine Dining",
        "avg_rating": 4.8,
        "location": {"area": "Chanakyapuri, Delhi", "lat": 28.5976, "lng": 77.1738},
        "ambience": "Fine Dining",
        "tags": ["Iconic", "Dal Bukhara", "Tandoor", "Valet Parking", "Luxury"],
        "description": "Legendary culinary icon world-famous for its slow-cooked Dal Bukhara and rustic tandoori meats.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Karim's",
        "cuisine": ["Mughlai", "North Indian", "Biryani"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Jama Masjid, Old Delhi", "lat": 28.6506, "lng": 77.2334},
        "ambience": "Casual",
        "tags": ["Heritage", "Spicy", "Mutton Korma", "Late Night", "Historic"],
        "description": "Centuries-old royal Mughlai fare served near the historic Jama Masjid in the heart of Old Delhi.",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500",
    },
    {
        "name": "Indian Accent",
        "cuisine": ["North Indian", "Continental"],
        "price_range": "Fine Dining",
        "avg_rating": 4.9,
        "location": {"area": "Lodhi Road, Delhi", "lat": 28.5916, "lng": 77.2393},
        "ambience": "Romantic",
        "tags": ["Michelin-Caliber", "Tasting Menu", "Wine Pairing", "Gourmet", "Luxury"],
        "description": "Progressive Indian tasting menus elevating traditional dishes with global culinary artistry.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Gulati",
        "cuisine": ["North Indian", "Biryani"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Pandara Road, Delhi", "lat": 28.6053, "lng": 77.2341},
        "ambience": "Family",
        "tags": ["Butter Chicken", "Midnight Dining", "Family-Friendly", "Rich Curries"],
        "description": "Beloved Pandara Road destination celebrated for rich butter chicken and luscious dal makhani.",
        "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500",
    },
    {
        "name": "Saravana Bhavan CP",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.3,
        "location": {"area": "Connaught Place, Delhi", "lat": 28.6328, "lng": 77.2195},
        "ambience": "Casual",
        "tags": ["Vegetarian", "Crispy Dosa", "Filter Coffee", "Budget-Friendly"],
        "description": "Authentic Tamil vegetarian comfort food serving crispy dosas, fluffy idlis, and piping hot filter coffee.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "The Big Chill Cafe",
        "cuisine": ["Italian", "Continental", "Cafe"],
        "price_range": "Moderate",
        "avg_rating": 4.7,
        "location": {"area": "Khan Market, Delhi", "lat": 28.6003, "lng": 77.2270},
        "ambience": "Trendy",
        "tags": ["Pasta", "Cheesecake", "Retro Cinema", "Milkshakes", "Outdoor Seating"],
        "description": "Retro Hollywood poster-lined trattoria famous for penne vodka, rich baked pasta, and decadent mud pies.",
        "image_url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=500",
    },
    {
        "name": "Smoke House Deli Hauz Khas",
        "cuisine": ["Continental", "Italian", "Cafe"],
        "price_range": "Premium",
        "avg_rating": 4.4,
        "location": {"area": "Hauz Khas, Delhi", "lat": 28.5494, "lng": 77.2001},
        "ambience": "Trendy",
        "tags": ["Hand-Drawn Walls", "Artisan Burgers", "Craft Cocktails", "Brunch"],
        "description": "Whimsical monochrome illustration decor paired with European comfort dishes and all-day breakfast.",
        "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500",
    },
    {
        "name": "Diggin",
        "cuisine": ["Italian", "Cafe", "Pizza"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Anand Lok, Delhi", "lat": 28.5583, "lng": 77.2185},
        "ambience": "Romantic",
        "tags": ["Fairy Lights", "Brick Oven Pizza", "Garden Dining", "Aesthetic"],
        "description": "Lush ivy-covered romantic cafe with rustic brick architecture, wood-fired pizzas, and ravioli.",
        "image_url": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=500",
    },
    {
        "name": "Farzi Cafe Connaught Place",
        "cuisine": ["North Indian", "Continental"],
        "price_range": "Premium",
        "avg_rating": 4.5,
        "location": {"area": "Connaught Place, Delhi", "lat": 28.6331, "lng": 77.2189},
        "ambience": "Trendy",
        "tags": ["Molecular Gastronomy", "Fusion", "Live Music", "Cocktails"],
        "description": "High-energy bistro revolutionizing Indian gastronomy with playful molecular illusions and vibrant beats.",
        "image_url": "https://images.unsplash.com/photo-1578474846511-04ba529f0b88?w=500",
    },
    {
        "name": "Olive Bar & Kitchen Mehrauli",
        "cuisine": ["Italian", "Continental"],
        "price_range": "Fine Dining",
        "avg_rating": 4.7,
        "location": {"area": "Mehrauli, Delhi", "lat": 28.5244, "lng": 77.1855},
        "ambience": "Rooftop",
        "tags": ["Qutub View", "Sunlit Courtyard", "Gourmet Pizza", "Fine Wine"],
        "description": "Serene white-walled Mediterranean haven nestled under the gaze of the majestic Qutub Minar.",
        "image_url": "https://images.unsplash.com/photo-1525610553991-2bede1a236e2?w=500",
    },
    {
        "name": "Moti Mahal Delux",
        "cuisine": ["North Indian", "Mughlai"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Daryaganj, Delhi", "lat": 28.6473, "lng": 77.2415},
        "ambience": "Family",
        "tags": ["Original Butter Chicken", "Tandoori Chicken", "Historic"],
        "description": "The historic birthplace of Tandoori Chicken and creamy butter chicken sauce created in 1947.",
        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500",
    },
    {
        "name": "Andrea's Bar & Brasserie",
        "cuisine": ["Continental", "Italian", "Thai"],
        "price_range": "Premium",
        "avg_rating": 4.5,
        "location": {"area": "Saket, Delhi", "lat": 28.5284, "lng": 77.2190},
        "ambience": "Casual",
        "tags": ["Artisan Pasta", "Dim Sum", "European Vibe", "Cocktails"],
        "description": "Sophisticated global brasserie bringing cosmopolitan flavors from Rome, Bangkok, and Paris.",
        "image_url": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=500",
    },

    # --- MUMBAI ---
    {
        "name": "Britannia & Co.",
        "cuisine": ["Continental", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Ballard Estate, Mumbai", "lat": 18.9348, "lng": 72.8407},
        "ambience": "Casual",
        "tags": ["Parsi Berry Pulao", "Vintage Clock", "Caramel Custard", "Heritage"],
        "description": "Iconic vintage colonial restaurant serving legendary Iranian Berry Pulao and Sali Boti since 1923.",
        "image_url": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=500",
    },
    {
        "name": "Leopold Cafe",
        "cuisine": ["Continental", "Fast Food", "Chinese"],
        "price_range": "Moderate",
        "avg_rating": 4.3,
        "location": {"area": "Colaba Causeway, Mumbai", "lat": 18.9229, "lng": 72.8317},
        "ambience": "Casual",
        "tags": ["Historic", "Chilled Beer", "Shantaram", "Bustling"],
        "description": "Historic 1871 Colaba institution known for bustling traveler energy, draught beer, and beef chilli.",
        "image_url": "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?w=500",
    },
    {
        "name": "Trishna",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Premium",
        "avg_rating": 4.7,
        "location": {"area": "Fort, Mumbai", "lat": 18.9287, "lng": 72.8335},
        "ambience": "Family",
        "tags": ["Butter Garlic Crab", "Mangalorean Seafood", "Neer Dosa", "Iconic"],
        "description": "World-famous seafood institution celebrated for legendary Jumbo Butter Garlic Crab and squid koliwada.",
        "image_url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=500",
    },
    {
        "name": "The Bombay Canteen",
        "cuisine": ["North Indian", "South Indian", "Continental"],
        "price_range": "Premium",
        "avg_rating": 4.8,
        "location": {"area": "Lower Parel, Mumbai", "lat": 18.9953, "lng": 72.8258},
        "ambience": "Trendy",
        "tags": ["Regional Ingredients", "Craft Cocktails", "Artisanal", "Lively"],
        "description": "Contemporary celebration of India's diverse regional culinary heritage with spirited craft cocktails.",
        "image_url": "https://images.unsplash.com/photo-1543007630-9710e4a00a20?w=500",
    },
    {
        "name": "Gajalee",
        "cuisine": ["South Indian", "North Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Vile Parle East, Mumbai", "lat": 19.1026, "lng": 72.8488},
        "ambience": "Family",
        "tags": ["Bombil Fry", "Tandoori Crab", "Solkadhi", "Malvani"],
        "description": "Coastal Maharashtrian paradise famous for crispy Bombil fry, clams masala, and refreshing Solkadhi.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Bastian Bandra",
        "cuisine": ["Continental", "Thai"],
        "price_range": "Fine Dining",
        "avg_rating": 4.6,
        "location": {"area": "Bandra West, Mumbai", "lat": 19.0620, "lng": 72.8332},
        "ambience": "Trendy",
        "tags": ["Celebrity Spot", "Seafood Boil", "Cheesecakes", "Vibrant"],
        "description": "Bustling upscale celebrity magnet boasting hearty seafood platters, lobster rolls, and monster cheesecakes.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Pizza By The Bay",
        "cuisine": ["Pizza", "Italian"],
        "price_range": "Premium",
        "avg_rating": 4.4,
        "location": {"area": "Marine Drive, Mumbai", "lat": 18.9333, "lng": 72.8242},
        "ambience": "Romantic",
        "tags": ["Sea View", "Artisan Crust", "Outdoor Seating", "Sunset"],
        "description": "Front-row seats to the Queen's Necklace paired with gourmet thin-crust pizza and sea breeze.",
        "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500",
    },
    {
        "name": "Mahesh Lunch Home",
        "cuisine": ["South Indian", "North Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Fort, Mumbai", "lat": 18.9340, "lng": 72.8358},
        "ambience": "Casual",
        "tags": ["Mangalorean Curry", "Prawn Ghee Roast", "Surmai Fry"],
        "description": "Authentic coastal dining serving rich Mangalorean surmai, crab sukka, and appams since 1977.",
        "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500",
    },
    {
        "name": "Kyani & Co.",
        "cuisine": ["Cafe", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.2,
        "location": {"area": "Marine Lines, Mumbai", "lat": 18.9429, "lng": 72.8277},
        "ambience": "Casual",
        "tags": ["Irani Chai", "Bun Maska", "Keema Pav", "Heritage"],
        "description": "Mumbai's oldest Irani cafe operating since 1904, renowned for bun maska, mawa cakes, and spicy keema.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Bayroute Juhu",
        "cuisine": ["Continental", "Cafe"],
        "price_range": "Fine Dining",
        "avg_rating": 4.7,
        "location": {"area": "Juhu, Mumbai", "lat": 19.0988, "lng": 72.8264},
        "ambience": "Romantic",
        "tags": ["Middle Eastern", "Hummus Platter", "Baklava", "Opulent"],
        "description": "Opulent Middle Eastern sanctuary bringing authentic Egyptian, Lebanese, and Turkish gourmet recipes.",
        "image_url": "https://images.unsplash.com/photo-1541518763669-27fef04b14ea?w=500",
    },
    {
        "name": "Pa Pa Ya Palladium",
        "cuisine": ["Sushi", "Thai", "Chinese"],
        "price_range": "Premium",
        "avg_rating": 4.6,
        "location": {"area": "Lower Parel, Mumbai", "lat": 18.9950, "lng": 72.8252},
        "ambience": "Trendy",
        "tags": ["Sashimi", "Dim Sum Matrix", "Liquid Nitrogen", "Rooftop Vibe"],
        "description": "High-energy Asian bistro serving avant-garde sushi towers, dim sums, and sensory craft cocktails.",
        "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500",
    },
    {
        "name": "Cafe Mondegar",
        "cuisine": ["Continental", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.3,
        "location": {"area": "Colaba, Mumbai", "lat": 18.9246, "lng": 72.8322},
        "ambience": "Casual",
        "tags": ["Mario Miranda Murals", "Jukebox", "Cold Beer", "Historic"],
        "description": "Lively heritage cafe adorned with Mario Miranda cartoon murals, a vintage jukebox, and chilly draft mugs.",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500",
    },

    # --- BANGALORE ---
    {
        "name": "Vidyarthi Bhavan",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.6,
        "location": {"area": "Basavanagudi, Bangalore", "lat": 12.9432, "lng": 77.5702},
        "ambience": "Casual",
        "tags": ["Crispy Benne Dosa", "Filter Coffee", "Heritage", "Nostalgic"],
        "description": "Historic eatery serving thick, golden-crisp Benne Masala Dosas with coconut chutney since 1943.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "CTR - Shri Sagar",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.7,
        "location": {"area": "Malleshwaram, Bangalore", "lat": 13.0031, "lng": 77.5709},
        "ambience": "Casual",
        "tags": ["Benne Dosa", "Poori Saggu", "Filter Coffee", "Quick Service"],
        "description": "Malleshwaram's crown jewel celebrated for melt-in-the-mouth butter dosas and spicy potato fillings.",
        "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500",
    },
    {
        "name": "Toit Brewpub",
        "cuisine": ["Continental", "Pizza", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.8,
        "location": {"area": "Indiranagar, Bangalore", "lat": 12.9784, "lng": 77.6408},
        "ambience": "Trendy",
        "tags": ["Microbrewery", "Craft Beer", "Wood-Fired Pizza", "Pet-Friendly", "Live Music"],
        "description": "The heart of Bengaluru craft beer culture serving signature Basmati Blonde, Tint-in-Toit, and artisan pies.",
        "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500",
    },
    {
        "name": "Mavalli Tiffin Room (MTR)",
        "cuisine": ["South Indian"],
        "price_range": "Budget",
        "avg_rating": 4.6,
        "location": {"area": "Lalbagh Road, Bangalore", "lat": 12.9554, "lng": 77.5857},
        "ambience": "Family",
        "tags": ["Rava Idli Inventor", "Pure Ghee", "Traditional Thali", "Historic"],
        "description": "Timeless institution near Lalbagh Gardens that invented the Rava Idli during World War II shortages.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "Truffles Koramangala",
        "cuisine": ["Continental", "Fast Food", "Cafe"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "Koramangala, Bangalore", "lat": 12.9345, "lng": 77.6200},
        "ambience": "Casual",
        "tags": ["All-American Burgers", "Steak", "Ferrero Milkshake", "Student Favorite"],
        "description": "Bengaluru youth favorite offering succulent handcrafted burgers, potato wedges, and pasta bowls.",
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500",
    },
    {
        "name": "The Only Place",
        "cuisine": ["Continental", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Museum Road, Bangalore", "lat": 12.9722, "lng": 77.6044},
        "ambience": "Casual",
        "tags": ["Steaks", "Apple Pie", "Garden Courtyard", "Heritage"],
        "description": "Old-world steakhouse nestled in a garden patio serving sizzling cuts and homemade hot apple pie.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Nagarjuna Residency Road",
        "cuisine": ["South Indian", "Biryani"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Residency Road, Bangalore", "lat": 12.9728, "lng": 77.6074},
        "ambience": "Family",
        "tags": ["Andhra Meals", "Spicy Chilli Chicken", "Guntur Biryani", "Banana Leaf"],
        "description": "Fiery Andhra feasts served on banana leaves with unlimited gunpowder podi, spicy curries, and biryani.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Windmills Craftworks",
        "cuisine": ["Continental", "North Indian"],
        "price_range": "Fine Dining",
        "avg_rating": 4.8,
        "location": {"area": "Whitefield, Bangalore", "lat": 12.9822, "lng": 77.7289},
        "ambience": "Romantic",
        "tags": ["Jazz Lounge", "Library", "Microbrewery", "Stout", "Luxury"],
        "description": "Exquisite microbrewery, live jazz performance space, and rare book library offering world-class ales.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Arbor Brewing Company",
        "cuisine": ["Continental", "Pizza", "Fast Food"],
        "price_range": "Premium",
        "avg_rating": 4.6,
        "location": {"area": "Magrath Road, Bangalore", "lat": 12.9719, "lng": 77.6094},
        "ambience": "Trendy",
        "tags": ["Craft Beer", "Bangalore Bliss", "Nachos", "Outdoor Seating"],
        "description": "Pioneering American craft beer taproom famous for its Bangalore Bliss hefeweizen and loaded platters.",
        "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500",
    },
    {
        "name": "Olive Beach",
        "cuisine": ["Italian", "Continental"],
        "price_range": "Fine Dining",
        "avg_rating": 4.7,
        "location": {"area": "Ashok Nagar, Bangalore", "lat": 12.9698, "lng": 77.6062},
        "ambience": "Romantic",
        "tags": ["White Villa", "Mediterranean", "Candlelight", "Wine List"],
        "description": "Restored Mediterranean villa offering exquisite culinary voyages through Provence and Tuscany.",
        "image_url": "https://images.unsplash.com/photo-1525610553991-2bede1a236e2?w=500",
    },
    {
        "name": "Meghana Foods Koramangala",
        "cuisine": ["Biryani", "North Indian", "South Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Koramangala, Bangalore", "lat": 12.9348, "lng": 77.6189},
        "ambience": "Casual",
        "tags": ["Spicy Boneless Biryani", "Andhra Style", "Quick Bite"],
        "description": "The quintessential Bengaluru spicy biryani benchmark boasting fragrant basmati and tender marinated chicken.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Glen's Bakehouse Lavelle Road",
        "cuisine": ["Cafe", "Continental", "Pizza"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Lavelle Road, Bangalore", "lat": 12.9702, "lng": 77.5998},
        "ambience": "Trendy",
        "tags": ["Red Velvet Cupcakes", "Sourdough Pizza", "Garden Cafe"],
        "description": "Charming colonial house bakery famous for mini red velvet cupcakes, sourdough pizzas, and hot coffee.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },

    # --- HYDERABAD ---
    {
        "name": "Paradise Secunderabad",
        "cuisine": ["Biryani", "Mughlai", "North Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Secunderabad, Hyderabad", "lat": 17.4411, "lng": 78.4870},
        "ambience": "Family",
        "tags": ["Dum Biryani", "Mirchi Ka Salan", "Iconic 1953", "Large Seating"],
        "description": "Hyderabad's most historic biryani destination serving fragrant Hyderabadi Dum Biryani since 1953.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Bawarchi RTC X Roads",
        "cuisine": ["Biryani", "North Indian", "Mughlai"],
        "price_range": "Budget",
        "avg_rating": 4.6,
        "location": {"area": "RTC X Roads, Hyderabad", "lat": 17.4024, "lng": 78.4975},
        "ambience": "Casual",
        "tags": ["Original Bawarchi", "Mutton Biryani", "Boti Kebab", "Crowded"],
        "description": "The legendary single original Bawarchi famous for intensely spiced mutton dum biryani and juicy kebabs.",
        "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500",
    },
    {
        "name": "Cafe Bahar",
        "cuisine": ["Biryani", "Mughlai"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "Basheerbagh, Hyderabad", "lat": 17.3995, "lng": 78.4832},
        "ambience": "Casual",
        "tags": ["Special Hyderabadi Biryani", "Haleem", "Irani Chai", "Osmania Biscuit"],
        "description": "Beloved local powerhouse serving rich saffron-laced biryani, seasonal mutton haleem, and Irani chai.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Shah Ghouse Tolichowki",
        "cuisine": ["Biryani", "Mughlai"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "Tolichowki, Hyderabad", "lat": 17.3970, "lng": 78.4110},
        "ambience": "Casual",
        "tags": ["Midnight Biryani", "Bheja Fry", "Tangdi Kebab", "Authentic"],
        "description": "High-octane late-night haven famed for authentic aromatic biryani, grilled kebabs, and rich gravies.",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500",
    },
    {
        "name": "Chutneys Banjara Hills",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.3,
        "location": {"area": "Banjara Hills, Hyderabad", "lat": 17.4239, "lng": 78.4482},
        "ambience": "Family",
        "tags": ["Steam Dosa", "Six Chutneys", "Guntur Idli", "Vegetarian"],
        "description": "Famous for ultra-soft Babai Steam Dosas served alongside a signature palette of six distinct chutneys.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "Tatva Jubilee Hills",
        "cuisine": ["Continental", "Italian", "North Indian"],
        "price_range": "Fine Dining",
        "avg_rating": 4.7,
        "location": {"area": "Jubilee Hills, Hyderabad", "lat": 17.4319, "lng": 78.4073},
        "ambience": "Fine Dining",
        "tags": ["Pure Vegetarian Gourmet", "Truffle Risotto", "Opulent Interior"],
        "description": "Sophisticated pure-vegetarian fine dining destination transforming European and Indian classics.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Olive Bistro Durgam Cheruvu",
        "cuisine": ["Italian", "Continental"],
        "price_range": "Fine Dining",
        "avg_rating": 4.6,
        "location": {"area": "Jubilee Hills, Hyderabad", "lat": 17.4326, "lng": 78.3846},
        "ambience": "Rooftop",
        "tags": ["Secret Lake View", "White Stone Courtyard", "Woodfired Pizza", "Wine"],
        "description": "Picturesque Grecian retreat perched on a cliff overlooking Durgam Cheruvu Secret Lake.",
        "image_url": "https://images.unsplash.com/photo-1525610553991-2bede1a236e2?w=500",
    },
    {
        "name": "Autumn Leaf Cafe",
        "cuisine": ["Cafe", "Continental"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Jubilee Hills, Hyderabad", "lat": 17.4281, "lng": 78.4069},
        "ambience": "Romantic",
        "tags": ["Vintage Villa Garden", "Pet-Friendly", "Smoothie Bowls", "Coffee"],
        "description": "Quiet leafy villa cafe with sprawling outdoor seating, artisan breakfast platters, and specialty coffee.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Rayalaseema Ruchulu",
        "cuisine": ["South Indian", "Biryani"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Hitec City, Hyderabad", "lat": 17.4483, "lng": 78.3741},
        "ambience": "Family",
        "tags": ["Ragi Sangati", "Natu Kodi Pulusu", "Fiery Andhra"],
        "description": "Authentic Rayalaseema culinary sanctuary featuring country chicken curry and soft ragi balls.",
        "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500",
    },
    {
        "name": "Feast Sheraton Gachibowli",
        "cuisine": ["Continental", "North Indian", "Italian"],
        "price_range": "Fine Dining",
        "avg_rating": 4.6,
        "location": {"area": "Gachibowli, Hyderabad", "lat": 17.4385, "lng": 78.3582},
        "ambience": "Fine Dining",
        "tags": ["Luxury Buffet", "Live Counters", "Sunday Brunch", "Cocktails"],
        "description": "Expansive five-star buffet showcasing international live cooking stations and artisanal patisserie.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Ulavacharu Jubilee Hills",
        "cuisine": ["South Indian", "Biryani"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Jubilee Hills, Hyderabad", "lat": 17.4334, "lng": 78.4042},
        "ambience": "Family",
        "tags": ["Horsegram Soup", "Ulavacharu Biryani", "Kodi Vepudu"],
        "description": "Celebrated for the famed Andhra delicacy of horse gram soup reduction tossed with aromatic basmati biryani.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Haiku Banjara Hills",
        "cuisine": ["Sushi", "Thai", "Chinese"],
        "price_range": "Premium",
        "avg_rating": 4.7,
        "location": {"area": "Banjara Hills, Hyderabad", "lat": 17.4165, "lng": 78.4412},
        "ambience": "Trendy",
        "tags": ["Pan Asian", "Dragon Rolls", "Pad Thai", "Minimalist"],
        "description": "Sleek Pan-Asian gem serving authentic Japanese sushi, delicate bao buns, and Thai street curries.",
        "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500",
    },

    # --- CHENNAI ---
    {
        "name": "Murugan Idli Shop T. Nagar",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "T. Nagar, Chennai", "lat": 13.0418, "lng": 80.2341},
        "ambience": "Casual",
        "tags": ["Mallipoo Idli", "Podi Dosa", "Four Chutneys", "Filter Coffee"],
        "description": "Cult classic Chennai joint renowned for melt-in-mouth jasmine idlis coated with ghee and spicy podi.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "Annalakshmi Restaurant",
        "cuisine": ["South Indian"],
        "price_range": "Premium",
        "avg_rating": 4.7,
        "location": {"area": "Egmore, Chennai", "lat": 13.0732, "lng": 80.2609},
        "ambience": "Family",
        "tags": ["Temple Architecture", "Sattvic Thali", "Pure Vegetarian", "Spiritual"],
        "description": "Temple-inspired vegetarian sanctuary where food is served as culinary worship in majestic bronze ware.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Buhari Hotel Anna Salai",
        "cuisine": ["Biryani", "Mughlai", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.3,
        "location": {"area": "Anna Salai, Chennai", "lat": 13.0612, "lng": 80.2644},
        "ambience": "Casual",
        "tags": ["Chicken 65 Originator", "Madras Biryani", "Historic 1951"],
        "description": "Historic Chennai institution celebrated as the original birthplace of the world-famous Chicken 65.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Dakshin Crowne Plaza",
        "cuisine": ["South Indian"],
        "price_range": "Fine Dining",
        "avg_rating": 4.8,
        "location": {"area": "Alwarpet, Chennai", "lat": 13.0336, "lng": 80.2520},
        "ambience": "Fine Dining",
        "tags": ["Carnatic Music", "Five Southern States", "Silver Plate", "Luxury"],
        "description": "Pinnacle of South Indian culinary refinement accompanied by soulful live Carnatic flute and veena.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Sangeetha Veg Mylapore",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.4,
        "location": {"area": "Mylapore, Chennai", "lat": 13.0339, "lng": 80.2690},
        "ambience": "Casual",
        "tags": ["Quick Tiffin", "Ghee Roast", "Kapaleeshwarar Temple Nearby", "Budget"],
        "description": "Bustling temple-town breakfast haven serving golden ghee roast dosas and fragrant South Indian filter coffee.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "The Flying Elephant",
        "cuisine": ["Continental", "Italian", "Thai"],
        "price_range": "Fine Dining",
        "avg_rating": 4.7,
        "location": {"area": "Guindy, Chennai", "lat": 13.0102, "lng": 80.2206},
        "ambience": "Trendy",
        "tags": ["Multi-Level Dining", "Theater Kitchens", "DJ Music", "Luxury Bar"],
        "description": "Spectacular multi-level culinary theater inside Park Hyatt featuring dynamic open show kitchens.",
        "image_url": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=500",
    },
    {
        "name": "Dindigul Thalappakatti Nungambakkam",
        "cuisine": ["Biryani", "South Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.3,
        "location": {"area": "Nungambakkam, Chennai", "lat": 13.0604, "lng": 80.2425},
        "ambience": "Family",
        "tags": ["Seeraga Samba Rice", "Turban Heritage", "Mutton Chukka", "Spicy"],
        "description": "Traditional Tamil Nadu biryani made with tiny aromatic Seeraga Samba rice and tender farm mutton.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Shiraz Art Cafe",
        "cuisine": ["Cafe", "Continental"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Neelankarai, Chennai", "lat": 12.9463, "lng": 80.2562},
        "ambience": "Romantic",
        "tags": ["ECR Beachfront", "Persian Flavors", "Sea Breeze", "Peaceful"],
        "description": "Tranquil East Coast Road beachside retreat serving authentic Iranian tea, kebabs, and pomegranate rice.",
        "image_url": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=500",
    },
    {
        "name": "Pumpkin Tales",
        "cuisine": ["Continental", "Cafe"],
        "price_range": "Premium",
        "avg_rating": 4.6,
        "location": {"area": "Alwarpet, Chennai", "lat": 13.0354, "lng": 80.2512},
        "ambience": "Trendy",
        "tags": ["All-Day Breakfast", "Gluten-Free", "Smoothie Bowls", "Woman-Led"],
        "description": "Sunlit global comfort bistro known for artisanal breads, healthy grain bowls, and French toast.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Writer's Cafe Gopalapuram",
        "cuisine": ["Cafe", "Continental", "Pizza"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "Gopalapuram, Chennai", "lat": 13.0514, "lng": 80.2536},
        "ambience": "Casual",
        "tags": ["Bookstore", "Social Cause", "Swiss Desserts", "Quiet Working"],
        "description": "Cozy bookstore cafe supporting burn survivors, serving Swiss-style fondues, thin pizzas, and coffees.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Southern Spice Taj Coromandel",
        "cuisine": ["South Indian"],
        "price_range": "Fine Dining",
        "avg_rating": 4.8,
        "location": {"area": "Nungambakkam, Chennai", "lat": 13.0610, "lng": 80.2470},
        "ambience": "Fine Dining",
        "tags": ["Royal Southern Cuisine", "Live Classical Music", "Five-Star Luxury"],
        "description": "Opulent temple-inspired dining room taking guests on a regal culinary voyage across South India.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Amelie's Cafe & Creamery",
        "cuisine": ["Italian", "Cafe", "Continental"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "MRC Nagar, Chennai", "lat": 13.0189, "lng": 80.2741},
        "ambience": "Romantic",
        "tags": ["Handcrafted Gelato", "Pastas", "Pastel Decor", "Outdoor Seating"],
        "description": "Pastel European-styled cafe serving handmade artisanal gelatos, crepes, and creamy risottos.",
        "image_url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=500",
    },

    # --- PUNE ---
    {
        "name": "German Bakery Koregaon Park",
        "cuisine": ["Cafe", "Continental", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "Koregaon Park, Pune", "lat": 18.5362, "lng": 73.8940},
        "ambience": "Trendy",
        "tags": ["Osho Ashram Vibe", "Kheema Pav", "Red Velvet Cake", "Bohemian"],
        "description": "Pune's bohemian heartbeat famous for organic herbal teas, German breads, and lively banter.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Vaishali FC Road",
        "cuisine": ["South Indian", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.6,
        "location": {"area": "FC Road, Pune", "lat": 18.5246, "lng": 73.8415},
        "ambience": "Casual",
        "tags": ["Mysore Masala Dosa", "SPDP", "Student Hub", "Filter Coffee"],
        "description": "The quintessential Pune student landmark famous for Mysore Masala Dosa, SPDP, and courtyard chats.",
        "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    },
    {
        "name": "Shabree FC Road",
        "cuisine": ["North Indian", "South Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.5,
        "location": {"area": "FC Road, Pune", "lat": 18.5230, "lng": 73.8421},
        "ambience": "Family",
        "tags": ["Authentic Maharashtrian Thali", "Puran Poli", "Pithla Bhakri"],
        "description": "Celebrated for traditional Maharashtrian vegetarian thalis loaded with zunka bhakri and puran poli.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Malaka Spice Koregaon Park",
        "cuisine": ["Thai", "Chinese", "Continental"],
        "price_range": "Premium",
        "avg_rating": 4.7,
        "location": {"area": "Koregaon Park, Pune", "lat": 18.5378, "lng": 73.8967},
        "ambience": "Romantic",
        "tags": ["Southeast Asian", "Art Gallery", "Farm-to-Table", "Cocktails"],
        "description": "Eclectic open-air South East Asian sanctuary blending original recipe street flavors with rotating art.",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500",
    },
    {
        "name": "George Restaurant Camp",
        "cuisine": ["North Indian", "Mughlai", "Biryani"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Camp, Pune", "lat": 18.5175, "lng": 73.8782},
        "ambience": "Casual",
        "tags": ["Chelo Kebab", "Mutton Biryani", "Heritage Camp"],
        "description": "Iconic military camp eatery celebrated for Persian Chelo Kebabs with buttered rice and biryani.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Cafe Goodluck",
        "cuisine": ["Cafe", "Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "Deccan Gymkhana, Pune", "lat": 18.5173, "lng": 73.8414},
        "ambience": "Casual",
        "tags": ["Irani Chai", "Bun Maska", "Keema Omelette", "Since 1935"],
        "description": "Oldest Irani cafe in Pune buzzing since 1935 with piping hot tea, butter-soaked buns, and keema pav.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Arthur's Theme",
        "cuisine": ["Continental", "Italian"],
        "price_range": "Premium",
        "avg_rating": 4.6,
        "location": {"area": "Koregaon Park, Pune", "lat": 18.5385, "lng": 73.8955},
        "ambience": "Romantic",
        "tags": ["European Fine Dining", "Knights Named Dishes", "Fondue"],
        "description": "Charming European bistro whose dishes are uniquely named after medieval historical royalty and knights.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Paasha JW Marriott",
        "cuisine": ["North Indian", "Mughlai"],
        "price_range": "Fine Dining",
        "avg_rating": 4.8,
        "location": {"area": "Senapati Bapat Road, Pune", "lat": 18.5327, "lng": 73.8298},
        "ambience": "Rooftop",
        "tags": ["Skyline View", "Kakori Kebab", "Dal Paasha", "Luxury Cocktails"],
        "description": "High-altitude rooftop lounge offering panoramic city skylines, melt-in-mouth kebabs, and ambient beats.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Marz-O-Rin",
        "cuisine": ["Fast Food", "Cafe"],
        "price_range": "Budget",
        "avg_rating": 4.3,
        "location": {"area": "Camp, Pune", "lat": 18.5190, "lng": 73.8791},
        "ambience": "Casual",
        "tags": ["Chutney Sandwich", "Cold Coffee", "Heritage Balcony"],
        "description": "Camp institution inside a colonial house serving legendary shredded chicken sandwiches and cold coffee.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "Effingut Brewerkz Baner",
        "cuisine": ["Continental", "Fast Food", "Pizza"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Baner, Pune", "lat": 18.5590, "lng": 73.7925},
        "ambience": "Trendy",
        "tags": ["Craft Beers", "Apple Cider", "Live Pub Quiz", "Outdoor Seating"],
        "description": "Vibrant craft brewery famous for legendary Apple Cider, Hefeweizen, and spicy loaded nachos.",
        "image_url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500",
    },
    {
        "name": "Blue Nile Camp",
        "cuisine": ["Biryani", "Mughlai", "North Indian"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Camp, Pune", "lat": 18.5211, "lng": 73.8764},
        "ambience": "Family",
        "tags": ["Irani Mutton Biryani", "Joojeh Kebab", "Camp Classic"],
        "description": "Pioneers of Irani-style biryani in Pune, known for slow-cooked Persian spiced meats and saffron rice.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Le Plaisir",
        "cuisine": ["Continental", "Cafe", "Italian"],
        "price_range": "Moderate",
        "avg_rating": 4.7,
        "location": {"area": "Prabhat Road, Pune", "lat": 18.5135, "lng": 73.8340},
        "ambience": "Trendy",
        "tags": ["Macarons", "Espresso Panna Cotta", "Artisan Sandwiches"],
        "description": "French-inspired bistro serving exquisite cheesecakes, artisanal sandwiches, and silken panna cotta.",
        "image_url": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=500",
    },

    # --- KOLKATA ---
    {
        "name": "Peter Cat",
        "cuisine": ["Continental", "North Indian"],
        "price_range": "Premium",
        "avg_rating": 4.8,
        "location": {"area": "Park Street, Kolkata", "lat": 22.5535, "lng": 88.3524},
        "ambience": "Romantic",
        "tags": ["Chelo Kebab", "Dim Light", "Heritage 1975", "Signature Dish"],
        "description": "Park Street's crown jewel celebrated for the world-renowned Chelo Kebab served with a dollop of butter.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Mocambo",
        "cuisine": ["Continental", "Italian"],
        "price_range": "Premium",
        "avg_rating": 4.7,
        "location": {"area": "Park Street, Kolkata", "lat": 22.5529, "lng": 88.3530},
        "ambience": "Romantic",
        "tags": ["Devilled Crab", "Chicken Tetrazzini", "Retro Red Lamps"],
        "description": "Kolkata's first nightclub turned heritage restaurant serving 1950s Continental delicacies like Devilled Crab.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Arsalan Park Circus",
        "cuisine": ["Biryani", "Mughlai"],
        "price_range": "Moderate",
        "avg_rating": 4.6,
        "location": {"area": "Park Circus, Kolkata", "lat": 22.5432, "lng": 88.3664},
        "ambience": "Family",
        "tags": ["Kolkata Biryani with Aloo", "Mutton Chaap", "Mughlai Heritage"],
        "description": "Benchmark Kolkata biryani institution famous for tender meat, aromatic long-grain rice, and the iconic boiled potato.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Flurys Park Street",
        "cuisine": ["Cafe", "Continental", "Fast Food"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Park Street, Kolkata", "lat": 22.5539, "lng": 88.3518},
        "ambience": "Trendy",
        "tags": ["English Breakfast", "Rum Balls", "Heritage Tearoom 1927"],
        "description": "Park Street's legendary European tearoom serving British breakfast, tea pastries, and decadent rum balls.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    },
    {
        "name": "6 Ballygunge Place",
        "cuisine": ["North Indian", "South Indian"],
        "price_range": "Premium",
        "avg_rating": 4.7,
        "location": {"area": "Ballygunge, Kolkata", "lat": 22.5273, "lng": 88.3670},
        "ambience": "Family",
        "tags": ["Authentic Bengali", "Daab Chingri", "Kosha Mangsho", "Colonial Bungalow"],
        "description": "Majestic century-old colonial bungalow serving authentic Bengali gems like Daab Chingri and Bhetki Paturi.",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    },
    {
        "name": "Kusum Rolls",
        "cuisine": ["Fast Food"],
        "price_range": "Budget",
        "avg_rating": 4.5,
        "location": {"area": "Park Street, Kolkata", "lat": 22.5542, "lng": 88.3512},
        "ambience": "Casual",
        "tags": ["Kathi Roll Origin", "Egg Chicken Roll", "Street Food Legend"],
        "description": "The quintessential street-corner shrine where crispy parathas are rolled with spiced tandoori fillings.",
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500",
    },
    {
        "name": "Oh! Calcutta",
        "cuisine": ["North Indian"],
        "price_range": "Fine Dining",
        "avg_rating": 4.6,
        "location": {"area": "Elgin Road, Kolkata", "lat": 22.5398, "lng": 88.3515},
        "ambience": "Fine Dining",
        "tags": ["Royal Bengali Feasts", "Hilsa Festival", "Smoked Bhetki"],
        "description": "Refined ode to Kolkata's colonial culinary history featuring mustard-infused fish curries and Gondhoraj coolers.",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500",
    },
    {
        "name": "Shiraz Golden Restaurant",
        "cuisine": ["Biryani", "Mughlai"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Mullick Bazar, Kolkata", "lat": 22.5467, "lng": 88.3621},
        "ambience": "Casual",
        "tags": ["Awadhi Heritage", "Mutton Biryani", "Rezala Curry"],
        "description": "Awadhi culinary heritage preserved in Kolkata, renowned for delicate aromatic biryani and milky mutton rezala.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Bohemian Ballygunge",
        "cuisine": ["Continental", "North Indian"],
        "price_range": "Premium",
        "avg_rating": 4.5,
        "location": {"area": "Ballygunge, Kolkata", "lat": 22.5255, "lng": 88.3644},
        "ambience": "Trendy",
        "tags": ["Fusion Bengali", "Panch Phoron Spiced", "Contemporary"],
        "description": "Innovative kitchen reimagining traditional Bengali ingredients like mustard, gondhoraj lemon, and paanch phoron.",
        "image_url": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=500",
    },
    {
        "name": "Aminia New Market",
        "cuisine": ["Biryani", "Mughlai"],
        "price_range": "Budget",
        "avg_rating": 4.3,
        "location": {"area": "New Market, Kolkata", "lat": 22.5604, "lng": 88.3533},
        "ambience": "Casual",
        "tags": ["Oldest Biryani 1929", "Awadhi Korma", "Affordable"],
        "description": "Feeding generations since 1929 near New Market with spiced Awadhi biryanis, pasinda kebabs, and firni.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    },
    {
        "name": "Tung Fong",
        "cuisine": ["Chinese"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Park Street, Kolkata", "lat": 22.5531, "lng": 88.3521},
        "ambience": "Family",
        "tags": ["Calcutta Tangra Chinese", "Chilli Chicken", "Hakka Noodles"],
        "description": "Classic Park Street Cantonese and Tangra-style Indo-Chinese restaurant famous for crispy chilli chicken.",
        "image_url": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=500",
    },
    {
        "name": "Barbeque Nation Salt Lake",
        "cuisine": ["North Indian", "Continental"],
        "price_range": "Moderate",
        "avg_rating": 4.4,
        "location": {"area": "Salt Lake Sector V, Kolkata", "lat": 22.5714, "lng": 88.4312},
        "ambience": "Family",
        "tags": ["Live Grill at Table", "Unlimited Buffet", "Kulfi Nation"],
        "description": "Pioneering live-on-table barbecue skewers with unlimited buffet courses and decadent dessert counters.",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500",
    },
]

# -------------------------------------------------------------------------
# 2. GENERATE 116 COMPLEMENTARY REALISTIC RESTAURANTS (TOTAL 200)
# -------------------------------------------------------------------------
CITIES_INFO = [
    {
        "city": "Delhi",
        "areas": [
            ("Connaught Place", 28.6328, 77.2195),
            ("Khan Market", 28.6003, 77.2270),
            ("Hauz Khas Village", 28.5494, 77.2001),
            ("Greater Kailash", 28.5398, 77.2410),
            ("Defence Colony", 28.5729, 77.2345),
            ("Vasant Kunj", 28.5298, 77.1542),
            ("Rajouri Garden", 28.6472, 77.1219),
            ("Cyber City", 28.4950, 77.0895),
        ],
    },
    {
        "city": "Mumbai",
        "areas": [
            ("Bandra West", 19.0620, 72.8332),
            ("Colaba", 18.9229, 72.8317),
            ("Lower Parel", 18.9953, 72.8258),
            ("Juhu", 19.0988, 72.8264),
            ("Andheri West", 19.1136, 72.8697),
            ("Powai", 19.1176, 72.9060),
            ("Kala Ghoda", 18.9272, 72.8327),
            ("Worli", 19.0134, 72.8184),
        ],
    },
    {
        "city": "Bangalore",
        "areas": [
            ("Indiranagar", 12.9784, 77.6408),
            ("Koramangala", 12.9345, 77.6200),
            ("Lavelle Road", 12.9702, 77.5998),
            ("Whitefield", 12.9822, 77.7289),
            ("HSR Layout", 12.9121, 77.6446),
            ("JP Nagar", 12.9063, 77.5857),
            ("MG Road", 12.9756, 77.6066),
            ("Malleshwaram", 13.0031, 77.5709),
        ],
    },
    {
        "city": "Hyderabad",
        "areas": [
            ("Jubilee Hills", 17.4319, 78.4073),
            ("Banjara Hills", 17.4239, 78.4482),
            ("Gachibowli", 17.4385, 78.3582),
            ("Hitec City", 17.4483, 78.3741),
            ("Kondapur", 17.4682, 78.3619),
            ("Begumpet", 17.4448, 78.4680),
            ("Madhapur", 17.4483, 78.3915),
            ("Secunderabad", 17.4411, 78.4870),
        ],
    },
    {
        "city": "Chennai",
        "areas": [
            ("T. Nagar", 13.0418, 80.2341),
            ("Alwarpet", 13.0336, 80.2520),
            ("Nungambakkam", 13.0604, 80.2425),
            ("Besant Nagar", 13.0003, 80.2667),
            ("Adyar", 13.0012, 80.2565),
            ("Mylapore", 13.0339, 80.2690),
            ("Anna Nagar", 13.0850, 80.2101),
            ("ECR Road", 12.9463, 80.2562),
        ],
    },
    {
        "city": "Pune",
        "areas": [
            ("Koregaon Park", 18.5362, 73.8940),
            ("Kalyani Nagar", 18.5477, 73.9037),
            ("FC Road", 18.5246, 73.8415),
            ("Baner", 18.5590, 73.7925),
            ("Viman Nagar", 18.5679, 73.9143),
            ("Deccan Gymkhana", 18.5173, 73.8414),
            ("Camp", 18.5175, 73.8782),
            ("Balewadi High Street", 18.5772, 73.7744),
        ],
    },
    {
        "city": "Kolkata",
        "areas": [
            ("Park Street", 22.5535, 88.3524),
            ("Ballygunge", 22.5273, 88.3670),
            ("Salt Lake", 22.5714, 88.4312),
            ("New Town", 22.5851, 88.4687),
            ("Gariahat", 22.5186, 88.3653),
            ("Southern Avenue", 22.5112, 88.3564),
            ("Elgin Road", 22.5398, 88.3515),
            ("Alipore", 22.5312, 88.3308),
        ],
    },
]

NAME_PREFIXES = [
    "Copper", "The Saffron", "Royal", "Amber", "Urban", "The Coastal",
    "Spice", "Little", "The Golden", "Bistro", "The Glass", "Casa",
    "Trattoria", "Wok &", "House of", "Brew &", "The Secret", "Szechuan",
    "Bella", "Social", "Mama", "Oven", "Rustic", "The Velvet"
]

NAME_SUFFIXES = [
    "Kitchen", "Lounge", "Grill", "Bistro", "Table", "Room", "Courtyard",
    "Story", "Corner", "Boutique", "Haven", "Social", "Palace", "Express",
    "Club", "Tavern", "Garden", "Canteen", "Pot", "Bakehouse"
]

CUISINE_OPTIONS = [
    ["North Indian", "Mughlai"],
    ["South Indian"],
    ["Chinese", "Thai"],
    ["Italian", "Pizza"],
    ["Continental", "Cafe"],
    ["Fast Food", "Cafe"],
    ["Biryani", "North Indian"],
    ["Sushi", "Thai"],
    ["Mexican", "Continental"],
    ["North Indian", "South Indian"],
    ["Italian", "Continental"],
    ["Cafe", "Fast Food"],
]

PRICE_RANGES = ["Budget", "Moderate", "Premium", "Fine Dining"]
AMBIENCE_OPTIONS = ["Casual", "Family", "Romantic", "Trendy", "Rooftop", "Fine Dining"]

ALL_TAG_POOL = [
    "Spicy", "Vegan-Friendly", "Pet-Friendly", "Live Music", "Outdoor Seating",
    "Craft Beer", "Late Night", "Valet Parking", "Buffet", "Waterfront",
    "Organic", "Dessert Bar", "Woodfired Oven", "Gluten-Free Options",
    "Cocktails", "Wine Cellar", "Cozy Corner", "City Views"
]

UNSPLASH_CUISINE_IMAGES = {
    "North Indian": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500",
    "South Indian": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=500",
    "Chinese": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=500",
    "Italian": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=500",
    "Continental": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
    "Fast Food": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500",
    "Biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500",
    "Sushi": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500",
    "Cafe": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500",
    "Pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500",
    "Mughlai": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500",
    "Thai": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=500",
}


def generate_complementary_restaurants(count: int, start_idx: int) -> List[Dict[str, Any]]:
    """Generates realistic named restaurants to reach the required total of 200."""
    generated = []
    random.seed(42)  # Deterministic seed for reproducible testing

    for i in range(count):
        city_data = CITIES_INFO[i % len(CITIES_INFO)]
        city_name = city_data["city"]
        area_name, base_lat, base_lng = city_data["areas"][i % len(city_data["areas"])]

        # Small random jitter to coordinates within ~1.5 km of area center
        lat = round(base_lat + random.uniform(-0.015, 0.015), 4)
        lng = round(base_lng + random.uniform(-0.015, 0.015), 4)

        prefix = NAME_PREFIXES[i % len(NAME_PREFIXES)]
        suffix = NAME_SUFFIXES[(i * 3) % len(NAME_SUFFIXES)]
        rest_name = f"{prefix} {suffix} {area_name.split()[0]}"

        cuisine = CUISINE_OPTIONS[i % len(CUISINE_OPTIONS)]
        primary_cuisine = cuisine[0]
        price_range = PRICE_RANGES[(i + 1) % len(PRICE_RANGES)]
        ambience = AMBIENCE_OPTIONS[(i * 2) % len(AMBIENCE_OPTIONS)]
        avg_rating = round(random.uniform(3.6, 4.8), 1)

        # 3 to 6 unique tags
        tag_count = random.randint(3, 5)
        selected_tags = random.sample(ALL_TAG_POOL, tag_count)

        img = UNSPLASH_CUISINE_IMAGES.get(
            primary_cuisine,
            f"https://source.unsplash.com/400x300/?restaurant,{primary_cuisine.lower()}"
        )

        desc = (
            f"A delightful {ambience.lower()} restaurant in {area_name}, {city_name} "
            f"specializing in freshly prepared {', '.join(cuisine)} dishes and drinks."
        )

        generated.append({
            "name": rest_name,
            "cuisine": cuisine,
            "price_range": price_range,
            "avg_rating": avg_rating,
            "location": {
                "area": f"{area_name}, {city_name}",
                "lat": lat,
                "lng": lng,
            },
            "ambience": ambience,
            "tags": selected_tags,
            "description": desc,
            "image_url": img,
        })

    return generated


# Combine to form exactly 200 restaurants
needed_generated = 200 - len(HARDCODED_RESTAURANTS)
ALL_200_RESTAURANTS = HARDCODED_RESTAURANTS + generate_complementary_restaurants(
    needed_generated, len(HARDCODED_RESTAURANTS)
)


# -------------------------------------------------------------------------
# 3. 50 REALISTIC USERS
# -------------------------------------------------------------------------
USER_NAMES_PREFS = [
    ("Aarav Sharma", "Non-Vegetarian", ["North Indian", "Mughlai", "Biryani"], "Delhi", "Fine Dining"),
    ("Priya Patel", "Vegetarian", ["South Indian", "Italian", "Cafe"], "Mumbai", "Moderate"),
    ("Rohan Mehta", "Non-Vegetarian", ["Continental", "Pizza", "Fast Food"], "Bangalore", "Moderate"),
    ("Ananya Iyer", "Vegetarian", ["South Indian", "North Indian"], "Chennai", "Budget"),
    ("Vikram Singh", "Non-Vegetarian", ["North Indian", "Biryani"], "Delhi", "Premium"),
    ("Sneha Reddy", "Non-Vegetarian", ["Biryani", "South Indian", "Mughlai"], "Hyderabad", "Moderate"),
    ("Arjun Nair", "Non-Vegetarian", ["Continental", "Italian", "Cafe"], "Bangalore", "Fine Dining"),
    ("Kavya Deshmukh", "Vegetarian", ["North Indian", "Fast Food", "Cafe"], "Pune", "Budget"),
    ("Aditya Verma", "Non-Vegetarian", ["North Indian", "Continental"], "Delhi", "Moderate"),
    ("Ishaan Joshi", "Vegetarian", ["South Indian", "Cafe"], "Pune", "Budget"),
    ("Tanvi Sengupta", "Non-Vegetarian", ["Continental", "Chinese", "Biryani"], "Kolkata", "Premium"),
    ("Rahul Kulkarni", "Non-Vegetarian", ["Continental", "Pizza", "Fast Food"], "Pune", "Moderate"),
    ("Neha Bansal", "Vegetarian", ["Italian", "Cafe", "Continental"], "Delhi", "Fine Dining"),
    ("Karan Malhotra", "Non-Vegetarian", ["North Indian", "Mughlai"], "Delhi", "Premium"),
    ("Ritu Chatterjee", "Non-Vegetarian", ["Chinese", "Continental", "Biryani"], "Kolkata", "Moderate"),
    ("Varun Kapoor", "Non-Vegetarian", ["Italian", "Continental", "Fast Food"], "Mumbai", "Fine Dining"),
    ("Pooja Hegde", "Vegetarian", ["South Indian", "Italian"], "Bangalore", "Moderate"),
    ("Siddharth Rao", "Non-Vegetarian", ["Biryani", "South Indian"], "Hyderabad", "Budget"),
    ("Divya Menon", "Vegetarian", ["South Indian", "Cafe"], "Chennai", "Budget"),
    ("Manish Tiwari", "Vegetarian", ["North Indian", "Mughlai"], "Delhi", "Moderate"),
    ("Sanya Mirza", "Non-Vegetarian", ["Biryani", "Mughlai", "Thai"], "Hyderabad", "Premium"),
    ("Deepak Gupta", "Vegetarian", ["North Indian", "South Indian"], "Delhi", "Budget"),
    ("Meera Nambiar", "Non-Vegetarian", ["Continental", "Italian", "Cafe"], "Bangalore", "Moderate"),
    ("Nikhil Bhat", "Non-Vegetarian", ["Fast Food", "Pizza", "Continental"], "Mumbai", "Budget"),
    ("Swati Saxena", "Vegetarian", ["Italian", "Continental"], "Pune", "Moderate"),
    ("Gaurav Chauhan", "Non-Vegetarian", ["North Indian", "Biryani"], "Delhi", "Moderate"),
    ("Aishwarya Sundaram", "Vegetarian", ["South Indian", "Fast Food"], "Chennai", "Budget"),
    ("Kunal Shah", "Vegetarian", ["Italian", "Pizza", "Cafe"], "Mumbai", "Fine Dining"),
    ("Shruti Bose", "Non-Vegetarian", ["Chinese", "Continental"], "Kolkata", "Moderate"),
    ("Harsh Vardhan", "Non-Vegetarian", ["North Indian", "Mughlai"], "Hyderabad", "Moderate"),
    ("Preeti Nair", "Vegetarian", ["South Indian", "Cafe"], "Bangalore", "Budget"),
    ("Abhishek Roy", "Non-Vegetarian", ["Continental", "Fast Food", "Biryani"], "Kolkata", "Moderate"),
    ("Alok Mishra", "Vegetarian", ["North Indian", "South Indian"], "Delhi", "Budget"),
    ("Ankita Das", "Non-Vegetarian", ["Chinese", "Thai", "Continental"], "Kolkata", "Premium"),
    ("Devendra Patil", "Non-Vegetarian", ["North Indian", "Mughlai"], "Pune", "Moderate"),
    ("Pallavi Krishnan", "Vegetarian", ["South Indian", "Italian"], "Chennai", "Moderate"),
    ("Tarun Khurana", "Non-Vegetarian", ["North Indian", "Biryani"], "Delhi", "Premium"),
    ("Simran Gill", "Non-Vegetarian", ["Continental", "Cafe", "Italian"], "Mumbai", "Fine Dining"),
    ("Sameer Deshpande", "Non-Vegetarian", ["Continental", "Pizza", "Fast Food"], "Pune", "Moderate"),
    ("Aparna Sen", "Non-Vegetarian", ["Continental", "Chinese"], "Kolkata", "Fine Dining"),
    ("Vishal Agarwal", "Vegetarian", ["North Indian", "Fast Food"], "Delhi", "Budget"),
    ("Rashmi Pillai", "Vegetarian", ["South Indian", "Cafe"], "Bangalore", "Moderate"),
    ("Prateek Jain", "Vegetarian", ["North Indian", "Italian"], "Mumbai", "Moderate"),
    ("Shreya Ghoshal", "Non-Vegetarian", ["Continental", "Italian", "Cafe"], "Kolkata", "Premium"),
    ("Rajesh Kumar", "Non-Vegetarian", ["North Indian", "Biryani"], "Hyderabad", "Budget"),
    ("Shalini Varma", "Vegetarian", ["South Indian", "North Indian"], "Chennai", "Moderate"),
    ("Mohit Suri", "Non-Vegetarian", ["Fast Food", "Pizza", "Continental"], "Mumbai", "Budget"),
    ("Kavita Rao", "Vegetarian", ["South Indian", "Cafe"], "Hyderabad", "Budget"),
    ("Saurabh Trivedi", "Non-Vegetarian", ["North Indian", "Mughlai"], "Delhi", "Moderate"),
    ("Bhavna Chawla", "Vegetarian", ["Italian", "Cafe", "Continental"], "Bangalore", "Fine Dining"),
]


async def seed():
    """Clears tables and seeds 200 restaurants, 50 users, and ratings."""
    print("=" * 65)
    print("HYBRID RESTAURANT RECOMMENDER: DATABASE SEEDING SCRIPT")
    print("=" * 65)

    # Ensure tables exist (idempotent)
    await init_db()

    SessionLocal = get_sync_session_factory()
    session = SessionLocal()

    # 1. Clear existing tables (children first for FK safety)
    session.execute(delete(Rating))
    session.execute(delete(Restaurant))
    session.execute(delete(User))
    session.commit()
    print("Cleared tables: ratings, restaurants, users")

    # 2. Hash default password once for efficiency
    default_password = "password123"
    print(f"\nHashing default user password ('{default_password}')...")
    hashed_pw = hash_password(default_password)

    # 3. Insert Users
    print("\nInserting 50 realistic users...")
    user_objs = []
    for i, (name, diet, cuisines, location, budget) in enumerate(USER_NAMES_PREFS):
        is_first = (i == 0)
        email = "admin@hybridrec.com" if is_first else f"{name.lower().replace(' ', '.')}@example.com"
        user_objs.append(User(
            name=name,
            email=email,
            password_hash=hashed_pw,
            preferences={
                "diet": [diet],
                "cuisines": cuisines,
                "location": location,
                "budget": budget,
            },
            is_admin=is_first,
            created_at=datetime.utcnow() - timedelta(days=random.randint(10, 180)),
        ))

    session.add_all(user_objs)
    session.commit()
    for u in user_objs:
        session.refresh(u)
    user_ids = [u.id for u in user_objs]
    print(f"Successfully inserted {len(user_ids)} users (Admin: admin@hybridrec.com / password123).")

    # 4. Insert Restaurants
    print(f"\nInserting {len(ALL_200_RESTAURANTS)} restaurants across 7 cities...")
    rest_objs = []
    for r in ALL_200_RESTAURANTS:
        rest_objs.append(Restaurant(
            name=r["name"],
            cuisine=r["cuisine"],
            price_range=r["price_range"],
            avg_rating=r.get("avg_rating", 0.0),
            rating_count=0,
            location=r["location"],
            ambience=r["ambience"],
            tags=r["tags"],
            description=r.get("description", ""),
            image_url=r.get("image_url", ""),
        ))

    session.add_all(rest_objs)
    session.commit()
    for r in rest_objs:
        session.refresh(r)
    restaurant_ids = [r.id for r in rest_objs]
    print(f"Successfully inserted {len(restaurant_ids)} restaurants.")

    # 5. Generate and Insert Ratings
    # Each user rates 5 to 20 restaurants, with realistic distribution favoring 3-5
    print("\nGenerating realistic ratings (favoring 3-5 stars)...")
    rating_scores_pool = [1, 2, 3, 3, 4, 4, 4, 5, 5]  # Weighted probability distribution
    rating_objs = []
    rest_ratings_map: Dict[int, List[int]] = {rid: [] for rid in restaurant_ids}

    random.seed(101)  # Predictable generation

    for uid in user_ids:
        # Choose 5 to 20 unique restaurants to rate
        num_ratings = random.randint(5, 20)
        chosen_rests = random.sample(restaurant_ids, num_ratings)

        for rid in chosen_rests:
            score = random.choice(rating_scores_pool)
            days_ago = random.randint(1, 90)
            timestamp = datetime.utcnow() - timedelta(days=days_ago, minutes=random.randint(0, 1440))

            rating_objs.append(Rating(
                user_id=uid,
                restaurant_id=rid,
                score=score,
                timestamp=timestamp,
            ))
            rest_ratings_map[rid].append(score)

    if rating_objs:
        session.add_all(rating_objs)
        session.commit()
    print(f"Successfully inserted {len(rating_objs)} ratings.")

    # 6. Synchronize Restaurant avg_rating and rating_count
    print("\nUpdating restaurant average ratings and rating counts...")
    rest_by_id = {r.id: r for r in rest_objs}
    for rid, scores in rest_ratings_map.items():
        rest = rest_by_id.get(rid)
        if not rest:
            continue
        if scores:
            rest.avg_rating = round(sum(scores) / len(scores), 2)
            rest.rating_count = len(scores)
        else:
            rest.avg_rating = 3.5
            rest.rating_count = 0
    session.commit()

    # 7. Print Summary Statistics
    total_users = session.execute(select(func.count(User.id))).scalar() or 0
    total_rests = session.execute(select(func.count(Restaurant.id))).scalar() or 0
    total_ratings = session.execute(select(func.count(Rating.id))).scalar() or 0
    avg_ratings_per_user = round(total_ratings / total_users, 1) if total_users else 0

    session.close()

    print("\n" + "=" * 65)
    print("SEEDING COMPLETE: SUMMARY STATISTICS")
    print("=" * 65)
    print(f"Total Restaurants:      {total_rests}")
    print(f"Total Users:            {total_users}")
    print(f"Total Ratings:          {total_ratings}")
    print(f"Avg Ratings Per User:   {avg_ratings_per_user}")
    print("Test Admin Account:     admin@hybridrec.com")
    print("Default User Password:  password123")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(seed())
