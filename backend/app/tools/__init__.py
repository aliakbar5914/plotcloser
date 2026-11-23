from app.tools.bookings import book_visit, get_my_visits, schedule_follow_up
from app.tools.leads import qualify_lead
from app.tools.listings import search_listings
from app.tools.memory import save_user_memory

# Sales agent: find listings and understand the customer. It can NOT book anything.
SALES_TOOLS = [search_listings, qualify_lead, save_user_memory]

# Booking agent: visits, test drives, follow-ups. search_listings is read-only
# and lets it find the listing number when the customer names a place instead.
BOOKING_TOOLS = [book_visit, schedule_follow_up, get_my_visits, search_listings]

ALL_TOOLS = [search_listings, qualify_lead, save_user_memory,
             book_visit, schedule_follow_up, get_my_visits]
