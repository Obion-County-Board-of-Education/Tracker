# 👥 OCS Tracker User Import System

<p align="center">
  <img src="ocs-portal-py/static/ocs-logo.png" alt="OCS Logo" width="120"/>
</p>

<h3 align="center" style="color: #6a1b9a;">Microsoft Graph User Import & Management System</h3>

---

## 📋 Overview

This document outlines the implementation plan for importing users from Azure AD groups (`All_Staff` and `All_Students`) into the OCS Tracker database system. This will enable comprehensive user management, requisition workflows, and system administration capabilities.

### **Current Status: 🎯 IMPLEMENTATION READY**
- ✅ Authentication system fully operational
- ✅ Group-based permissions established
- ✅ Microsoft Graph API integration active
- ✅ **NEW**: User import service implemented
- ✅ **NEW**: Database schema migration ready
- ✅ **NEW**: Admin interface created
- ✅ **NEW**: API endpoints implemented
- 🎯 **NEXT**: Run database migration and test imports
- 🎯 **GOAL**: Complete user database with requisition workflows

---

## ✅ **IMPLEMENTATION STATUS UPDATE**

### **🎯 Phase 1: User Import System - COMPLETED**

The user import system has been successfully implemented and is ready for deployment:

#### **📁 New Files Created:**
- `ocs-portal-py/user_import_service.py` - Core Azure AD import service
- `ocs-portal-py/user_import_routes.py` - FastAPI API endpoints  
- `ocs-portal-py/templates/user_management.html` - Admin web interface
- `ocs-portal-py/migrate_user_tables.py` - Database migration script
- `ocs-portal-py/test_user_import.py` - Test suite for validation
- `setup_user_import.ps1` - PowerShell setup script

#### **🔧 Updated Files:**
- `ocs_shared_models/models.py` - Extended User model with Azure AD fields
- `ocs-portal-py/main.py` - Added user import routes and admin page
- `users_import.md` - Updated status and implementation details

#### **🚀 Ready Features:**
- ✅ **Azure AD Integration**: Import from All_Staff and All_Students groups
- ✅ **User Management Interface**: Modern web UI with search and filtering
- ✅ **Database Migration**: Automated schema updates for existing systems
- ✅ **API Endpoints**: RESTful APIs for all import operations
- ✅ **Department Management**: Automatic department assignment and tracking
- ✅ **Background Processing**: Non-blocking imports for large user sets
- ✅ **Error Handling**: Comprehensive error tracking and reporting
- ✅ **Security**: Super admin access control and audit logging

#### **📋 Quick Start Instructions:**
1. **Run Setup Script** (PowerShell):
   ```powershell
   .\setup_user_import.ps1
   ```
2. **Manual Setup** (Alternative):
   ```bash
   # Start services
   docker-compose up -d
   
   # Run database migration
   docker-compose exec ocs-portal-py python migrate_user_tables.py
   
   # Test the system
   docker-compose exec ocs-portal-py python test_user_import.py
   ```
3. **Access User Management**:
   - URL: http://localhost:8080/admin/users
   - Requires: Super admin login
   - Features: Import, search, view, and manage users

#### **🎯 Next Phase Ready:**
With Phase 1 complete, the system is ready to proceed to Phase 2 (Requisition System) with a solid foundation of imported users and established organizational hierarchy.

---

## 🎯 Import Objectives

### **Primary Goals**
1. **User Database Population**: Import all staff and students from Azure AD
2. **Profile Management**: Sync user profiles with organizational data
3. **Department Assignment**: Map users to appropriate departments/buildings
4. **Requisition System**: Enable staff to submit purchase requests
5. **Management Hierarchy**: Establish approval workflows
6. **Inventory Management**: Tie inventory items to users and rooms
7. **Asset Tracking**: Complete asset lifecycle management system

### **Business Benefits**
- Complete user directory for system administration
- Streamlined requisition and approval processes
- Automated user role assignment and permissions
- Integration with existing OCS organizational structure
- Audit trail for user management and requests
- **Comprehensive asset tracking** tied to users and locations
- **Inventory accountability** with assignment history
- **Space management** with room-based asset organization
- **Lifecycle tracking** from requisition to disposal

---

## 🏗️ Database Schema Extensions

### **New Tables Required**

#### **users**
Complete user directory from Azure AD
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    azure_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    user_principal_name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    given_name VARCHAR(100),
    surname VARCHAR(100),
    job_title VARCHAR(255),
    department VARCHAR(255),
    office_location VARCHAR(255),
    employee_id VARCHAR(50),
    employee_type VARCHAR(50), -- Staff, Student, Faculty
    manager_id VARCHAR(255), -- References another user's azure_user_id
    building_assignment VARCHAR(255),
    grade_level VARCHAR(10), -- For students
    user_type VARCHAR(20) NOT NULL, -- staff, student, admin
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **user_departments**
Department assignments and hierarchies
```sql
CREATE TABLE user_departments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    department_name VARCHAR(255) NOT NULL,
    building_name VARCHAR(255),
    is_primary BOOLEAN DEFAULT true,
    role_in_department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **purchase_requisitions**
Staff purchase request system with multi-stage approval workflow
```sql
CREATE TABLE purchase_requisitions (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER REFERENCES users(id) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    justification TEXT,
    total_amount DECIMAL(10,2),
    budget_code VARCHAR(50),
    department VARCHAR(255),
    building VARCHAR(255),
    vendor_preference VARCHAR(255),
    requested_delivery_date DATE,
    
    -- Multi-stage approval workflow status
    current_stage VARCHAR(50) DEFAULT 'supervisor', -- supervisor/finance_director/director_of_schools/po_entry/completed
    overall_status VARCHAR(50) DEFAULT 'pending', -- pending/approved/rejected/returned
    
    -- Stage 1: Supervisor Approval
    supervisor_email VARCHAR(255),
    supervisor_status VARCHAR(20) DEFAULT 'pending', -- pending/approved/rejected
    supervisor_approved_at TIMESTAMP,
    supervisor_comments TEXT,
    
    -- Stage 2: Finance Director Approval
    finance_director_status VARCHAR(20) DEFAULT 'pending',
    finance_director_approved_at TIMESTAMP,
    finance_director_comments TEXT,
    
    -- Stage 3: Director of Schools Approval
    director_schools_status VARCHAR(20) DEFAULT 'pending',
    director_schools_approved_at TIMESTAMP,
    director_schools_comments TEXT,
    
    -- Stage 4: PO Entry
    po_entered_by INTEGER REFERENCES users(id),
    po_number VARCHAR(50),
    po_entered_at TIMESTAMP,
    
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

#### **requisition_items**
Individual items in purchase requests
```sql
CREATE TABLE requisition_items (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER REFERENCES purchase_requisitions(id),
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    vendor VARCHAR(255),
    part_number VARCHAR(100),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **organizational_hierarchy**
Staff reporting structure for approval workflows
```sql
CREATE TABLE organizational_hierarchy (
    id SERIAL PRIMARY KEY,
    employee_email VARCHAR(255) UNIQUE NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    supervisor_email VARCHAR(255), -- References another employee_email
    department VARCHAR(255),
    building VARCHAR(255),
    position_title VARCHAR(255),
    is_supervisor BOOLEAN DEFAULT false,
    is_finance_director BOOLEAN DEFAULT false,
    is_director_of_schools BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **approval_notifications**
Notification tracking for workflow stages
```sql
CREATE TABLE approval_notifications (
    id SERIAL PRIMARY KEY,
    requisition_id INTEGER REFERENCES purchase_requisitions(id),
    recipient_email VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- pending_approval/approved/rejected/completed
    stage VARCHAR(50), -- supervisor/finance_director/director_of_schools/po_entry
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **inventory_items**
Complete inventory management system (updated to include legacy field mapping)
```sql
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    
    -- Core identification (maps from legacy 'tag', 'type', 'brand', 'model', 'serial')
    asset_tag VARCHAR(100) UNIQUE, -- Legacy: 'tag'
    item_name VARCHAR(255) NOT NULL, -- Legacy: 'type' 
    description TEXT,
    category VARCHAR(100), -- Technology, Furniture, Equipment, Supplies
    subcategory VARCHAR(100),
    brand VARCHAR(100), -- Legacy: 'brand'
    model VARCHAR(100), -- Legacy: 'model'
    serial_number VARCHAR(255), -- Legacy: 'serial'
    
    -- Purchase and financial information (maps from legacy 'po', 'price', 'funds', 'vendor')
    purchase_date DATE, -- Legacy: 'install' (installation date as purchase proxy)
    purchase_price DECIMAL(10,2), -- Legacy: 'price'
    po_number VARCHAR(100), -- Legacy: 'po'
    vendor VARCHAR(255), -- Legacy: 'vendor'
    funding_source VARCHAR(255), -- Legacy: 'funds'
    warranty_expiration DATE,
    
    -- Location tracking (maps from legacy 'school', 'room')
    school_assignment VARCHAR(255), -- Legacy: 'school'
    legacy_room VARCHAR(100), -- Legacy: 'room' (before room normalization)
    assigned_to_user_id INTEGER REFERENCES users(id), -- Current user assignment
    assigned_to_room_id INTEGER REFERENCES rooms(id), -- Current room assignment (normalized)
    assignment_type VARCHAR(50), -- user_assigned/room_assigned/unassigned/disposed
    assignment_date TIMESTAMP,
    
    -- Lifecycle and condition (maps from legacy 'condition', 'dispose')
    status VARCHAR(50) DEFAULT 'active', -- active/maintenance/retired/disposed/lost
    condition_rating VARCHAR(20) DEFAULT 'good', -- Legacy: 'condition' (excellent/good/fair/poor/damaged)
    install_date DATE, -- Legacy: 'install'
    disposal_date DATE, -- Legacy: 'dispose'
    
    -- Financial compliance and ownership (maps from legacy 'funding_percentage', 'titleholder', 'use', 'fain')
    funding_percentage DECIMAL(5,2), -- Legacy: 'funding_percentage' (federal funding percentage)
    title_holder VARCHAR(255), -- Legacy: 'titleholder' (legal ownership entity)
    usage_type VARCHAR(100), -- Legacy: 'use' (intended use classification)
    federal_award_id VARCHAR(100), -- Legacy: 'fain' (Federal Award Identification Number)
    last_inspection_date DATE,
    next_inspection_due DATE,
    
    -- Financial tracking
    depreciation_rate DECIMAL(5,2), -- Annual depreciation percentage
    current_value DECIMAL(10,2),
    replacement_cost DECIMAL(10,2),
    
    -- Administrative
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **inventory_assignments**
Assignment history and tracking
```sql
CREATE TABLE inventory_assignments (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER REFERENCES inventory_items(id),
    assigned_to_user_id INTEGER REFERENCES users(id),
    assigned_to_room_id INTEGER REFERENCES rooms(id),
    assignment_type VARCHAR(50) NOT NULL, -- user_checkout/room_placement/transfer/return
    assignment_reason TEXT,
    
    -- Assignment period
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id) NOT NULL,
    expected_return_date DATE,
    returned_at TIMESTAMP,
    returned_by INTEGER REFERENCES users(id),
    return_condition VARCHAR(20), -- same_condition/wear_noted/damaged/lost
    return_notes TEXT,
    
    -- Status tracking
    is_current_assignment BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **rooms**
Room and location management (integration with existing buildings/rooms)
```sql
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    room_number VARCHAR(50) NOT NULL,
    room_name VARCHAR(255),
    building_id INTEGER REFERENCES buildings(id),
    floor_number INTEGER,
    room_type VARCHAR(100), -- classroom/office/lab/storage/common_area
    capacity INTEGER,
    
    -- Room details
    square_footage DECIMAL(8,2),
    room_manager_id INTEGER REFERENCES users(id), -- Primary responsible person
    department VARCHAR(255),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_inventory_date DATE,
    next_inventory_due DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **inventory_transactions**
Complete audit trail for all inventory movements
```sql
CREATE TABLE inventory_transactions (
    id SERIAL PRIMARY KEY,
    inventory_item_id INTEGER REFERENCES inventory_items(id),
    transaction_type VARCHAR(50) NOT NULL, -- purchase/assignment/transfer/maintenance/disposal/audit
    
    -- Transaction details
    from_user_id INTEGER REFERENCES users(id),
    to_user_id INTEGER REFERENCES users(id),
    from_room_id INTEGER REFERENCES rooms(id),
    to_room_id INTEGER REFERENCES rooms(id),
    
    -- Administrative
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by INTEGER REFERENCES users(id) NOT NULL,
    notes TEXT,
    reference_number VARCHAR(100), -- PO number, work order, etc.
    
    -- Financial impact
    cost_amount DECIMAL(10,2),
    budget_code VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 Implementation Plan

### **Phase 1: Microsoft Graph User Import (Week 1)**

#### **Step 1.1: Extend Authentication Service**
```python
# File: ocs-portal-py/user_import_service.py
class UserImportService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
    
    async def import_all_staff(self):
        """Import all users from All_Staff Azure AD group"""
        pass
    
    async def import_all_students(self):
        """Import all users from All_Students Azure AD group"""
        pass
    
    async def sync_user_profiles(self):
        """Sync existing user profiles with latest Azure AD data"""
        pass
```

#### **Step 1.2: Graph API Group Members Endpoint**
- Endpoint: `https://graph.microsoft.com/v1.0/groups/{group-id}/members`
- Required permissions: `GroupMember.Read.All`, `User.Read.All`
- Batch processing for large user sets (up to 100 users per request)

#### **Step 1.3: User Data Mapping**
```python
# Azure AD fields to database mapping
user_mapping = {
    'id': 'azure_user_id',
    'userPrincipalName': 'user_principal_name',
    'mail': 'email',
    'displayName': 'display_name',
    'givenName': 'given_name',
    'surname': 'surname',
    'jobTitle': 'job_title',
    'department': 'department',
    'officeLocation': 'office_location',
    'employeeId': 'employee_id',
    'employeeType': 'employee_type'
}
```

### **Phase 2: User Management Interface (Week 2)**

#### **Step 2.1: Admin User Management Pages**
```
/admin/users/
├── list - View all imported users with search/filter
├── import - Trigger manual import from Azure AD
├── sync - Sync existing users with Azure AD updates
├── departments - Manage department assignments
└── export - Export user data for reporting
```

#### **Step 2.2: User Profile Integration**
- Link user profiles to existing ticket system
- Display user information in ticket creation
- Auto-populate user details in forms
- Building/department-based filtering

#### **Step 2.3: Permission Updates**
```python
# Update auth_middleware.py to use imported user data
def get_user_profile(azure_user_id: str) -> User:
    """Get complete user profile from database"""
    return db.query(User).filter(User.azure_user_id == azure_user_id).first()
```

### **Phase 3: Purchase Requisition System (Week 3)**
*📋 Full workflow details available in: [req_approval.md](req_approval.md)*

#### **Step 3.1: Multi-Stage Approval Workflow**
**4-Stage Approval Process**: Staff → Supervisor → Finance Director → Director of Schools → PO Entry

```
/requisitions/
├── create - New purchase request form
├── my-requests - User's submitted requests
├── pending-approval - Requests awaiting current user's approval
├── approved - Approved requests ready for PO
├── rejected - Rejected requests with feedback
├── completed - Completed requisitions with PO numbers
└── reports - Requisition analytics and audit trails
```

#### **Step 3.2: Advanced Approval Workflow Engine**
```python
# File: ocs-portal-py/requisition_service.py
class RequisitionService:
    def __init__(self, db: Session):
        self.db = db
    
    def determine_approval_chain(self, requisition: PurchaseRequisition) -> Dict[str, str]:
        """Determine 4-stage approval chain based on organizational hierarchy"""
        # Stage 1: Direct Supervisor (auto-approve if self-supervisor)
        # Stage 2: Finance Director (budget/financial review)
        # Stage 3: Director of Schools (final executive approval)
        # Stage 4: Finance Staff (PO creation)
        pass
    
    def submit_for_approval(self, requisition_id: int) -> bool:
        """Initiate multi-stage approval workflow"""
        pass
    
    def process_stage_approval(self, requisition_id: int, stage: str, approver_id: int, 
                              decision: str, comments: str = None) -> bool:
        """Process approval/rejection at specific workflow stage"""
        pass
    
    def handle_self_supervision(self, requisition: PurchaseRequisition) -> bool:
        """Auto-approve supervisor stage if submitter is their own supervisor"""
        pass
    
    def escalate_to_next_stage(self, requisition_id: int) -> bool:
        """Move requisition to next approval stage"""
        pass
```

#### **Step 3.3: Comprehensive Notification System**
**Automated Email Notifications**:
- **Pending Approval**: Notification to current stage approver
- **Stage Approved**: Update to submitter and previous approvers
- **Requisition Rejected**: Detailed feedback to submitter
- **Workflow Completed**: PO number and completion details
- **Reminder Notifications**: 24/48 hour approval reminders
- **Override Alerts**: Admin override notifications for audit trail

### **Phase 4: Inventory Management System (Week 4)**

#### **Step 4.1: Asset Tracking Integration**
```
/admin/inventory/
├── items - View and manage all inventory items
├── assignments - Current user and room assignments
├── checkout - Assign items to users or rooms
├── checkin - Return items and update condition
├── transfers - Move items between users/rooms
├── audit - Inventory auditing and reconciliation
├── reports - Asset reports and analytics
└── import - Bulk import inventory from spreadsheets
```

#### **Step 4.2: User-Inventory Integration**
```python
# File: ocs-portal-py/inventory_service.py
class InventoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def assign_item_to_user(self, item_id: int, user_id: int, assigned_by: int, 
                           reason: str = None, expected_return: date = None) -> bool:
        """Assign inventory item to specific user"""
        pass
    
    def assign_item_to_room(self, item_id: int, room_id: int, assigned_by: int,
                           reason: str = None) -> bool:
        """Assign inventory item to specific room/location"""
        pass
    
    def transfer_item(self, item_id: int, from_user: int = None, to_user: int = None,
                     from_room: int = None, to_room: int = None, 
                     transferred_by: int, reason: str = None) -> bool:
        """Transfer item between users or rooms"""
        pass
    
    def return_item(self, assignment_id: int, returned_by: int, 
                   condition: str, notes: str = None) -> bool:
        """Process item return and update condition"""
        pass
    
    def get_user_inventory(self, user_id: int) -> List[InventoryItem]:
        """Get all items currently assigned to user"""
        pass
    
    def get_room_inventory(self, room_id: int) -> List[InventoryItem]:
        """Get all items currently assigned to room"""
        pass
    
    def generate_asset_tag(self, category: str) -> str:
        """Generate unique asset tag based on category and sequence"""
        pass
```

#### **Step 4.3: Room Management Integration**
```python
# File: ocs-portal-py/room_service.py
class RoomService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_room(self, room_data: RoomCreate, created_by: int) -> Room:
        """Create new room/location entry"""
        pass
    
    def update_room_manager(self, room_id: int, manager_user_id: int) -> bool:
        """Assign room manager (responsible person)"""
        pass
    
    def schedule_room_inventory(self, room_id: int, scheduled_date: date,
                               scheduled_by: int) -> bool:
        """Schedule physical inventory audit for room"""
        pass
    
    def get_room_assignments(self, room_id: int) -> Dict:
        """Get all current assignments for room (users + inventory)"""
        pass
    
    def get_user_room_responsibilities(self, user_id: int) -> List[Room]:
        """Get rooms where user is designated manager"""
        pass
```

### **Phase 5: Management & Reporting (Week 5)**

#### **Step 5.1: Administrative Dashboard**
- User import status and statistics
- Pending requisitions requiring approval
- Department spending summaries
- User activity reports
- **Inventory assignment overview**
- **Asset utilization metrics**
- **Room occupancy and inventory status**

#### **Step 5.2: Financial Integration**
- Budget tracking per department
- Spending analytics and reports
- Purchase order generation
- Vendor management integration
- **Asset depreciation tracking**
- **Replacement cost projections**
- **Total cost of ownership analysis**

#### **Step 5.3: Compliance & Audit**
- User access logging
- Requisition approval audit trail
- Department spending compliance
- Annual reporting capabilities
- **Inventory audit trails**
- **Asset accountability reports**
- **Missing/damaged item tracking**

---

## 🏢 Inventory Management System Integration

### **Asset-User-Room Relationship Model**

The inventory management system creates a comprehensive relationship between:
- **Users** (staff and students from Azure AD)
- **Inventory Items** (all physical assets)
- **Rooms** (physical locations and spaces)

#### **🔗 Core Relationships**

```mermaid
erDiagram
    USERS ||--o{ INVENTORY_ASSIGNMENTS : "assigned_to"
    ROOMS ||--o{ INVENTORY_ASSIGNMENTS : "located_in"
    INVENTORY_ITEMS ||--|| INVENTORY_ASSIGNMENTS : "tracks"
    USERS ||--o{ ROOMS : "manages"
    PURCHASE_REQUISITIONS ||--o{ INVENTORY_ITEMS : "creates"
    
    USERS {
        int id PK
        string azure_user_id
        string email
        string display_name
        string department
        string building_assignment
    }
    
    ROOMS {
        int id PK
        string room_number
        string room_name
        int building_id
        int room_manager_id FK
        string room_type
    }
    
    INVENTORY_ITEMS {
        int id PK
        string asset_tag
        string item_name
        string category
        int assigned_to_user_id FK
        int assigned_to_room_id FK
        string status
    }
    
    INVENTORY_ASSIGNMENTS {
        int id PK
        int inventory_item_id FK
        int assigned_to_user_id FK
        int assigned_to_room_id FK
        datetime assigned_at
        datetime returned_at
        boolean is_current_assignment
    }
```

#### **📋 Asset Tracking Scenarios**

**Scenario 1: Technology Equipment Assignment**
- **Item**: Laptop (Asset Tag: TECH-2025-001)
- **Assigned To**: Teacher (Ms. Johnson)
- **Located In**: Room 205 (Ms. Johnson's classroom)
- **Tracking**: User checkout with room as secondary location

**Scenario 2: Shared Room Equipment**
- **Item**: Projector (Asset Tag: AV-2025-015)
- **Assigned To**: Room 105 (Conference Room)
- **Manager**: Principal (Mr. Davis)
- **Tracking**: Room-based assignment with responsible manager

**Scenario 3: Mobile Equipment**
- **Item**: iPad Cart (Asset Tag: MOBILE-2025-003)
- **Assigned To**: Technology Coordinator (IT Staff)
- **Usage**: Transfers between classrooms as needed
- **Tracking**: User assignment with location history

#### **🔧 Management Features**

**User Inventory Management:**
- View all items assigned to a specific user
- Check out equipment to users with return dates
- Track user responsibility and accountability
- Generate user equipment reports

**Room Inventory Management:**
- View all items located in a specific room
- Assign room managers for accountability
- Schedule regular room inventory audits
- Track room utilization and capacity

**Asset Lifecycle Tracking:**
- From requisition approval to purchase
- Initial assignment and deployment
- Transfers and reassignments
- Maintenance and repair history
- Retirement and disposal

#### **🔐 Security & Permissions**

**Inventory Access Levels:**
- **Technology Department**: Full inventory management across all locations
- **Finance**: Asset tracking for financial reporting and audits
- **Room Managers**: View and manage inventory in their assigned rooms
- **Staff Users**: View their personally assigned equipment
- **Students**: Limited visibility to checked-out items only

**Assignment Authority:**
- **Super Admin**: Can assign/transfer any item to any user/room
- **Department Heads**: Can manage assignments within their department
- **Room Managers**: Can manage items within their rooms
- **IT Staff**: Technology equipment assignments and transfers

---

## 📋 Requisition Approval Workflow Reference

### **Integration with req_approval.md**
This implementation plan integrates with the comprehensive requisition approval workflow detailed in **[req_approval.md](req_approval.md)**. The approval system implements a structured 4-stage process:

#### **🔗 Multi-Stage Approval Chain**
```mermaid
flowchart TD
    A[Staff Submits Requisition] --> B{Is Submitter Their Own Supervisor?}
    B -->|Yes| C[Auto-Approve Supervisor Stage]
    B -->|No| D[Send to Supervisor]
    D --> E[Supervisor Reviews & Approves]
    E --> F[Stage 2: Finance Director]
    C --> F
    F --> G[Finance Director Reviews & Approves]
    G --> H[Stage 3: Director of Schools]
    H --> I[Director of Schools Final Approval]
    I --> J[Stage 4: Finance Staff PO Entry]
    J --> K[Workflow Complete - PO Generated]
```

#### **🎯 Workflow Stages & Roles**

| Stage | Approver Role | Azure AD Integration | Approval Authority |
|-------|---------------|---------------------|-------------------|
| **1** | Direct Supervisor | Organizational Hierarchy | Operational approval |
| **2** | Finance Director | `Finance` group member | Budget/financial review |
| **3** | Director of Schools | `extensionAttribute10="Director of Schools"` | Executive final approval |
| **4** | Finance Staff | `Finance` group member | PO creation & processing |

#### **🔔 Notification System**
- **Pending Approval**: Email to current stage approver with requisition details
- **Stage Completed**: Updates to submitter and previous approvers
- **Rejection**: Detailed feedback and re-submission guidance
- **Completion**: PO number and vendor information to all stakeholders
- **Reminders**: 24/48 hour automated follow-ups

#### **🛡️ Security & Compliance Features**
- **Permission Validation**: Each stage validates approver authority
- **Audit Trail**: Complete logging of all decisions and timestamps
- **Self-Supervision Logic**: Automatic approval for supervisor self-submissions
- **Admin Override**: Technology Department emergency approval capabilities
- **Data Integrity**: Foreign key constraints and referential integrity

#### **📊 Reporting & Analytics**
- **Approval Metrics**: Average processing time by stage and department
- **Budget Tracking**: Department spending analysis and compliance
- **Performance Insights**: Supervisor efficiency and bottleneck identification
- **Compliance Reports**: Complete audit trail for financial oversight

### **Implementation Coordination**
The user import system provides the foundation for the approval workflow by:
1. **Populating organizational hierarchy** from Azure AD manager relationships
2. **Establishing role-based permissions** through group memberships
3. **Creating user profiles** for approval chain determination
4. **Enabling notification routing** through imported email addresses
5. **Supporting audit requirements** with complete user tracking

---

## 📊 Expected Outcomes

### **User Database Metrics**
- **All_Staff Import**: ~200-500 staff members
- **All_Students Import**: ~1,500-3,000 students
- **Update Frequency**: Daily synchronization
- **Data Accuracy**: 99%+ with Azure AD as source of truth

### **Requisition System Benefits**
- **4-Stage Approval Process**: Supervisor → Finance Director → Director of Schools → PO Entry
- **Automated Workflow Routing**: Self-supervision detection and auto-approval
- **Complete Audit Trail**: Every decision tracked with timestamp and comments
- **Role-Based Permissions**: Azure AD group integration for approval authority
- **Email Notifications**: Automated alerts for each workflow stage
- **Budget Management**: Department-level spending oversight and compliance
- **Emergency Override**: Technology Department admin capabilities for urgent requests
- **Compliance Reporting**: Complete audit trail for financial oversight and policy compliance

### **Administrative Capabilities**
- **User Management**: Complete staff/student directory
- **Department Organization**: Building and role assignments
- **Workflow Automation**: Reduced manual processing
- **Reporting & Analytics**: Data-driven decision making
- **Asset Accountability**: Complete inventory tracking tied to users
- **Space Management**: Room-based inventory organization
- **Lifecycle Management**: From requisition to disposal tracking
- **Audit Compliance**: Complete history of all assignments and transfers

---

## 🔒 Security Considerations

### **Data Privacy**
- Import only necessary user fields
- Respect student privacy regulations (FERPA)
- Secure storage of employee information
- Audit logging for all user data access

### **Access Control**
- User import restricted to super_admin role
- Requisition access based on department permissions
- Approval authority validation
- Sensitive data encryption at rest

### **Integration Security**
- Graph API token management
- Rate limiting for bulk operations
- Error handling and retry logic
- Monitoring for failed imports

---

## 📅 Timeline & Milestones

### **Week 1: Foundation (Days 1-7)**
- [ ] Database schema migration
- [ ] Graph API user import service
- [ ] Basic user import scripts
- [ ] Testing with small user groups

### **Week 2: Management Interface (Days 8-14)**
- [ ] Admin user management pages
- [ ] User search and filtering
- [ ] Department assignment interface
- [ ] Profile synchronization tools

### **Week 3: Requisition System (Days 15-21)**
- [ ] Multi-stage approval workflow implementation
- [ ] Organizational hierarchy setup and validation
- [ ] Stage-based notification system
- [ ] Self-supervision detection logic
- [ ] Admin override capabilities
- [ ] Audit trail and compliance reporting

### **Week 4: Inventory Management System (Days 22-28)**
- [ ] Inventory item database and asset tracking
- [ ] User-inventory assignment system
- [ ] Room-inventory assignment system
- [ ] Asset transfer and checkout workflows
- [ ] Inventory audit and reconciliation tools

### **Week 5: Reporting & Integration (Days 29-35)**
- [ ] Administrative dashboard with inventory metrics
- [ ] Financial integration and asset depreciation
- [ ] Compliance reporting and audit trails
- [ ] Performance optimization
- [ ] User acceptance testing

---

## 🚀 Getting Started

### **Immediate Next Steps**

1. **Review and approve this implementation plan**
2. **Set up development database with new schema**
3. **Test Graph API permissions for group member access**
4. **Create initial user import service structure**
5. **Begin with small test group (Technology Department)**

### **Prerequisites**
- ✅ Authentication system operational
- ✅ Azure AD Graph API access configured
- ✅ Database connection established
- ✅ Admin interface framework ready

### **Success Criteria**
- Complete user directory imported from Azure AD with organizational hierarchy
- Functional 4-stage requisition approval system with automated routing
- Administrative tools for user and workflow management
- Integration with existing authentication and role-based permissions
- Comprehensive audit trail and compliance reporting capabilities
- Email notification system for all workflow stages
- Self-supervision detection and emergency override features
- **Complete inventory management system** with user and room assignments
- **Asset tracking** from requisition through disposal
- **Room management** with designated managers and scheduled audits
- **Inventory accountability** with complete assignment history

---

<p align="center" style="color: #6a1b9a;">
<b>🎯 Ready to Transform OCS User & Asset Management</b><br>
This comprehensive system will establish the foundation for<br>
advanced workflow management, asset accountability, and organizational efficiency.
</p>

---

*Created: June 23, 2025*  
*Version: 1.1 - Implementation Plan with Inventory Management*  
*Status: 🎯 READY FOR DEVELOPMENT*

## **Legacy Data Migration**

### **Legacy Inventory Fields Mapping**

The current inventory system has the following fields that need to be migrated:

| Legacy Field | New Field | Data Type | Migration Notes |
|--------------|-----------|-----------|-----------------|
| `tag` | `asset_tag` | VARCHAR(100) | Direct mapping, ensure uniqueness |
| `type` | `item_name` | VARCHAR(255) | Map to standardized item names |
| `brand` | `brand` | VARCHAR(100) | Direct mapping |
| `model` | `model` | VARCHAR(100) | Direct mapping |
| `serial` | `serial_number` | VARCHAR(255) | Direct mapping |
| `school` | `school_assignment` | VARCHAR(255) | Direct mapping, normalize later |
| `room` | `legacy_room` | VARCHAR(100) | Store original, map to normalized rooms |
| `po` | `po_number` | VARCHAR(100) | Direct mapping |
| `price` | `purchase_price` | DECIMAL(10,2) | Convert to decimal format |
| `funds` | `funding_source` | VARCHAR(255) | Direct mapping |
| `install` | `install_date` | DATE | Convert to DATE format |
| `dispose` | `disposal_date` | DATE | Convert to DATE format if not null |
| `vendor` | `vendor` | VARCHAR(255) | Direct mapping |
| `condition` | `condition_rating` | VARCHAR(20) | Standardize values |
| `funding_percentage` | `funding_percentage` | DECIMAL(5,2) | Convert to decimal format |
| `titleholder` | `title_holder` | VARCHAR(255) | Direct mapping |
| `use` | `usage_type` | VARCHAR(100) | Standardize categories |
| `fain` | `federal_award_id` | VARCHAR(100) | Direct mapping |

### **Migration Script Structure**

```sql
-- Step 1: Create temporary staging table
CREATE TABLE legacy_inventory_staging AS 
SELECT * FROM legacy_inventory_table;

-- Step 2: Data cleaning and standardization
UPDATE legacy_inventory_staging 
SET condition = CASE 
    WHEN LOWER(condition) IN ('excellent', 'exc', 'e') THEN 'excellent'
    WHEN LOWER(condition) IN ('good', 'g') THEN 'good'
    WHEN LOWER(condition) IN ('fair', 'f') THEN 'fair'
    WHEN LOWER(condition) IN ('poor', 'p') THEN 'poor'
    WHEN LOWER(condition) IN ('damaged', 'dmg', 'd') THEN 'damaged'
    ELSE 'good'
END;

-- Step 3: Migrate core inventory data
INSERT INTO inventory_items (
    asset_tag, item_name, brand, model, serial_number,
    school_assignment, legacy_room, po_number, purchase_price,
    funding_source, install_date, disposal_date, vendor,
    condition_rating, funding_percentage, title_holder,
    usage_type, federal_award_id, status
)
SELECT 
    tag, type, brand, model, serial,
    school, room, po, 
    CASE WHEN price ~ '^[0-9]+\.?[0-9]*$' THEN price::DECIMAL(10,2) ELSE NULL END,
    funds, 
    CASE WHEN install IS NOT NULL AND install != '' THEN install::DATE ELSE NULL END,
    CASE WHEN dispose IS NOT NULL AND dispose != '' THEN dispose::DATE ELSE NULL END,
    vendor, condition, 
    CASE WHEN funding_percentage ~ '^[0-9]+\.?[0-9]*$' THEN funding_percentage::DECIMAL(5,2) ELSE NULL END,
    titleholder, use, fain,
    CASE WHEN dispose IS NOT NULL AND dispose != '' THEN 'disposed' ELSE 'active' END
FROM legacy_inventory_staging;

-- Step 4: Create room normalization mapping
INSERT INTO rooms (building, floor, room_number, room_name, room_type)
SELECT DISTINCT 
    COALESCE(school, 'Unknown Building') as building,
    '1' as floor,
    room as room_number,
    room as room_name,
    'General' as room_type
FROM legacy_inventory_staging 
WHERE room IS NOT NULL AND room != ''
ON CONFLICT (building, floor, room_number) DO NOTHING;

-- Step 5: Update inventory items with normalized room references
UPDATE inventory_items 
SET assigned_to_room_id = r.id,
    assignment_type = 'room_assigned'
FROM rooms r 
WHERE inventory_items.legacy_room = r.room_number 
    AND inventory_items.school_assignment = r.building
    AND inventory_items.status = 'active';
```

### **Data Validation Queries**

```sql
-- Verify migration completeness
SELECT 
    COUNT(*) as total_legacy_records,
    COUNT(CASE WHEN asset_tag IS NOT NULL THEN 1 END) as migrated_with_tags,
    COUNT(CASE WHEN assigned_to_room_id IS NOT NULL THEN 1 END) as room_assignments
FROM inventory_items;

-- Check for data quality issues
SELECT 
    'Missing Asset Tags' as issue,
    COUNT(*) as count
FROM inventory_items 
WHERE asset_tag IS NULL OR asset_tag = ''
UNION ALL
SELECT 
    'Invalid Purchase Prices' as issue,
    COUNT(*) as count
FROM inventory_items 
WHERE purchase_price < 0 OR purchase_price > 999999
UNION ALL
SELECT 
    'Future Install Dates' as issue,
    COUNT(*) as count
FROM inventory_items 
WHERE install_date > CURRENT_DATE;
```

### **Post-Migration Tasks**

1. **Room Normalization**: Review and standardize room assignments
2. **Category Classification**: Assign proper categories based on item types
3. **User Assignment Reconciliation**: Match current assignments to users
4. **Asset Tag Validation**: Ensure all active items have unique asset tags
5. **Financial Data Verification**: Validate purchase prices and funding sources
6. **Disposal Records Cleanup**: Review and categorize disposal methods

### **Migration Testing Framework**

```python
# migration_validator.py
"""
Legacy inventory data migration validation script
"""
import psycopg2
from typing import Dict, List, Any
import logging

class MigrationValidator:
    def __init__(self, db_connection_string: str):
        self.conn = psycopg2.connect(db_connection_string)
        self.cursor = self.conn.cursor()
        
    def validate_migration(self) -> Dict[str, Any]:
        """Run comprehensive migration validation"""
        results = {
            'record_counts': self._check_record_counts(),
            'data_quality': self._check_data_quality(),
            'referential_integrity': self._check_referential_integrity(),
            'business_rules': self._check_business_rules()
        }
        return results
    
    def _check_record_counts(self) -> Dict[str, int]:
        """Verify record counts match expectations"""
        queries = {
            'legacy_total': "SELECT COUNT(*) FROM legacy_inventory_staging",
            'migrated_total': "SELECT COUNT(*) FROM inventory_items",
            'active_items': "SELECT COUNT(*) FROM inventory_items WHERE status = 'active'",
            'disposed_items': "SELECT COUNT(*) FROM inventory_items WHERE disposal_date IS NOT NULL"
        }
        
        results = {}
        for key, query in queries.items():
            self.cursor.execute(query)
            results[key] = self.cursor.fetchone()[0]
        
        return results
    
    def _check_data_quality(self) -> List[Dict[str, Any]]:
        """Check for data quality issues"""
        quality_checks = [
            {
                'check': 'Duplicate Asset Tags',
                'query': """
                    SELECT asset_tag, COUNT(*) 
                    FROM inventory_items 
                    WHERE asset_tag IS NOT NULL 
                    GROUP BY asset_tag 
                    HAVING COUNT(*) > 1
                """,
                'expected': 0
            },
            {
                'check': 'Missing Required Fields',
                'query': """
                    SELECT COUNT(*) 
                    FROM inventory_items 
                    WHERE item_name IS NULL OR item_name = ''
                """,
                'expected': 0
            },
            {
                'check': 'Invalid Price Ranges',
                'query': """
                    SELECT COUNT(*) 
                    FROM inventory_items 
                    WHERE purchase_price < 0 OR purchase_price > 1000000
                """,
                'expected': 0
            }
        ]
        
        results = []
        for check in quality_checks:
            self.cursor.execute(check['query'])
            count = self.cursor.fetchone()[0]
            results.append({
                'check': check['check'],
                'count': count,
                'passed': count == check['expected']
            })
        
        return results
    
    def _check_referential_integrity(self) -> List[Dict[str, Any]]:
        """Verify foreign key relationships"""
        integrity_checks = [
            {
                'check': 'Room References',
                'query': """
                    SELECT COUNT(*) 
                    FROM inventory_items i 
                    LEFT JOIN rooms r ON i.assigned_to_room_id = r.id 
                    WHERE i.assigned_to_room_id IS NOT NULL AND r.id IS NULL
                """,
                'expected': 0
            },
            {
                'check': 'User References',
                'query': """
                    SELECT COUNT(*) 
                    FROM inventory_items i 
                    LEFT JOIN users u ON i.assigned_to_user_id = u.id 
                    WHERE i.assigned_to_user_id IS NOT NULL AND u.id IS NULL
                """,
                'expected': 0
            }
        ]
        
        results = []
        for check in integrity_checks:
            self.cursor.execute(check['query'])
            count = self.cursor.fetchone()[0]
            results.append({
                'check': check['check'],
                'count': count,
                'passed': count == check['expected']
            })
        
        return results
```

# Usage example:
if __name__ == "__main__":
    validator = MigrationValidator("postgresql://user:pass@localhost/ocs_portal")
    results = validator.validate_migration()
    
    print("Migration Validation Results:")
    for category, data in results.items():
        print(f"\n{category.upper()}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        elif isinstance(data, list):
            for item in data:
                status = "✓ PASS" if item.get('passed', True) else "✗ FAIL"
                print(f"  {item['check']}: {item.get('count', 'N/A')} {status}")
```

### **Legacy Field Validation Rules**

| Field | Validation Rule | Example | Notes |
|-------|----------------|---------|--------|
| `asset_tag` | Must be unique, non-empty | "TECH-001234" | Primary identifier |
| `item_name` | Required, standardized | "Dell Laptop" vs "laptop dell" | Normalize naming |
| `purchase_price` | Numeric, 0-999999.99 | 1299.99 | Validate currency format |
| `install_date` | Valid date, not future | "2023-08-15" | Installation/deployment |
| `condition_rating` | Enum values only | excellent/good/fair/poor/damaged | Standardize conditions |
| `funding_percentage` | 0-100.00 | 85.50 | Federal funding percentage |
| `serial_number` | Alphanumeric | "ABC123XYZ" | Manufacturing serial |
| `po_number` | Valid format | "PO-2023-001" | Purchase order reference |
