# 🇵🇰 Pakistan Boycott Alternatives

A community-driven platform that helps Pakistanis find local alternatives to products on boycott lists. Users can suggest alternatives, which are reviewed by admins before publication.

## 🎯 Purpose

This platform empowers Pakistani consumers to make informed choices by:
- Providing a curated list of products to boycott
- Offering verified local Pakistani alternatives
- Building a community-driven database of alternatives
- Supporting local businesses and industries

## ✨ Features

### For All Users (Public)
- 🔍 Browse boycott products and their local alternatives
- 📊 View product details, categories, and ratings
- 🔎 Search and filter products
- 📱 Fully responsive design

### For Registered Users
- ➕ Suggest new alternatives for existing boycott products
- 📝 Propose new boycott products to add
- ⭐ Rate and review alternatives
- 📋 Track your suggested alternatives

### For Super Admins
- ✅ Review and approve/reject user-submitted alternatives
- 📝 Manage product listings
- 👥 User management
- 📊 Dashboard with analytics
- ⚡ Quick moderation queue

## 📋 Prerequisites

- Python 3.8+
- pip
- Git

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/pakistan-boycott-alternatives.git
cd pakistan-boycott-alternatives
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## 🔒 User Roles

| Role | Permissions |
|------|-------------|
| **Visitor** | View products and alternatives |
| **Registered User** | Suggest alternatives, vote, comment |
| **Superuser/Admin** | Review suggestions, manage all content |
| **Moderator** | Review and moderate content |

## 🔄 Moderation Workflow

1. **User Submits** alternative suggestion
2. **Pending Review** - Appears in admin queue
3. **Admin Reviews** - Checks accuracy and quality
4. **Status Updates**:
   - ✅ Approved → Published publicly
   - ❌ Rejected → Removed with feedback
   - ⏳ Pending → Awaiting review
5. **User Notified** via email/dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Django community
- Bootstrap team
- All contributors and users
- Pakistani local businesses

## 🌟 Support

If you find this project useful, please:
- ⭐ Star the repository
- 🐛 Report issues
- 🤝 Contribute code
- 📢 Share with others

---

**🇵🇰 Made with ❤️ for Pakistan**
```
