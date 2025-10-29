from flask import render_template, Blueprint, request
from the_greenhouse import db
from the_greenhouse.models import Events, EventItem
from sqlalchemy import select, desc, and_, or_
from datetime import date

core = Blueprint('core', __name__)

@core.route('/')
@core.route('/<int:page>')
def index(page=1):
    # Get search parameters from request
    search_name = request.args.get('event_name', '').strip()
    search_location = request.args.get('location', '').strip()
    search_items = request.args.get('items_search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start with base query - only future events
    query = select(Events).filter(Events.event_date >= date.today())
    
    # Apply search filters
    if search_name:
        query = query.filter(Events.event_title.ilike(f'%{search_name}%'))
    
    if search_location:
        query = query.filter(Events.location.ilike(f'%{search_location}%'))
    
    if date_from:
        try:
            from_date = date.fromisoformat(date_from)
            query = query.filter(Events.event_date >= from_date)
        except ValueError:
            pass  # Invalid date format, ignore
    
    if date_to:
        try:
            to_date = date.fromisoformat(date_to)
            query = query.filter(Events.event_date <= to_date)
        except ValueError:
            pass  # Invalid date format, ignore
    
    # Search by items being brought
    if search_items:
        # Join with EventItem table to search by items
        query = query.join(EventItem, Events.id == EventItem.event_id).filter(
            EventItem.item_name.ilike(f'%{search_items}%')).distinct()
    
    # Order by creation date (newest first)
    query = query.order_by(desc(Events.created_date))
    
    # Paginate results
    events = db.paginate(
        query,
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template('home.html', events=events, 
                         search_name=search_name, search_location=search_location, 
                         search_items=search_items, date_from=date_from, date_to=date_to)

@core.route('/info')
def info():
    return render_template('info.html')