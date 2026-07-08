from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Category, SubCategory, BoycottProduct, PakistaniAlternative


SEED_DATA = [
    {
        'name': 'Food & Beverages', 'icon': '🍔', 'order': 1,
        'description': 'Everyday food products, snacks, and drinks',
        'subcategories': [
            {
                'name': 'Fast Food', 'icon': '🍟',
                'products': [
                    {'name': "McDonald's", 'brand': "McDonald's Corporation", 'reason': "McDonald's Israel provided free meals to Israeli soldiers during the Gaza conflict.", 'alternatives': [
                        {'name': 'Hardees Pakistan', 'brand': 'Hardees PK', 'description': 'Pakistani-operated fast food chain with similar menu options.'},
                        {'name': 'Burger Lab', 'brand': 'Burger Lab', 'description': 'Premium Pakistani burger chain with quality ingredients.'},
                        {'name': 'Smash Burger', 'brand': 'Smash Burger PK', 'description': 'Local smash burger chain growing across Pakistan.'},
                    ]},
                    {'name': 'Dominos Pizza', 'brand': 'Domino\'s Inc', 'reason': 'Domino\'s Israel donated food to Israeli military forces.', 'alternatives': [
                        {'name': 'Pizza Point', 'brand': 'Pizza Point PK', 'description': 'Pakistani pizza chain with great local flavors.'},
                        {'name': 'Crust Bros', 'brand': 'Crust Bros', 'description': 'Artisan pizza made by Pakistanis for Pakistanis.'},
                    ]},
                ]
            },
            {
                'name': 'Soft Drinks', 'icon': '🥤',
                'products': [
                    {'name': 'Coca-Cola', 'brand': 'The Coca-Cola Company', 'reason': 'Coca-Cola has operations in Israel and has been linked to supporting Israeli economy.', 'alternatives': [
                        {'name': 'Pakola', 'brand': 'Mehran Bottlers', 'description': 'Iconic Pakistani soft drink brand since 1950. Available in multiple flavors.', 'website': 'https://pakola.com.pk'},
                        {'name': 'Gourmet Cola', 'brand': 'Gourmet Foods', 'description': 'Pakistani cola brand with great taste at affordable price.'},
                        {'name': 'Makah Cola', 'brand': 'Makah Cola', 'description': 'Halal certified Pakistani cola alternative.'},
                    ]},
                    {'name': 'Pepsi', 'brand': 'PepsiCo', 'reason': 'PepsiCo has significant business interests in Israel.', 'alternatives': [
                        {'name': 'Pakola', 'brand': 'Mehran Bottlers', 'description': 'The original Pakistani soft drink — refreshing and proudly local.'},
                        {'name': 'Gourmet Drinks', 'brand': 'Gourmet Foods', 'description': 'Wide range of Pakistani beverages.'},
                    ]},
                    {'name': 'Sprite', 'brand': 'The Coca-Cola Company', 'reason': 'Coca-Cola subsidiary with Israeli operations.', 'alternatives': [
                        {'name': 'Pakola Lemon', 'brand': 'Mehran Bottlers', 'description': 'Refreshing lemon-lime Pakistani alternative.'},
                    ]},
                ]
            },
            {
                'name': 'Coffee & Tea', 'icon': '☕',
                'products': [
                    {'name': 'Starbucks', 'brand': 'Starbucks Corporation', 'reason': "Starbucks CEO Howard Schultz is a known supporter of Israel. The company has faced boycotts globally.", 'alternatives': [
                        {'name': 'Espresso', 'brand': 'Espresso PK', 'description': 'Premium Pakistani coffee chain with quality brews.'},
                        {'name': 'Gloria Jeans Pakistan', 'brand': 'Gloria Jeans PK', 'description': 'Australian-origin but Pakistani-operated coffee chain.'},
                        {'name': 'Chai Wala', 'brand': 'Local Chai Wala', 'description': 'Support your local chai wala — authentic desi experience!'},
                    ]},
                    {'name': 'Nescafe', 'brand': 'Nestlé', 'reason': 'Nestlé has significant operations and investments in Israel.', 'alternatives': [
                        {'name': 'Tapal Tea', 'brand': 'Tapal', 'description': 'Pakistan\'s leading tea brand since 1947.', 'website': 'https://tapal.com.pk'},
                        {'name': 'Vital Tea', 'brand': 'Vital Tea', 'description': 'Quality Pakistani tea brand.'},
                    ]},
                ]
            },
            {
                'name': 'Snacks & Chips', 'icon': '🍿',
                'products': [
                    {'name': "Lay's", 'brand': 'PepsiCo / Frito-Lay', 'reason': 'PepsiCo subsidiary with Israeli business operations.', 'alternatives': [
                        {'name': 'Kolson Slanty', 'brand': 'Kolson', 'description': 'Iconic Pakistani snack brand loved for generations.'},
                        {'name': 'Oye Hoye', 'brand': 'Ismail Industries', 'description': 'Popular Pakistani chips brand with great flavors.'},
                        {'name': 'Kurleez', 'brand': 'Ismail Industries', 'description': 'Pakistani corn snack — crunchy and delicious.'},
                    ]},
                    {'name': 'Pringles', 'brand': 'Kellogg\'s', 'reason': 'Kellogg\'s has operations in Israel.', 'alternatives': [
                        {'name': 'Oye Hoye', 'brand': 'Ismail Industries', 'description': 'Great Pakistani alternative to Pringles.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Personal Care', 'icon': '🧴', 'order': 2,
        'description': 'Hygiene, grooming, and personal care products',
        'subcategories': [
            {
                'name': 'Shampoo & Hair Care', 'icon': '💆',
                'products': [
                    {'name': 'Head & Shoulders', 'brand': 'Procter & Gamble', 'reason': 'P&G has significant business operations in Israel.', 'alternatives': [
                        {'name': 'Sunsilk Pakistan', 'brand': 'Unilever PK', 'description': 'Widely available Pakistani-market shampoo.'},
                        {'name': 'Saeed Ghani Hair Oil', 'brand': 'Saeed Ghani', 'description': 'Traditional Pakistani herbal hair care products.'},
                    ]},
                    {'name': 'Pantene', 'brand': 'Procter & Gamble', 'reason': 'P&G has significant business operations in Israel.', 'alternatives': [
                        {'name': 'Saeed Ghani', 'brand': 'Saeed Ghani', 'description': 'Herbal Pakistani hair care brand.'},
                    ]},
                ]
            },
            {
                'name': 'Soap & Body Wash', 'icon': '🧼',
                'products': [
                    {'name': 'Dove', 'brand': 'Unilever', 'reason': 'Unilever has operations in Israel.', 'alternatives': [
                        {'name': 'Dettol', 'brand': 'Reckitt (non-Israeli ops)', 'description': 'Widely trusted hygiene brand in Pakistan.'},
                        {'name': 'Safeguard Pakistan', 'brand': 'P&G PK', 'description': 'Antibacterial soap popular in Pakistan.'},
                        {'name': 'Lifebuoy', 'brand': 'Unilever PK', 'description': 'Affordable hygiene soap available everywhere.'},
                    ]},
                ]
            },
            {
                'name': 'Toothpaste', 'icon': '🦷',
                'products': [
                    {'name': 'Colgate', 'brand': 'Colgate-Palmolive', 'reason': 'Colgate-Palmolive has Israeli market operations.', 'alternatives': [
                        {'name': 'Medicam', 'brand': 'Medicam Pakistan', 'description': 'Pakistani toothpaste brand with fluoride protection.'},
                        {'name': 'Dentonic', 'brand': 'Dentonic PK', 'description': 'Trusted Pakistani dental care brand.'},
                        {'name': 'Miswak', 'brand': 'Dabur Pakistan', 'description': 'Herbal toothpaste with natural miswak extract.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Household & Cleaning', 'icon': '🏠', 'order': 3,
        'description': 'Home cleaning and household products',
        'subcategories': [
            {
                'name': 'Detergents', 'icon': '🧺',
                'products': [
                    {'name': 'Ariel', 'brand': 'Procter & Gamble', 'reason': 'P&G has significant business operations in Israel.', 'alternatives': [
                        {'name': 'Surf Excel', 'brand': 'Unilever PK', 'description': 'Pakistan\'s most popular detergent brand.'},
                        {'name': 'Bonus', 'brand': 'Colgate-Palmolive PK', 'description': 'Affordable Pakistani detergent.'},
                        {'name': 'Express Power', 'brand': 'Gul Ahmed', 'description': 'Pakistani detergent brand.'},
                    ]},
                ]
            },
            {
                'name': 'Dishwashing', 'icon': '🍽️',
                'products': [
                    {'name': 'Fairy / Dawn', 'brand': 'Procter & Gamble', 'reason': 'P&G has significant business operations in Israel.', 'alternatives': [
                        {'name': 'Vim', 'brand': 'Unilever PK', 'description': 'Popular Pakistani dishwashing brand.'},
                        {'name': 'Lemon Max', 'brand': 'Colgate-Palmolive PK', 'description': 'Trusted Pakistani dish soap.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Baby Products', 'icon': '👶', 'order': 4,
        'description': 'Baby food, diapers, and care products',
        'subcategories': [
            {
                'name': 'Baby Food', 'icon': '🍼',
                'products': [
                    {'name': 'Nestlé Cerelac', 'brand': 'Nestlé', 'reason': 'Nestlé has significant operations and investments in Israel.', 'alternatives': [
                        {'name': 'Mead Johnson Enfamil', 'brand': 'Mead Johnson', 'description': 'Alternative baby nutrition brand.'},
                        {'name': 'Homemade Khichdi', 'brand': 'Home Kitchen', 'description': 'Traditional Pakistani baby food — healthier and local!'},
                    ]},
                ]
            },
            {
                'name': 'Diapers', 'icon': '🧷',
                'products': [
                    {'name': 'Pampers', 'brand': 'Procter & Gamble', 'reason': 'P&G has significant business operations in Israel.', 'alternatives': [
                        {'name': 'Canbebe', 'brand': 'Canbebe', 'description': 'Turkish brand widely available in Pakistan.'},
                        {'name': 'Molfix', 'brand': 'Hayat Kimya', 'description': 'Quality diapers available in Pakistani markets.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Clothing & Fashion', 'icon': '👕', 'order': 5,
        'description': 'Apparel, footwear, and fashion accessories',
        'subcategories': [
            {
                'name': 'Sportswear', 'icon': '👟',
                'products': [
                    {'name': 'Nike', 'brand': 'Nike Inc.', 'reason': 'Nike has operations in Israel and has been linked to Israeli military sponsorships.', 'alternatives': [
                        {'name': 'Servis', 'brand': 'Servis Industries', 'description': 'Pakistan\'s largest footwear brand since 1959.', 'website': 'https://servis.com.pk'},
                        {'name': 'Bata Pakistan', 'brand': 'Bata PK', 'description': 'Trusted footwear brand with wide range.'},
                        {'name': 'Starlet', 'brand': 'Starlet Shoes', 'description': 'Affordable Pakistani footwear brand.'},
                    ]},
                    {'name': 'Adidas', 'brand': 'Adidas AG', 'reason': 'Adidas has Israeli market operations and partnerships.', 'alternatives': [
                        {'name': 'Servis', 'brand': 'Servis Industries', 'description': 'Quality Pakistani sports footwear.'},
                        {'name': 'Insignia', 'brand': 'Insignia PK', 'description': 'Pakistani fashion brand with sportswear line.'},
                    ]},
                ]
            },
            {
                'name': 'Casual Wear', 'icon': '👔',
                'products': [
                    {'name': 'Zara', 'brand': 'Inditex', 'reason': 'Inditex (Zara parent) has Israeli operations and the founder has made pro-Israel statements.', 'alternatives': [
                        {'name': 'Khaadi', 'brand': 'Khaadi', 'description': 'Premium Pakistani fashion brand with global presence.', 'website': 'https://khaadi.com'},
                        {'name': 'Gul Ahmed', 'brand': 'Gul Ahmed', 'description': 'Iconic Pakistani textile and fashion brand.'},
                        {'name': 'Alkaram Studio', 'brand': 'Alkaram', 'description': 'Quality Pakistani fashion at great prices.'},
                        {'name': 'Bonanza Satrangi', 'brand': 'Bonanza', 'description': 'Colorful Pakistani fashion brand.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Electronics & Tech', 'icon': '📱', 'order': 6,
        'description': 'Gadgets, software, and technology products',
        'subcategories': [
            {
                'name': 'Smartphones', 'icon': '📲',
                'products': [
                    {'name': 'Apple iPhone', 'brand': 'Apple Inc.', 'reason': 'Apple has significant R&D operations in Israel and has been linked to Israeli tech ecosystem.', 'alternatives': [
                        {'name': 'Samsung (Korean)', 'brand': 'Samsung Electronics', 'description': 'South Korean brand — no Israeli ties.'},
                        {'name': 'Xiaomi', 'brand': 'Xiaomi Corp', 'description': 'Chinese brand with great value for money.'},
                        {'name': 'Infinix', 'brand': 'Transsion Holdings', 'description': 'Affordable smartphones popular in Pakistan.'},
                    ]},
                ]
            },
            {
                'name': 'Software & Apps', 'icon': '💻',
                'products': [
                    {'name': 'Wix', 'brand': 'Wix.com Ltd', 'reason': 'Wix is an Israeli company headquartered in Tel Aviv.', 'alternatives': [
                        {'name': 'WordPress', 'brand': 'Automattic', 'description': 'Open-source website builder — American company.'},
                        {'name': 'Webflow', 'brand': 'Webflow Inc', 'description': 'Powerful website builder with no Israeli ties.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Health & Pharmacy', 'icon': '💊', 'order': 7,
        'description': 'Medicines, supplements, and health products',
        'subcategories': [
            {
                'name': 'Vitamins & Supplements', 'icon': '💉',
                'products': [
                    {'name': 'Ensure (Abbott)', 'brand': 'Abbott Laboratories', 'reason': 'Abbott has significant operations in Israel.', 'alternatives': [
                        {'name': 'Horlicks', 'brand': 'GSK PK', 'description': 'Nutritional supplement widely available in Pakistan.'},
                        {'name': 'Complan', 'brand': 'Complan PK', 'description': 'Pakistani market nutritional drink.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Dairy & Breakfast', 'icon': '🥛', 'order': 8,
        'description': 'Milk, yogurt, cereals, and breakfast items',
        'subcategories': [
            {
                'name': 'Milk & Dairy', 'icon': '🐄',
                'products': [
                    {'name': 'Nestlé Milk', 'brand': 'Nestlé', 'reason': 'Nestlé has significant operations and investments in Israel.', 'alternatives': [
                        {'name': 'Olpers', 'brand': 'Engro Foods', 'description': 'Pakistan\'s premium dairy brand by Engro.', 'website': 'https://engro.com'},
                        {'name': 'Nurpur', 'brand': 'Nurpur Dairy', 'description': 'Quality Pakistani dairy products.'},
                        {'name': 'Haleeb', 'brand': 'Haleeb Foods', 'description': 'Trusted Pakistani milk brand.'},
                        {'name': 'Good Milk', 'brand': 'Shakarganj', 'description': 'Pakistani dairy brand from Shakarganj.'},
                    ]},
                ]
            },
            {
                'name': 'Cereals', 'icon': '🥣',
                'products': [
                    {'name': 'Kellogg\'s Corn Flakes', 'brand': 'Kellogg\'s', 'reason': 'Kellogg\'s has operations in Israel.', 'alternatives': [
                        {'name': 'Quaker Oats', 'brand': 'PepsiCo (check local)', 'description': 'Widely available oats in Pakistan.'},
                        {'name': 'Shredded Wheat', 'brand': 'Local brands', 'description': 'Local wheat-based breakfast options.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Cosmetics & Beauty', 'icon': '💄', 'order': 9,
        'description': 'Makeup, skincare, and beauty products',
        'subcategories': [
            {
                'name': 'Skincare', 'icon': '✨',
                'products': [
                    {'name': 'Neutrogena', 'brand': 'Johnson & Johnson', 'reason': 'J&J has significant Israeli operations and investments.', 'alternatives': [
                        {'name': 'Saeed Ghani', 'brand': 'Saeed Ghani', 'description': 'Herbal Pakistani skincare brand with natural ingredients.'},
                        {'name': 'Hemani', 'brand': 'Hemani Herbals', 'description': 'Pakistani herbal beauty brand.', 'website': 'https://hemani.com.pk'},
                    ]},
                ]
            },
            {
                'name': 'Makeup', 'icon': '💅',
                'products': [
                    {'name': 'MAC Cosmetics', 'brand': 'Estée Lauder', 'reason': 'Estée Lauder has Israeli operations and the founder family has made pro-Israel statements.', 'alternatives': [
                        {'name': 'Rivaj UK', 'brand': 'Rivaj', 'description': 'Pakistani makeup brand with wide product range.'},
                        {'name': 'Medora', 'brand': 'Medora PK', 'description': 'Affordable Pakistani cosmetics brand.'},
                        {'name': 'Luscious Cosmetics', 'brand': 'Luscious', 'description': 'Premium Pakistani beauty brand.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Food Condiments', 'icon': '🧂', 'order': 10,
        'description': 'Sauces, spices, and cooking ingredients',
        'subcategories': [
            {
                'name': 'Sauces & Ketchup', 'icon': '🍅',
                'products': [
                    {'name': 'Heinz Ketchup', 'brand': 'Kraft Heinz', 'reason': 'Kraft Heinz has Israeli market operations.', 'alternatives': [
                        {'name': 'National Foods Ketchup', 'brand': 'National Foods', 'description': 'Pakistan\'s leading condiment brand.', 'website': 'https://nationalfoods.com.pk'},
                        {'name': 'Shangrila Ketchup', 'brand': 'Shangrila Foods', 'description': 'Quality Pakistani ketchup brand.'},
                    ]},
                ]
            },
            {
                'name': 'Spices & Masala', 'icon': '🌶️',
                'products': [
                    {'name': 'Knorr', 'brand': 'Unilever', 'reason': 'Unilever has operations in Israel.', 'alternatives': [
                        {'name': 'National Masala', 'brand': 'National Foods', 'description': 'Pakistan\'s #1 spice brand with authentic flavors.'},
                        {'name': 'Shan Foods', 'brand': 'Shan Foods', 'description': 'World-famous Pakistani spice brand exported globally.', 'website': 'https://shanfoods.com'},
                        {'name': 'Mehran Masala', 'brand': 'Mehran Foods', 'description': 'Quality Pakistani spice brand.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Restaurants & Dining', 'icon': '🍽️', 'order': 11,
        'description': 'Restaurant chains and dining brands to boycott',
        'subcategories': [
            {
                'name': 'Coffee Chains', 'icon': '☕',
                'products': [
                    {'name': 'Costa Coffee', 'brand': 'Coca-Cola Company', 'reason': 'Owned by Coca-Cola which has Israeli operations.', 'alternatives': [
                        {'name': 'Espresso PK', 'brand': 'Espresso', 'description': 'Premium Pakistani coffee chain.'},
                        {'name': 'Second Cup Pakistan', 'brand': 'Second Cup PK', 'description': 'Canadian-origin, Pakistani-operated coffee chain.'},
                    ]},
                    {'name': 'Tim Hortons', 'brand': 'Restaurant Brands International', 'reason': 'RBI has Israeli franchise operations.', 'alternatives': [
                        {'name': 'Chai Dhaba', 'brand': 'Local', 'description': 'Authentic Pakistani chai experience.'},
                        {'name': 'Espresso PK', 'brand': 'Espresso', 'description': 'Great coffee and snacks, proudly Pakistani.'},
                    ]},
                ]
            },
            {
                'name': 'Burger Chains', 'icon': '🍔',
                'products': [
                    {'name': 'Burger King', 'brand': 'Restaurant Brands International', 'reason': 'RBI has Israeli franchise operations and has been linked to supporting Israeli economy.', 'alternatives': [
                        {'name': 'Burger Lab', 'brand': 'Burger Lab PK', 'description': 'Premium Pakistani smash burger chain.'},
                        {'name': 'Johnny & Jugnu', 'brand': 'Johnny & Jugnu', 'description': 'Popular Pakistani burger chain with great flavors.'},
                        {'name': 'Brodburger', 'brand': 'Brodburger PK', 'description': 'Quality Pakistani burgers.'},
                    ]},
                    {'name': 'KFC', 'brand': 'Yum! Brands', 'reason': 'Yum! Brands has Israeli franchise operations.', 'alternatives': [
                        {'name': 'Crispy Fried Chicken (CFC)', 'brand': 'CFC Pakistan', 'description': 'Pakistani fried chicken chain.'},
                        {'name': 'Chicken Cottage', 'brand': 'Chicken Cottage PK', 'description': 'Halal fried chicken — Pakistani owned.'},
                        {'name': 'Nandos Pakistan', 'brand': 'Nandos PK', 'description': 'South African origin, Pakistani-operated peri-peri chicken.'},
                    ]},
                    {'name': 'Pizza Hut', 'brand': 'Yum! Brands', 'reason': 'Yum! Brands has Israeli franchise operations.', 'alternatives': [
                        {'name': 'Pizza Point', 'brand': 'Pizza Point PK', 'description': 'Pakistani pizza chain with local flavors.'},
                        {'name': 'Crust Bros', 'brand': 'Crust Bros', 'description': 'Artisan Pakistani pizza brand.'},
                        {'name': 'Sbarro Pakistan', 'brand': 'Sbarro PK', 'description': 'Italian-style pizza, Pakistani-operated.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Beverages & Juices', 'icon': '🧃', 'order': 12,
        'description': 'Juices, energy drinks, and bottled water',
        'subcategories': [
            {
                'name': 'Energy Drinks', 'icon': '⚡',
                'products': [
                    {'name': 'Red Bull', 'brand': 'Red Bull GmbH', 'reason': 'Red Bull has Israeli distribution and marketing operations.', 'alternatives': [
                        {'name': 'Power Horse', 'brand': 'Power Horse', 'description': 'Energy drink available in Pakistan.'},
                        {'name': 'Sting', 'brand': 'PepsiCo PK', 'description': 'Widely available energy drink in Pakistan.'},
                    ]},
                    {'name': 'Monster Energy', 'brand': 'Coca-Cola Company', 'reason': 'Owned by Coca-Cola which has Israeli operations.', 'alternatives': [
                        {'name': 'Sting Energy', 'brand': 'PepsiCo PK', 'description': 'Popular energy drink in Pakistan.'},
                    ]},
                ]
            },
            {
                'name': 'Juices & Water', 'icon': '🥤',
                'products': [
                    {'name': 'Tropicana', 'brand': 'PepsiCo', 'reason': 'PepsiCo has significant business interests in Israel.', 'alternatives': [
                        {'name': 'Shezan Juice', 'brand': 'Shezan International', 'description': 'Pakistan\'s iconic juice brand since 1964.', 'website': 'https://shezan.com.pk'},
                        {'name': 'Nestle Fruita Vitals', 'brand': 'Nestle PK', 'description': 'Fruit juices widely available in Pakistan.'},
                        {'name': 'Minute Maid', 'brand': 'Coca-Cola PK', 'description': 'Juice brand available in Pakistan.'},
                    ]},
                    {'name': 'Evian Water', 'brand': 'LVMH / Danone', 'reason': 'Danone has Israeli operations and investments.', 'alternatives': [
                        {'name': 'Nestle Pure Life', 'brand': 'Nestle PK', 'description': 'Widely available bottled water in Pakistan.'},
                        {'name': 'Aquafina', 'brand': 'PepsiCo PK', 'description': 'Purified bottled water.'},
                        {'name': 'Sufi Water', 'brand': 'Sufi Group', 'description': 'Pakistani bottled water brand.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Stationery & Office', 'icon': '📚', 'order': 13,
        'description': 'Stationery, office supplies, and school items',
        'subcategories': [
            {
                'name': 'Pens & Writing', 'icon': '✏️',
                'products': [
                    {'name': 'Pilot Pens', 'brand': 'Pilot Corporation', 'reason': 'Pilot has Israeli distribution partnerships.', 'alternatives': [
                        {'name': 'Dollar Pens', 'brand': 'Dollar Industries', 'description': 'Pakistan\'s leading pen manufacturer.'},
                        {'name': 'Flair Pens', 'brand': 'Flair PK', 'description': 'Affordable quality pens available in Pakistan.'},
                    ]},
                ]
            },
            {
                'name': 'School Supplies', 'icon': '🎒',
                'products': [
                    {'name': 'Staedtler', 'brand': 'Staedtler Mars GmbH', 'reason': 'Staedtler has Israeli market operations.', 'alternatives': [
                        {'name': 'Camel Art Supplies', 'brand': 'Camel PK', 'description': 'Pakistani art and stationery brand.'},
                        {'name': 'Dollar Stationery', 'brand': 'Dollar Industries', 'description': 'Comprehensive Pakistani stationery brand.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Automotive & Transport', 'icon': '🚗', 'order': 14,
        'description': 'Car brands, fuel, and automotive products',
        'subcategories': [
            {
                'name': 'Car Brands', 'icon': '🏎️',
                'products': [
                    {'name': 'Ford', 'brand': 'Ford Motor Company', 'reason': 'Ford has Israeli operations and has been linked to Israeli defense contracts.', 'alternatives': [
                        {'name': 'Suzuki Pakistan', 'brand': 'Pak Suzuki', 'description': 'Pakistan\'s most popular car brand — assembled locally.'},
                        {'name': 'United Autos', 'brand': 'United Motors', 'description': 'Pakistani automobile manufacturer.'},
                        {'name': 'Prince DFSK', 'brand': 'Regal Automobiles', 'description': 'Pakistani-assembled vehicles.'},
                    ]},
                ]
            },
            {
                'name': 'Lubricants & Oil', 'icon': '🛢️',
                'products': [
                    {'name': 'Castrol', 'brand': 'BP / Castrol', 'reason': 'BP has Israeli energy sector operations.', 'alternatives': [
                        {'name': 'PSO Lubricants', 'brand': 'Pakistan State Oil', 'description': 'Pakistani state oil company lubricants.'},
                        {'name': 'Attock Oil', 'brand': 'Attock Petroleum', 'description': 'Pakistani petroleum and lubricant brand.'},
                    ]},
                ]
            },
        ]
    },
    {
        'name': 'Financial Services', 'icon': '💳', 'order': 15,
        'description': 'Banks, payment services, and financial products',
        'subcategories': [
            {
                'name': 'Payment Services', 'icon': '💰',
                'products': [
                    {'name': 'PayPal', 'brand': 'PayPal Holdings', 'reason': 'PayPal has Israeli operations and has been accused of discriminatory practices against Palestinians.', 'alternatives': [
                        {'name': 'JazzCash', 'brand': 'Jazz / VEON', 'description': 'Pakistan\'s leading mobile payment service.'},
                        {'name': 'Easypaisa', 'brand': 'Telenor Pakistan', 'description': 'Widely used Pakistani mobile wallet.'},
                        {'name': 'SadaPay', 'brand': 'SadaPay', 'description': 'Modern Pakistani digital banking app.'},
                    ]},
                ]
            },
        ]
    },
]


class Command(BaseCommand):
    help = 'Seed database with boycott products and Pakistani alternatives'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding database...')

        for cat_data in SEED_DATA:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(cat_data['name']),
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                    'description': cat_data.get('description', ''),
                }
            )
            self.stdout.write(f'  📁 {cat.name}')

            for sub_data in cat_data.get('subcategories', []):
                sub, _ = SubCategory.objects.get_or_create(
                    category=cat,
                    slug=slugify(sub_data['name']),
                    defaults={'name': sub_data['name'], 'icon': sub_data['icon']}
                )

                for prod_data in sub_data.get('products', []):
                    prod, created = BoycottProduct.objects.get_or_create(
                        slug=slugify(prod_data['name']),
                        defaults={
                            'subcategory': sub,
                            'name': prod_data['name'],
                            'brand': prod_data['brand'],
                            'reason': prod_data['reason'],
                            'logo_url': prod_data.get('logo_url', ''),
                        }
                    )
                    if created:
                        self.stdout.write(f'    🚫 {prod.name}')
                        for alt_data in prod_data.get('alternatives', []):
                            PakistaniAlternative.objects.get_or_create(
                                product=prod,
                                name=alt_data['name'],
                                defaults={
                                    'brand': alt_data['brand'],
                                    'description': alt_data.get('description', ''),
                                    'website': alt_data.get('website', ''),
                                    'status': 'approved',
                                }
                            )

        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
        self.stdout.write(f"   Categories: {Category.objects.count()}")
        self.stdout.write(f"   SubCategories: {SubCategory.objects.count()}")
        self.stdout.write(f"   Boycott Products: {BoycottProduct.objects.count()}")
        self.stdout.write(f"   Pakistani Alternatives: {PakistaniAlternative.objects.count()}")
