# Clean export-for-import routes - no syntax errors

@app.get("/api/tickets/tech/export-for-import")
def export_tech_tickets_for_import_csv(db: Session = Depends(get_db)):
    """Export all technology tickets to CSV in import-ready format (no IDs or timestamps)"""
    try:
        # Get all tech tickets
        tickets = db.query(TechTicket).order_by(desc(TechTicket.created_at)).all()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        
        # Write CSV headers - import-ready format (no id, created_at, updated_at)
        writer = csv.writer(temp_file)
        writer.writerow([
            'title', 'description', 'issue_type', 'school', 'room', 'tag', 
            'status', 'created_by'
        ])
        
        # Write ticket data
        for ticket in tickets:
            writer.writerow([
                ticket.title or '',
                ticket.description or '',
                ticket.issue_type or '',
                ticket.school or '',
                ticket.room or '',
                ticket.tag or '',
                ticket.status,
                ticket.created_by or ''
            ])
        
        temp_file.close()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"tech_tickets_import_ready_{current_date}.csv"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting tech tickets for import: {str(e)}")

@app.get("/api/tickets/maintenance/export-for-import")
def export_maintenance_tickets_for_import_csv(db: Session = Depends(get_db)):
    """Export all maintenance tickets to CSV in import-ready format (no IDs or timestamps)"""
    try:
        # Get all maintenance tickets
        tickets = db.query(MaintenanceTicket).order_by(desc(MaintenanceTicket.created_at)).all()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        
        # Write CSV headers - import-ready format (no id, created_at, updated_at)
        writer = csv.writer(temp_file)
        writer.writerow([
            'title', 'description', 'issue_type', 'school', 'room', 
            'status', 'created_by'
        ])
        
        # Write ticket data
        for ticket in tickets:
            writer.writerow([
                ticket.title or '',
                ticket.description or '',
                ticket.issue_type or '',
                ticket.school or '',
                ticket.room or '',
                ticket.status,
                ticket.created_by or ''
            ])
        
        temp_file.close()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"maintenance_tickets_import_ready_{current_date}.csv"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting maintenance tickets for import: {str(e)}")
