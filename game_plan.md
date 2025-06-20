# OCS Tracker Development Game Plan

## Overview
Comprehensive strategy for implementing a robust, role-based OCS (Office of Computer Services) management system with Azure AD authentication and full inventory tracking capabilities.

---

## 🔐 Authentication & Authorization Strategy

### Current Implementation Status: ✅ **COMPLETE**
- **Azure AD Integration**: Single sign-on with Microsoft Azure Active Directory
- **Role-Based Access Control**: Dynamic content filtering based on user permissions
- **GroupRole System**: Automatic initialization of essential group roles
  - `All_Staff`: Staff access (tickets + purchasing)
  - `All_Students`: Student access (tickets only)
  - `Technology Department`: Super admin access (all systems)
  - `Finance`: Admin access (purchasing + forms + reports)
  - `Director of Schools`: Super admin via extensionAttribute10

### Design Principles
- **Azure AD as Single Source of Truth** for authentication and authorization
- **Real-time Permission Checking** via Azure Graph API
- **No Local Password Storage** - all authentication through Microsoft
- **Dynamic UI Adaptation** based on user's actual permissions

---

## 👥 User Management Strategy

### **Hybrid Approach: Azure AD + Local Database**

#### **For Authentication & Permissions**
- ✅ **Use Azure AD Only**
  - Real-time group membership checking
  - No sync issues for access control
  - Automatic updates when users change roles
  - Simplified IT management

#### **For Business Data & Relationships**
- 🔄 **Sync Users to Local Database**
  - **Why**: Equipment assignments, room relationships, audit trails
  - **Who**: ALL Azure AD users (staff, students, contractors, substitutes)
  - **When**: Scheduled daily sync + real-time critical updates

### **User Sync Requirements**

#### **Staff Users**
- Sync Method: Hybrid (login-based + scheduled)
- Data Needs: Full profile for equipment assignments
- Update Frequency: Real-time on login + daily batch

#### **Student Users**
- Sync Method: Scheduled only (many never log in)
- Data Needs: Basic profile for device assignments
- Update Frequency: Daily sync (especially during enrollment periods)
- Use Cases: iPad programs, laptop assignments, classroom equipment

#### **Temporary/Substitute Users**
- Sync Method: Scheduled with rapid provisioning
- Data Needs: Basic profile + temporary equipment needs
- Update Frequency: Daily with quick activation/deactivation

---

## 🏢 Database Design Strategy

### **Shared Models Architecture**
- ✅ **Central `ocs_shared_models` package** for all database definitions
- ✅ **Service-specific databases** within single PostgreSQL instance
- ✅ **Modular microservices** architecture with shared data layer

### **Core Entity Relationships**

```
Users (from Azure AD sync)
├── Equipment Assignments
├── Room Assignments  
├── Ticket Submissions
├── Purchase Requisitions
└── Historical Records

Buildings
├── Rooms
│   ├── Equipment Locations
│   └── User Assignments
└── Department Mappings

Equipment
├── Assignment History
├── Maintenance Records
├── Purchase Information
└── Warranty Tracking

GroupRoles (permission definitions)
├── Access Level Mappings
├── Service Permissions
└── Department Restrictions
```

---

## 📊 Service Architecture

### **Current Services**
- ✅ **ocs-portal-py**: Main dashboard and authentication hub
- ✅ **ocs-tickets-api**: Help desk and support tickets
- ✅ **ocs-purchasing-api**: Purchase requisitions and approvals
- ✅ **ocs-forms-api**: Digital forms and submissions
- ✅ **ocs-manage-api**: Administrative functions and inventory management

### **Service Permissions Matrix**

| User Group | Tickets | Purchasing | Inventory | Forms | Management |
|------------|---------|------------|-----------|-------|------------|
| All_Students | Write | None | None | None | None |
| All_Staff | Read/Write | Read/Write | None | None | None |
| Finance | Read/Write | Admin | Read | Admin | Limited |
| Technology Dept | Admin | Admin | Admin | Admin | Full |
| Director of Schools | Admin | Admin | Admin | Admin | Full |

---

## 🔄 User Synchronization Implementation

### **Sync Strategy**

#### **Daily Scheduled Sync**
- **Scope**: All Azure AD users (active and recently disabled)
- **Data**: Basic profile, department, grade level (students), status
- **Process**: Incremental sync with change detection
- **Timing**: Off-hours to minimize system impact

#### **Real-time Updates**
- **Triggers**: User login, critical permission changes
- **Scope**: Individual user profile updates
- **Data**: Authentication-related info, recent activity

#### **Soft Delete Approach**
- **Departed Users**: Mark as inactive, preserve all historical data
- **Equipment History**: Maintain complete audit trail
- **Compliance**: Support regulatory requirements for data retention

### **Sync Data Model**

#### **Essential User Fields**
```
User Table:
- azure_object_id (primary key)
- email (unique)
- display_name
- first_name, last_name
- department
- employee_id / student_id
- grade_level (students only)
- status (active/inactive/disabled)
- last_sync_date
- created_date
- updated_date
```

#### **Relationship Tables**
```
Equipment_Assignments:
- user_id → equipment_id
- assigned_date, returned_date
- condition_notes
- assigned_by_user_id

Room_Assignments:
- user_id → room_id (office, classroom)
- assignment_type (primary, temporary)
- start_date, end_date

User_Groups: (for audit/reporting)
- user_id → group_name
- assigned_date, removed_date
```

---

## 🎯 Implementation Phases

### **Phase 1: Foundation** ✅ **COMPLETE**
- [x] Azure AD authentication
- [x] Basic role-based access control
- [x] GroupRole automatic initialization
- [x] Service-specific databases
- [x] Dynamic dashboard filtering

### **Phase 2: User Management** 🔄 **IN PROGRESS**
- [ ] Implement Azure Graph API user sync
- [ ] Create user management tables
- [ ] Build scheduled sync job
- [ ] Add user profile management UI
- [ ] Implement soft delete for departed users

### **Phase 3: Inventory Core** 📋 **PLANNED**
- [ ] Equipment catalog and tracking
- [ ] Room and location management
- [ ] Basic assignment workflows
- [ ] Equipment check-in/check-out
- [ ] Asset lifecycle tracking

### **Phase 4: Advanced Features** 🚀 **FUTURE**
- [ ] Bulk equipment operations
- [ ] Advanced reporting and analytics
- [ ] Mobile device management integration
- [ ] Automated compliance reporting
- [ ] Equipment maintenance scheduling

---

## 🔧 Technical Considerations

### **Performance Optimization**
- **Caching Strategy**: Cache Azure AD group memberships for short periods
- **Database Indexing**: Optimize for common equipment/user lookup patterns
- **API Rate Limiting**: Respect Microsoft Graph API throttling limits
- **Batch Operations**: Support bulk equipment assignments

### **Security & Compliance**
- **Data Privacy**: Minimal user data storage, FERPA compliance
- **Audit Trails**: Complete history of equipment assignments and access
- **Access Logging**: Track who accessed what equipment data when
- **Backup Strategy**: Regular backups with point-in-time recovery

### **Scalability Planning**
- **User Growth**: Support district expansion and enrollment changes
- **Equipment Volume**: Handle thousands of devices and assets
- **Seasonal Loads**: Handle back-to-school equipment deployment cycles
- **Multi-Building**: Scale across multiple school locations

---

## 📈 Success Metrics

### **User Experience**
- Single sign-on adoption rate
- Time to complete common tasks (ticket submission, equipment checkout)
- User satisfaction with role-appropriate interface

### **Operational Efficiency**
- Reduction in IT support requests
- Equipment accountability improvement
- Time savings in inventory management
- Automated compliance reporting accuracy

### **System Performance**
- Authentication response times
- Database query performance
- Sync job completion times
- System uptime and reliability

---

## 🎯 Next Immediate Steps

1. **User Sync Implementation**
   - Set up Microsoft Graph API permissions
   - Create sync job infrastructure
   - Implement incremental sync logic

2. **Equipment Data Model**
   - Design equipment catalog structure
   - Create assignment tracking tables
   - Build basic CRUD operations

3. **Testing & Validation**
   - Test sync with real Azure AD data
   - Validate permission inheritance
   - Verify equipment assignment workflows

---

*This game plan provides a comprehensive roadmap for building a robust, scalable OCS management system that leverages Azure AD for security while maintaining the flexibility needed for complex inventory and equipment management requirements.*
