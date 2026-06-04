"""
Sample retail data for bootstrapping the registry
"""

SAMPLE_RETAILERS = [
    {
        "retailer_id": "house-of-nova-001",
        "name": "House of Nova",
        "website_url": "https://houseofnova.xyz",
        "agent_endpoint": "https://houseofnova.xyz/api/agent",
        "quality_tier": "luxury",
        "categories": ["luxury-outerwear", "puffer-jackets", "luxury-coats", "knitwear"],
        "x402_payment_address": "rN7n7otQDd6FczFgLdklrStb5bPH3fF8Ch",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "dover-street-market-001",
        "name": "Dover Street Market",
        "website_url": "https://www.doverstreetmarket.com",
        "agent_endpoint": "https://api.doverstreetmarket.com/agent",
        "quality_tier": "luxury",
        "categories": ["luxury-fashion", "designer-clothing", "shoes", "accessories"],
        "x402_payment_address": "rU6K7V8x8z7y5e4r3w2q1a0s9d8f7g6h",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "ssense-001",
        "name": "SSENSE",
        "website_url": "https://www.ssense.com",
        "agent_endpoint": "https://api.ssense.com/fashion-agent",
        "quality_tier": "luxury",
        "categories": ["designer-fashion", "luxury-apparel", "accessories", "footwear"],
        "x402_payment_address": "rK5j6h4g3f2d1s9a8q7w6e5r4t3y2u1i",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "browns-fashion-001",
        "name": "Browns Fashion",
        "website_url": "https://www.brownsfashion.com",
        "agent_endpoint": "https://api.brownsfashion.com/discovery",
        "quality_tier": "luxury",
        "categories": ["luxury-designer", "emerging-designers", "contemporary"],
        "x402_payment_address": "rP8k9l0m1n2b3v4c5x6z7a8s9d0f1g2",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "farfetch-001",
        "name": "Farfetch",
        "website_url": "https://www.farfetch.com",
        "agent_endpoint": "https://api.farfetch.com/agent",
        "quality_tier": "luxury",
        "categories": ["designer-fashion", "luxury-shoes", "accessories", "menswear"],
        "x402_payment_address": "rH3d4e5f6g7h8i9j0k1l2m3n4o5p6q7",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "vestiaire-collective-001",
        "name": "Vestiaire Collective",
        "website_url": "https://www.vestiairecollective.com",
        "agent_endpoint": "https://api.vestiairecollective.com/discovery",
        "quality_tier": "premium",
        "categories": ["pre-owned-luxury", "designer-resale", "sustainable-fashion"],
        "x402_payment_address": "rE2r3t4y5u6i7o8p9a0s1d2f3g4h5j",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "the-real-real-001",
        "name": "TheRealReal",
        "website_url": "https://www.therealreal.com",
        "agent_endpoint": "https://api.therealreal.com/fashion-agent",
        "quality_tier": "premium",
        "categories": ["luxury-consignment", "pre-owned", "designer-goods"],
        "x402_payment_address": "rT6h7j8k9l0m1n2b3v4c5x6z7a8s9d",
        "is_verified": True,
        "status": "active"
    },
    {
        "retailer_id": "matchesfashion-001",
        "name": "MATCHES FASHION",
        "website_url": "https://www.matchesfashion.com",
        "agent_endpoint": "https://api.matchesfashion.com/search",
        "quality_tier": "luxury",
        "categories": ["luxury-designer", "contemporary", "ready-to-wear"],
        "x402_payment_address": "rM9s8d7f6g5h4j3k2l1m0n9o8p7q6r",
        "is_verified": True,
        "status": "active"
    }
]

SAMPLE_BLACKLIST = [
    ("amazon.com", "Mass-market retailer"),
    ("temu.com", "Mass-market retailer"),
    ("shein.com", "Mass-market fast fashion"),
    ("fashionnova.com", "Mass-market fashion"),
    ("hm.com", "Mass-market fashion"),
    ("zara.com", "Mass-market fashion"),
    ("target.com", "Mass-market retailer"),
    ("walmart.com", "Mass-market retailer"),
    ("ebay.com", "Mass-market marketplace"),
    ("aliexpress.com", "Mass-market marketplace"),
    ("etsy.com", "General marketplace"),
    ("forever21.com", "Mass-market fast fashion"),
    ("fashionboutique.com", "Low-tier discount fashion"),
    ("boohoo.com", "Mass-market fast fashion"),
    ("asos.com", "Mass-market fashion"),
    ("prettylittlething.com", "Mass-market fast fashion"),
]
