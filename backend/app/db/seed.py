"""Creates the tables and adds demo listings.

Run from the backend folder:  venv\\Scripts\\python.exe -m app.db.seed
"""
from app.db.connection import close_pool, create_tables, fetch_one, open_pool, pool

CRORE = 10_000_000
LAKH = 100_000

# (type, title, city, area, size_label, size_marla, price_pkr, purpose, bedrooms, description)
DEMO_LISTINGS = [
    # --- Houses for sale ---
    ("property", "10 Marla Modern House", "Islamabad", "Bahria Town Phase 8", "10 marla", 10, 3 * CRORE, "sale", 5,
     "Brand new double-storey house, near park and mosque, gas and electricity available."),
    ("property", "10 Marla House Near Main Boulevard", "Islamabad", "DHA Phase 2", "10 marla", 10, 4_75 * LAKH, "sale", 5,
     "Corner house, solar panels installed, 2 minutes from main boulevard."),
    ("property", "1 Kanal Luxury House", "Islamabad", "DHA Phase 2", "1 kanal", 20, 8_50 * LAKH, "sale", 6,
     "Basement, home theatre, servant quarter, facing park."),
    ("property", "7 Marla House", "Islamabad", "G-13", "7 marla", 7, 4_20 * LAKH, "sale", 4,
     "Well maintained, close to Metro and Kashmir Highway."),
    ("property", "5 Marla House", "Islamabad", "B-17 Multi Gardens", "5 marla", 5, 1_45 * LAKH, "sale", 3,
     "Ideal for small family, possession ready, installment option available."),
    ("property", "10 Marla House", "Rawalpindi", "Bahria Town Phase 7", "10 marla", 10, 2_80 * LAKH, "sale", 5,
     "Near Spring North commercial, recently renovated."),
    ("property", "1 Kanal House", "Islamabad", "F-11", "1 kanal", 20, 15 * CRORE, "sale", 6,
     "Prime sector, wide street, ideal for embassy or family."),
    # --- Plots for sale ---
    ("property", "5 Marla Residential Plot", "Islamabad", "B-17 Multi Gardens", "5 marla", 5, 72 * LAKH, "sale", None,
     "Developed block, on 3 year installment plan."),
    ("property", "10 Marla Residential Plot", "Islamabad", "DHA Phase 5", "10 marla", 10, 1_90 * LAKH, "sale", None,
     "Possession plot, sun-facing, all dues clear."),
    ("property", "1 Kanal Plot", "Islamabad", "Gulberg Greens", "1 kanal", 20, 2_40 * LAKH, "sale", None,
     "Near Islamabad Expressway, good for farmhouse-style home."),
    ("property", "8 Marla Commercial Plot", "Islamabad", "Bahria Enclave", "8 marla", 8, 3_10 * LAKH, "sale", None,
     "Main boulevard commercial, high rental potential."),
    # --- Rentals ---
    ("property", "10 Marla Upper Portion for Rent", "Islamabad", "G-13", "10 marla", 10, 85_000, "rent", 3,
     "Separate entrance, family only, monthly rent."),
    ("property", "2 Bed Apartment for Rent", "Islamabad", "E-11", "1100 sq ft", None, 1_10_000, "rent", 2,
     "Furnished, lift and parking, monthly rent."),
    ("property", "5 Marla House for Rent", "Rawalpindi", "Bahria Town Phase 4", "5 marla", 5, 65_000, "rent", 3,
     "Near Civic Center, monthly rent."),
    ("property", "1 Kanal House for Rent", "Islamabad", "DHA Phase 2", "1 kanal", 20, 2_50_000, "rent", 5,
     "Fully furnished, monthly rent."),
    # --- Cars (for car-dealer leads) ---
    ("car", "Toyota Corolla Altis 1.6 2021", "Islamabad", "Blue Area Showroom", "2021, 45,000 km", None, 62 * LAKH, "sale", None,
     "First owner, Islamabad registered, full service history."),
    ("car", "Honda Civic Oriel 2020", "Islamabad", "I-8 Markaz Showroom", "2020, 60,000 km", None, 68 * LAKH, "sale", None,
     "Genuine paint, sunroof, auto transmission."),
    ("car", "Suzuki Alto VXL AGS 2023", "Rawalpindi", "Saddar Showroom", "2023, 15,000 km", None, 30 * LAKH, "sale", None,
     "Automatic, fuel efficient, ideal first car."),
    ("car", "Toyota Yaris 1.3 2022", "Islamabad", "Blue Area Showroom", "2022, 30,000 km", None, 48 * LAKH, "sale", None,
     "Manual, excellent condition, bank leasing possible."),
    ("car", "Kia Sportage AWD 2021", "Islamabad", "I-8 Markaz Showroom", "2021, 50,000 km", None, 85 * LAKH, "sale", None,
     "All-wheel drive, panoramic roof, top variant."),
]


def seed_listings() -> int:
    row = fetch_one("SELECT COUNT(*) AS n FROM listings")
    if row["n"] > 0:
        return 0  # already seeded; don't add duplicates

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO listings
                   (type, title, city, area, size_label, size_marla, price_pkr, purpose, bedrooms, description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                DEMO_LISTINGS,
            )
    return len(DEMO_LISTINGS)


if __name__ == "__main__":
    open_pool()
    try:
        create_tables()
        print("Tables ready.")
        added = seed_listings()
        print(f"Added {added} demo listings." if added else "Listings already exist, nothing added.")
    finally:
        close_pool()
