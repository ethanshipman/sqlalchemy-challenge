# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import datetime as dt


#################################################
# Database Setup
#################################################

#set up the database engine for sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# homepage route
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

#precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the JSON representation of precipitation data for the last year."""
    # querying the last 12 months
    last_date = session.query(func.max(Measurement.date)).scalar()
    last_year = dt.datetime.strptime(last_date, "%Y-%m-%d") - dt.timedelta(days=365)
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= last_year).all()
    
    #converting to dict
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)

#stations route
@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations."""
    stations = session.query(Station.station).all()
    stations_list = [station[0] for station in stations]
    return jsonify(stations_list)

# TOBS route
@app.route("/api/v1.0/tobs")
def tobs():
    """Return JSON of temperature observations (TOBS) for the previous year."""
    # Query the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.id).desc()).first()[0]

    # Query the last 12 months of TOBS data for the most active station
    last_date = session.query(func.max(Measurement.date)).scalar()
    last_year = dt.datetime.strptime(last_date, "%Y-%m-%d") - dt.timedelta(days=365)
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= last_year).all()

    # Convert the query results to a list of dictionaries
    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in tobs_data]
    return jsonify(tobs_list)

#start and start-end range routes
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def stats(start, end=None):
    """Return TMIN, TAVG, and TMAX for a given start or start-end range."""
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    if not end:
        # Calculate stats from the start date to the end of the dataset
        results = session.query(*sel).filter(Measurement.date >= start).all()
    else:
        # Calculate stats for the date range
        results = session.query(*sel).\
            filter(Measurement.date >= start).\
            filter(Measurement.date <= end).all()

    # Unpack the results into a dictionary
    stats_dict = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }
    return jsonify(stats_dict)

#running the app
if __name__ == "__main__":
    app.run(debug=True)