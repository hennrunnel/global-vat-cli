from typing import Dict


CATEGORY_MAP: Dict[str, str] = {
    # Food & Groceries
    "Foodstuffs": "Food & Groceries",
    "Live Equines": "Food & Groceries",
    "Plant": "Food & Groceries",
    "Wine Fresh Grape": "Food & Groceries",
    # Books & Publications
    "Books": "Books & Publications",
    "Newspapers": "Books & Publications",
    "Periodicals": "Books & Publications",
    "Loan Libraries": "Books & Publications",
    # Pharmaceuticals & Medical Goods
    "Children Car Seats": "Pharmaceuticals & Medical Goods",
    "Medical Equipment": "Pharmaceuticals & Medical Goods",
    "Pharmaceutical Products": "Pharmaceuticals & Medical Goods",
    "Rescue Equipment": "Pharmaceuticals & Medical Goods",
    # Agricultural Supplies
    "Agricultural Equipment": "Agricultural Supplies",
    "Agricultural Production": "Agricultural Supplies",
    "Certain Agricultural Input": "Agricultural Supplies",
    "Chemical Fertilisers": "Agricultural Supplies",
    "Chemical Pesticides Environment": "Agricultural Supplies",
    # Art & Collectibles
    "100 Years Old": "Art & Collectibles",
    "Antiques": "Art & Collectibles",
    "Ceramics": "Art & Collectibles",
    "Enamels": "Art & Collectibles",
    "Impressions": "Art & Collectibles",
    "Photographs": "Art & Collectibles",
    "Pictures": "Art & Collectibles",
    "Postage": "Art & Collectibles",
    "Sculpture Casts": "Art & Collectibles",
    "Sculptures": "Art & Collectibles",
    "Tapestries": "Art & Collectibles",
    "Zoological": "Art & Collectibles",
    # Energy & Eco-Friendly Goods
    "Fossil Fuel": "Energy & Eco-Friendly Goods",
    "Fuel Mineral Oil": "Energy & Eco-Friendly Goods",
    "Solar Panels": "Energy & Eco-Friendly Goods",
    "Sustainable Energy": "Energy & Eco-Friendly Goods",
    "Wood": "Energy & Eco-Friendly Goods",
    "Wood Article98": "Energy & Eco-Friendly Goods",
    # Other Physical Goods
    "Bicycles Electric": "Other Physical Goods",
    "Child Wear": "Other Physical Goods",
    "Cleaning Product": "Other Physical Goods",
    "Printed Advertising Material": "Other Physical Goods",
    # Standard Rate
    "Region": "Standard Rate",
    "Standard": "Standard Rate",
}


UI_LABELS = [
    "Standard Rate",
    "Food & Groceries",
    "Books & Publications",
    "Pharmaceuticals & Medical Goods",
    "Agricultural Supplies",
    "Art & Collectibles",
    "Energy & Eco-Friendly Goods",
    "Other Physical Goods",
]


def map_category(source_label: str) -> str:
    if not source_label:
        return "Other Physical Goods"
    return CATEGORY_MAP.get(source_label.strip(), "Other Physical Goods")


