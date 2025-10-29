from flask import render_template, url_for, flash, redirect, request, Blueprint, abort
from flask_login import current_user, login_required
from the_greenhouse import db
from the_greenhouse.models import Events, EventAttendee, EventItem
from the_greenhouse.posts.forms import EventForm, JoinEventForm
from sqlalchemy import select, and_
from datetime import date

posts = Blueprint('posts', __name__)

@posts.route('/create_event', methods = ['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Events(
            event_title = form.event_title.data, 
            event_description = form.event_description.data,
            event_date = form.event_date.data,
            event_time = form.event_time.data,
            location = form.location.data,
            user_id = current_user.id
        )
        db.session.add(event)
        db.session.flush()  # Get the event ID
        
        # Automatically join the creator to the event
        items_bringing = None
        if form.purpose.data in ['Sell', 'Both'] and form.items_bringing.data:
            items_bringing = form.items_bringing.data
        
        attendee = EventAttendee(
            event_id=event.id,
            user_id=current_user.id,
            attendance_likelihood='Definitely',  # Creator is definitely attending
            purpose=form.purpose.data,
            items_bringing=items_bringing
        )
        
        db.session.add(attendee)
        db.session.flush()  # Get the attendee ID
        
        # Parse items_bringing text and create EventItem records for creator
        if items_bringing and form.purpose.data in ['Sell', 'Both']:
            # Split items by newlines and process each item
            items_list = [item.strip() for item in items_bringing.split('\n') if item.strip()]
            
            for item_text in items_list:
                # Simple item name only
                item_name = item_text.strip()
                
                # Create EventItem record
                event_item = EventItem(
                    event_id=event.id,
                    user_id=current_user.id,
                    item_name=item_name
                )
                db.session.add(event_item)
        
        db.session.commit()
        flash('Event created successfully and you have been automatically joined!', 'success')
        return redirect(url_for('core.index'))

    return render_template('create_event.html', form = form)

@posts.route('/event/<int:event_id>')
def event(event_id):
    event = db.session.scalar(select(Events).where(Events.id == event_id))
    if event is None:
        abort(404)
    
    # Check if current user is already attending
    user_attending = None
    if current_user.is_authenticated:
        user_attending = db.session.scalar(
            select(EventAttendee).where(
                and_(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id)
            )
        )
    
    # Get all attendees
    attendees = db.session.scalars(
        select(EventAttendee).where(EventAttendee.event_id == event_id)
    ).all()
    
    # Get all event items
    event_items = db.session.scalars(
        select(EventItem).where(EventItem.event_id == event_id)
    ).all()
    
    return render_template('event.html', event=event, user_attending=user_attending, attendees=attendees, event_items=event_items, now = date.today())

@posts.route('/event/<int:event_id>/update', methods = ['GET', 'POST'])
@login_required
def update(event_id):
    event = db.session.scalar(select(Events).where(Events.id == event_id))
    if event is None:
        abort(404)
    if event.author != current_user:
        abort(403)
    form = EventForm()
    if form.validate_on_submit():
        event.event_title = form.event_title.data
        event.event_description = form.event_description.data
        event.event_date = form.event_date.data
        event.event_time = form.event_time.data
        event.location = form.location.data
        
        # Update creator's attendance record
        creator_attendance = db.session.scalar(
            select(EventAttendee).where(
                and_(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id)
            )
        )
        
        if creator_attendance:
            creator_attendance.purpose = form.purpose.data
            items_bringing = None
            if form.purpose.data in ['Sell', 'Both'] and form.items_bringing.data:
                items_bringing = form.items_bringing.data
            creator_attendance.items_bringing = items_bringing
        
        db.session.commit()
        flash('Event updated successfully', 'success')
        return redirect(url_for('posts.event', event_id = event.id))

    elif request.method == 'GET':
        form.event_title.data = event.event_title
        form.event_description.data = event.event_description
        form.event_date.data = event.event_date
        form.event_time.data = event.event_time
        form.location.data = event.location
        
        # Pre-fill creator's attendance data
        creator_attendance = db.session.scalar(
            select(EventAttendee).where(
                and_(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id)
            )
        )
        if creator_attendance:
            form.purpose.data = creator_attendance.purpose
            form.items_bringing.data = creator_attendance.items_bringing or ''

    return render_template('create_event.html', form = form, event = event)

@posts.route('/event/<int:event_id>/delete', methods = ['GET', 'POST'])
@login_required
def delete(event_id):
    event = db.session.scalar(select(Events).where(Events.id == event_id))
    if event is None:
        abort(404)
    if event.author != current_user:
        abort(403)
    
    # Delete the event (cascade will handle attendees automatically)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully', 'success')
    return redirect(url_for('core.index'))

@posts.route('/event/<int:event_id>/join', methods = ['GET', 'POST'])
@login_required
def join_event(event_id):
    event = db.session.scalar(select(Events).where(Events.id == event_id))
    if event is None:
        abort(404)
    
    # Check if user is already attending
    existing_attendance = db.session.scalar(
        select(EventAttendee).where(
            and_(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id)
        )
    )
    
    if existing_attendance:
        flash('You are already attending this event!', 'info')
        return redirect(url_for('posts.event', event_id=event_id))
    
    form = JoinEventForm()
    if form.validate_on_submit():
        # Only include items_bringing if purpose is Sell or Both
        items_bringing = None
        if form.purpose.data in ['Sell', 'Both'] and form.items_bringing.data:
            items_bringing = form.items_bringing.data
        
        attendee = EventAttendee(
            event_id=event_id,
            user_id=current_user.id,
            attendance_likelihood=form.attendance_likelihood.data,
            purpose=form.purpose.data,
            items_bringing=items_bringing
        )
        
        db.session.add(attendee)
        db.session.flush()  # Get the attendee ID
        
        # Parse items_bringing text and create EventItem records
        if items_bringing and form.purpose.data in ['Sell', 'Both']:
            # Split items by newlines and process each item
            items_list = [item.strip() for item in items_bringing.split('\n') if item.strip()]
            
            for item_text in items_list:
                # Simple item name only
                item_name = item_text.strip()
                
                # Create EventItem record
                event_item = EventItem(
                    event_id=event_id,
                    user_id=current_user.id,
                    item_name=item_name
                )
                db.session.add(event_item)
        
        db.session.commit()
        flash('Successfully joined the event!', 'success')
        return redirect(url_for('posts.event', event_id=event_id))
    
    return render_template('join_event.html', form=form, event=event)

@posts.route('/event/<int:event_id>/unattend', methods=['POST'])
@login_required
def unattend_event(event_id):
    """Remove user from event attendance"""
    event = db.session.scalar(select(Events).where(Events.id == event_id))
    if event is None:
        abort(404)
    
    # Check if user is attending
    user_attendance = db.session.scalar(
        select(EventAttendee).where(
            and_(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id)
        )
    )
    
    if not user_attendance:
        flash('You are not attending this event!', 'warning')
        return redirect(url_for('posts.event', event_id=event_id))
    
    # Prevent event creator from unattending their own event
    if event.user_id == current_user.id:
        flash('You cannot unattend your own event!', 'warning')
        return redirect(url_for('posts.event', event_id=event_id))
    
    # Delete all EventItem records for this user and event
    EventItem.query.filter(
        and_(EventItem.event_id == event_id, EventItem.user_id == current_user.id)
    ).delete()
    
    # Delete the EventAttendee record
    db.session.delete(user_attendance)
    db.session.commit()
    
    flash('You have successfully unattended the event. Your items have been removed.', 'success')
    return redirect(url_for('posts.event', event_id=event_id))