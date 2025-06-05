#!/usr/bin/env python3
"""
Data migration script to move ticket data from ocs_portal to ocs_tickets database.
This script should be run after both databases are created but before removing
ticket tables from the portal database.
"""

import sys
sys.path.append('/home/nimda/Projects/Tracker')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ocs_shared_models.models import TechTicket, MaintenanceTicket
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URLs
PORTAL_DB_URL = "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_portal"
TICKETS_DB_URL = "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_tickets"

def migrate_tickets():
    """Migrate tickets from portal database to tickets database."""
    try:
        # Create engines
        portal_engine = create_engine(PORTAL_DB_URL)
        tickets_engine = create_engine(TICKETS_DB_URL)
        
        # Create sessions
        PortalSession = sessionmaker(bind=portal_engine)
        TicketsSession = sessionmaker(bind=tickets_engine)
        
        portal_session = PortalSession()
        tickets_session = TicketsSession()
        
        # Check if tables exist in source database
        portal_tables = portal_engine.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('tech_tickets', 'maintenance_tickets')
        """)).fetchall()
        
        if not portal_tables:
            logger.info("No ticket tables found in portal database. Migration not needed.")
            return
        
        logger.info(f"Found tables in portal database: {[t[0] for t in portal_tables]}")
        
        # Migrate Tech Tickets
        if any(t[0] == 'tech_tickets' for t in portal_tables):
            try:
                tech_tickets = portal_session.query(TechTicket).all()
                logger.info(f"Found {len(tech_tickets)} tech tickets to migrate")
                
                for ticket in tech_tickets:
                    # Create new ticket in tickets database
                    new_ticket = TechTicket(
                        id=ticket.id,
                        building_id=ticket.building_id,
                        room_id=ticket.room_id,
                        user_name=ticket.user_name,
                        contact_info=ticket.contact_info,
                        device_type=ticket.device_type,
                        description=ticket.description,
                        status=ticket.status,
                        created_at=ticket.created_at,
                        updated_at=ticket.updated_at
                    )
                    tickets_session.merge(new_ticket)  # Use merge to handle duplicates
                
                tickets_session.commit()
                logger.info(f"Successfully migrated {len(tech_tickets)} tech tickets")
                
            except Exception as e:
                logger.error(f"Error migrating tech tickets: {e}")
                tickets_session.rollback()
        
        # Migrate Maintenance Tickets  
        if any(t[0] == 'maintenance_tickets' for t in portal_tables):
            try:
                maintenance_tickets = portal_session.query(MaintenanceTicket).all()
                logger.info(f"Found {len(maintenance_tickets)} maintenance tickets to migrate")
                
                for ticket in maintenance_tickets:
                    # Create new ticket in tickets database
                    new_ticket = MaintenanceTicket(
                        id=ticket.id,
                        building_id=ticket.building_id,
                        room_id=ticket.room_id,
                        user_name=ticket.user_name,
                        contact_info=ticket.contact_info,
                        issue_type=ticket.issue_type,
                        description=ticket.description,
                        status=ticket.status,
                        created_at=ticket.created_at,
                        updated_at=ticket.updated_at
                    )
                    tickets_session.merge(new_ticket)  # Use merge to handle duplicates
                
                tickets_session.commit()
                logger.info(f"Successfully migrated {len(maintenance_tickets)} maintenance tickets")
                
            except Exception as e:
                logger.error(f"Error migrating maintenance tickets: {e}")
                tickets_session.rollback()
        
        portal_session.close()
        tickets_session.close()
        
        logger.info("Ticket data migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_tickets()
