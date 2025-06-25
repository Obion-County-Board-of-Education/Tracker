# 👥 Team Development Guide
**OCS Tracker - Local Development Setup**

## 🚀 Quick Start (5 minutes)

### Option 1: Simple Local Setup (Recommended for beginners)
```powershell
# 1. Clone the repository
git clone <repository-url>
cd Tracker

# 2. Set up development environment
python setup_dev_environment.py

# 3. Start the portal
cd ocs-portal-py
python main.py
```

### Option 2: Docker Setup (Recommended for consistent environments)
```powershell
# 1. Clone and start all services
git clone <repository-url>
cd Tracker
docker-compose -f docker-compose.dev.yml up

# Portal will be available at http://localhost:8080
```

## 📊 Database Development Strategies

### 1. **Shared Sample Data**
Everyone runs the same data setup script:
```powershell
python setup_dev_data.py
```
This creates identical test data across all developer machines.

### 2. **Database Snapshots**
Share database state via SQL dumps:
```powershell
# Create snapshot (team lead)
sqlite3 tracker_dev.db .dump > dev_snapshot.sql

# Apply snapshot (team members)
sqlite3 tracker_dev.db < dev_snapshot.sql
```

### 3. **Migrations & Versioning**
Track database changes with migration scripts:
```
/migrations/
  001_initial_setup.sql
  002_add_closed_count_feature.sql
  003_add_building_rooms.sql
```

## 🔄 Development Workflow

### Daily Workflow:
1. **Pull latest changes**: `git pull origin main`
2. **Update database**: `python setup_dev_data.py` (if needed)
3. **Start development**: `python main.py`
4. **Test changes**: Visit http://localhost:8080
5. **Commit & push**: Standard git workflow

### When Adding New Features:
1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Update database schema** (if needed)
3. **Update `setup_dev_data.py`** with new sample data
4. **Test locally**
5. **Create pull request**

## 🧪 Testing Strategy

### Manual Testing Checklist:
- [ ] Tech tickets (create, view, update, close)
- [ ] Maintenance tickets (create, view, update, close)
- [ ] CSV import/export functionality
- [ ] Closed ticket counter display
- [ ] Building/room selection

### Automated Testing:
```powershell
# Run all tests
python run_all_tests.py

# Test specific functionality
python test_closed_counter.py
python test_csv_import.py
```

## 📁 Project Structure Understanding

```
Tracker/
├── ocs-portal-py/          # Main FastAPI web portal
│   ├── main.py             # Web routes & UI
│   ├── services.py         # API communication
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, images
├── ocs-tickets-api/        # Backend API
│   ├── main.py             # API endpoints
│   └── database.py         # Database connection
├── ocs_shared_models/      # Database models (shared)
├── setup_dev_data.py       # Development data setup
└── docker-compose.dev.yml  # Docker development environment
```

## 🔧 Common Issues & Solutions

### Issue: "Cannot import purchasing_service"
**Solution**: Service instances not created
```python
# Add to services.py
purchasing_service = PurchasingService()
```

### Issue: Database changes not reflected
**Solution**: Recreate development database
```powershell
python setup_dev_data.py
```

### Issue: Port already in use
**Solution**: Check running processes
```powershell
netstat -ano | findstr :8080
# Kill process if needed
taskkill /PID <process-id> /F
```

### Issue: Different team members see different data
**Solution**: Ensure everyone runs the same setup script
```powershell
# Everyone should run this after pulling changes
python setup_dev_data.py
```

## 🌟 Best Practices

### For Individual Developers:
1. **Always pull before starting work**
2. **Run setup script after pulling database changes**
3. **Test your changes locally before committing**
4. **Use descriptive commit messages**
5. **Keep your local database in sync**

### For Feature Development:
1. **Small, focused commits**
2. **Update sample data for new features**
3. **Include tests when possible**
4. **Document new functionality**
5. **Test the closed ticket counter feature**

### For Database Changes:
1. **Update shared models first**
2. **Update setup script with new sample data**
3. **Create migration script if needed**
4. **Test with clean database**
5. **Coordinate with team on major changes**

## 🎯 Current Features to Test

### Closed Ticket Counter Feature:
- Navigate to Tech Tickets → Open
- Should see counter showing number of closed tickets
- Navigate to Tech Tickets → Closed
- Counter should NOT appear
- Same behavior for Maintenance tickets

### CSV Import/Export:
- Export tickets to CSV
- Import tickets from CSV
- Verify data integrity

## 📞 Getting Help

1. **Check this guide first**
2. **Run diagnostic scripts**: `python test_portal_startup.py`
3. **Check common issues section**
4. **Ask team lead for database snapshot**
5. **Review recent commits for changes**

---
*Last updated: June 2025*
