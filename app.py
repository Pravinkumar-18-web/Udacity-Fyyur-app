""" 
 Main file that starts the app
 Contains endpoints for the app
"""
# Imports

from collections import defaultdict
import logging
import os
from logging import FileHandler, Formatter
import babel
import dateutil.parser
from flask import (Flask, flash,  
redirect, render_template, request, url_for)
from flask_migrate import Migrate
from flask_moment import Moment

from forms import *
from models import db, Artist, Venue, Show

# App Config.

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# Filters.

def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date =dateutil.parser.parse(value)
    else:
        date = value

    if format == 'full':
        format = "EEEE MMMM d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM dd, y h:mma"

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
    if request.method == 'POST' :
        if form.validate() :
           city = form.city.data
           state = form.state.data
       
           artists = Artist.query.filter_by(city=city, state=state).all()
       
           venues = Venue.query.filter_by(city=city, state=state).all()
           return render_template('pages/show_results.html',city=city,state=state,artists=artists, venues=venues)
           
        else:   
          flash('Please enter a valid city and state.')
          return render_template('forms/search_results.html', form=form, artists=artists, venues=venues)
    else :
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
    form = ArtistForm(request.form,meta={'csrf':False})
    if form.validate() :
       try:
          artist = Artist(
          name = form.name.data,
          city = form.city.data,
          state = form.state.data,
          phone = form.phone.data,
          genres = form.genres.data,
          website_link = form.website_link.data,
          image_link = form.image_link.data,
          facebook_link = form.facebook_link.data,
          seeking_venue = form.seeking_venue.data,
          seeking_description = form.seeking_description.data)
          db.session.add(artist)
          db.session.commit()
          flash('Artist ' + form.name.data +
                  ' was successfully listed!')
          return render_template('pages/home.html')
       except Exception as e:
          db.session.rollback()
          print(e)
          flash('An error occurred. Artist ' +
                  form.name.data + ' could not be listed.')
       finally:
        db.session.close()
    else:
        errors = ", ".join([f"{field}:{error}" for field, errs in form.errors.items() for error in errs])
        flash(f'please fix the following errors: {errors}')  
        return render_template('forms/new_artist.html', form=form)

# View Artist
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    past_shows = []
    upcoming_shows = []

    for show in artist.shows:
        show_info = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": format_datetime(show.start_time)
        }
        if show.start_time <= datetime.now():
            past_shows.append(show_info)
        else:
            upcoming_shows.append(show_info)

    data = artist.__dict__
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    availability_data = []
    current_datetime = datetime.now()

    if artist.availability:
        for slot in artist.availability:
            date_str = slot.get("date")
            time_str = slot.get("start_time")

            if date_str and time_str:
                try:
                    slot_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    
                    if slot_datetime > current_datetime:
                        formatted_slot = f"{date_str}, {time_str}"
                        availability_data.append(formatted_slot)
                except ValueError:
                    continue

    return render_template('pages/show_artist.html', artist=data, availability_data=availability_data)

# Edit Artist
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get_or_404(artist_id)
  
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    try:
        artist = Artist.query.get_or_404(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.website_link = form.website_link.data
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + form.name.data +
                  ' was successfully updated!')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('An error occured. Artist ' +
                  form.name.data + ' Could not be updated!')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))
              

# Venue
@app.route('/venues')
def venues():
    venues = Venue.query.order_by(Venue.state, Venue.city).all()

    data = defaultdict(lambda :{ "venues":[]})

    for venue in venues:
        city_state = (venue.city,venue.state)
        data[city_state]["city"] = venue.city
        data[city_state]["state"] = venue.state
        data[city_state]["venues"].append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.today()])
        })

    data = [value for value in data.values()]

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
    form = VenueForm(request.form,meta={'csrf':False})
    if form.validate():
         try:
             venue = Venue(
             name = form.name.data,
             city = form.city.data,
             state =form.state.data,
             address = form.address.data,
             phone = form.phone.data,
             genres = form.genres.data,
             facebook_link = form.facebook_link.data,
             website_link = form.website_link.data,
             image_link = form.image_link.data,
             seeking_talent = form.seeking_talent.data,
             seeking_description = form.seeking_description.data)
             db.session.add(venue)
             db.session.commit()
             flash('Venue ' + form.name.data +
                  ' was successfully listed!')
             return render_template('pages/home.html')
         except Exception as e :
             error = True
             db.session.rollback()
             print(e)
             flash('An error occured. Venue Could not be listed!')
         finally:
             db.session.close()
    else:
        errors = ", ".join([f"{field}:{error}" for field, errs in form.errors.items() for error in errs])
        flash(f'please fix the following errors: {errors}')  
        return render_template('forms/new_venue.html', form=form)
        
# View Venue
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    past_shows=[]
    upcoming_shows=[]

    for show in venue.shows:
        show_info = {
            "artist_id" : show.artist_id,
            "artist_name" : show.artist.name,
            "artist_image_link" : show.artist.image_link,
            "start_time" : format_datetime(show.start_time)
        }
        if show.start_time <= datetime.now():
            past_shows.append(show_info)
        else:
            upcoming_shows.append(show_info)

    data = venue.__dict__
    data['past_shows']= past_shows
    data['upcoming_shows']= upcoming_shows
    data['past_shows_count']=len(past_shows)
    data['upcoming_shows_count']= len(upcoming_shows)
    
    return render_template('pages/show_venue.html', venue=data)
        
# Edit venue
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get_or_404(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    try:
        venue = Venue.query.get_or_404(venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.image_link = form.image_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + form.name.data +
                  ' was successfully updated!')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash('An error occurred. Venue ' +
                  form.name.data + ' could not be updated.')
    finally:
        db.session.close()
               
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
    form = ShowForm(request.form,meta={'csrf':False})
    if form.validate() :
         try:
            show = Show(
            artist_id= form.artist_id.data,
            venue_id= form.venue_id.data,
            start_time= form.start_time.data
             )
            
            show_date = show.start_time.date().isoformat()  
            show_time = show.start_time.time().strftime("%H:%M")

            if is_artist_available(show.artist_id, show_date, show_time) :
                 db.session.add(show)
                 db.session.commit()
                 flash('Requested show was successfully listed')
                 return render_template('pages/home.html')
            else:
                 flash("The artist is not available at the requested date and time.")
                 return redirect(url_for('create_shows'))
         except Exception as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. show could not be listed.')
            return redirect(url_for('create_shows'))
         finally:
            db.session.close()
           
    else:
        errors = ", ".join([f"{field}:{error}" for field, errs in form.errors.items() for error in errs])
        flash(f'please fix the following errors: {errors}')  

    return render_template('pages/shows.html', form=form)

def is_artist_available(artist_id, show_date, show_time):

    artist = Artist.query.get_or_404(artist_id)
    available_slots = artist.availability 

    for slot in available_slots:
        available_date = slot.get("date")
        available_time = slot.get("start_time")

        if show_date == available_date and show_time == available_time:
            return True
    return False    

# Set Availability
@app.route('/artists/<int:artist_id>/set_availability', methods=['GET', 'POST'])
def set_availability(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    form = AvailabilityForm(request.form, meta={'csrf': False})
    entries = []
    if request.method == 'POST':
        if form.validate():
            try:
                entries = [
                    {"date": entry.date.data.strftime('%Y-%m-%d'), "start_time": entry.start_time.data.strftime('%H:%M')}
                    for entry in form.entries
                ]
                artist.availability = entries  
                db.session.commit()
                flash('Availability updated successfully!', 'success')
                return redirect(url_for('show_artist', artist_id=artist_id))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash('An error occurred. Unable to Update it !!!.')
            finally:
                db.session.close()
        else:
            errors = ", ".join([f"{field}: {error}" for field, errs in form.errors.items() for error in errs])
            flash(f'Please fix the following errors: {errors}')

    return render_template('forms/set_availability.html', form=form, artist=artist, entries=entries)

     
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