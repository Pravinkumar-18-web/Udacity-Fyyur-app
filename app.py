""" 
 Main file that starts the app
 Contains endpoints for the app
"""
# Imports

import json
import logging
import os
import sys
from logging import FileHandler, Formatter
from venv import logger

import babel
import dateutil.parser
from flask import (Flask, Response, flash, jsonify, 
redirect, render_template, request, url_for)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form,FlaskForm

from forms import *
from models import db, Artist, Venue, Show

# App Config.


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

SQLALCHEMY_DATABASE_URI = 'postgresql://pravi:1898@localhost:5432/fyyur'
# Filters.


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# Controllers.


@app.route('/')
def index():
  
    recent_artists = Artist.query.order_by(Artist.created_at.desc()).limit(10).all()

    recent_venues = Venue.query.order_by(Venue.created_at.desc()).limit(10).all()

    return render_template('pages/home.html',recent_artists=recent_artists, recent_venues=recent_venues)
  

pass

# Common Search by city and State
@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    artists = []
    venues = []

    city = form.city.data
    state = form.state.data

    artists = Artist.query.filter_by(city=city, state=state).all()

    venues = Venue.query.filter_by(city=city, state=state).all()

    return render_template('forms/search_results.html', form=form, artists=artists, venues=venues)

# Artists
@app.route('/artists')
def artists():
    return render_template('pages/artists.html',
                           artists=Artist.query.all())

# Artist Search
@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term')
    search_results = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_term))).all()  

    response = {}
    response['count'] = len(search_results)
    response['data'] = search_results

    return render_template('pages/search_artists.html',
                           results=response,
                           search_term=request.form.get('search_term', ''))

# Create Artist
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    error=False
       
    try:
        artist = Artist()
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website_link = request.form['website_link']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        return render_template('pages/home.html')

# View Artist
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    current_time = datetime.today()

    past_shows = [show.show_venue() for show in artist.shows if show.start_time < current_time]
    upcoming_shows = [show.show_venue() for show in artist.shows if show.start_time >= current_time]

    data = artist.to_dict()
    data.update({
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    })

    return render_template('pages/show_artist.html', artist=data)

# Edit Artist
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
  
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        artist.genres = ','.join(tmp_genres)
        artist.website_link = request.form['website_link']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Artist ' +
                  request.form['name'] + ' Could not be updated!')
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully updated!')
            return redirect(url_for('show_artist', artist_id=artist_id))
              

# Venue
@app.route('/venues')
def venues():
    venues = Venue.query.order_by(Venue.state, Venue.city).all()
    data = []
    tmp = {}
    prev_city = None
    prev_state = None

    for venue in venues:
        venue_data = {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.today()])
        }

        if venue.city == prev_city and venue.state == prev_state:
            tmp['venues'].append(venue_data)
        else:
            if prev_city is not None:
                data.append(tmp)
            tmp = {
                'city': venue.city,
                'state': venue.state,
                'venues': [venue_data]
            }
        
        prev_city = venue.city
        prev_state = venue.state

    if tmp:
        data.append(tmp)

    return render_template('pages/venues.html', areas=data)

# Venue Search
@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term')
    venues = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_term))).all()

    data = []
    for venue in venues:
        tmp = {}
        tmp['id'] = venue.id
        tmp['name'] = venue.name
        tmp['num_upcoming_shows'] = len(venue.shows)
        data.append(tmp)

    response = {}
    response['count'] = len(data)
    response['data'] = data

    return render_template('pages/search_venues.html',
                           results=response,
                           search_term=request.form.get('search_term', ''))

#  Create Venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    error = False
    try:
        venue = Venue()
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)
        venue.facebook_link = request.form['facebook_link']
        venue.website_link = request.form['website_link']
        venue.image_link = request.form['image_link']
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = request.form['seeking_description']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' +
                  request.form['name'] + ' Could not be listed!')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
    return render_template('pages/home.html')

# View Venue
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    current_time = datetime.today()

    past_shows = [show.show_artist() for show in venue.shows if show.start_time < current_time]
    upcoming_shows = [show.show_artist() for show in venue.shows if show.start_time >= current_time]

    data = venue.to_dict()
    data.update({
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    })

    return render_template('pages/show_venue.html', venue=data)

# Edit venue
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id).to_dict()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    error = False
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        tmp_genres = request.form.getlist('genres')
        venue.genres = ','.join(tmp_genres)  
        venue.facebook_link = request.form['facebook_link']
        venue.website_link = request.form['website_link']
        venue.image_link = request.form['image_link']
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = request.form['seeking_description']
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
        else:
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Shows
@app.route('/shows')
def shows():
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.isoformat()
        })

    return render_template('pages/shows.html', shows=data)

# Create Show 
@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time'] 
        
        show_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        show_date = show_datetime.date().isoformat()  
        show_time = show_datetime.time().strftime("%H:%M") 
        
        artist = Artist.query.get(artist_id)
        available_slots = artist.availability 

        is_available = False
        for slot in available_slots:
           available_date = slot.get("date")  
           available_time = slot.get("start_time") 

           if show_date == available_date and show_time == available_time:
              is_available = True
              break

        if is_available:
            show = Show(
                artist_id=artist_id,
                venue_id=venue_id,
                start_time=start_time
            )
            db.session.add(show)
            db.session.commit()
            flash('Requested show was successfully listed')
            return render_template('pages/home.html')
        else:
            flash("The artist is not available at the requested date and time.")
            return redirect(url_for('create_show'))
        
    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        
    return render_template('pages/home.html')

# Set Availability
@app.route('/artists/<int:artist_id>/set_availability', methods=['GET', 'POST'])
def set_availability(artist_id):
    artist = Artist.query.get(artist_id)
    form = AvailabilityForm()

    if request.method == 'POST' :
        availability = [{"date": entry.date.data, "start_time": entry.start_time.data} for entry in form.entries.entries]
        artist.availability = availability  
        db.session.commit()
        flash('Availability updated successfully!', 'success')
    
    return render_template('forms/set_availability.html', form=form, artist=artist)
   

 #error handler - 404 
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

#error handler - 500
@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)