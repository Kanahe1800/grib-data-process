from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import timedelta
import pygrib
import pandas as pd
from json import loads
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route("/location/<float:lat>/<float:lng>", methods=['GET'])
def get_wind_info(lat, lng):
    return_df = create_df(lat, lng)
    try:
        retunr_json = return_df.to_json(orient="values")
        parsed = loads(retunr_json)
        return jsonify({"message": "Data received successfully", "data": parsed}), 200
    except AttributeError:
        return jsonify({"message": "latitude and / or longitude is not valid"}), 412

@app.route("/allData", methods=['GET'])
def get_all_wind_info():
    return_df = getAlldata()
    try:
        retunr_json = return_df.to_json(orient="records")
        parsed = loads(retunr_json)
        return jsonify({"message": "Data received successfully", "data": parsed}), 200
    except AttributeError:
        return jsonify({"message": "no data available"}), 404



def create_df(lat, lng):
    maxlat = lat + 0.0005
    minlat = lat - 0.00049
    maxlng = lng + 0.000625
    minlng = lng - 0.000624
    pd.set_option('display.max_rows', None)
    gpv_file = pygrib.open("XR183_User11_20241108_1600.grb2")
    u_messages = gpv_file.select(parameterName='u-component of wind', level = 50)
    v_messages = gpv_file.select(parameterName='v-component of wind', level = 50)
    time_diff = timedelta(hours=9)
    try:
        u_results = [ 
            {   "valid date": str(u_msg.validDate + time_diff),
                "lat": lat, 
                "lng": lng, 
                "eastward wind": wind, 
                } 
            for u_msg in u_messages 
            for i in range(len(u_msg.data(lat1=minlat, lat2=maxlat, lon1=minlng, lon2=maxlng)[0])) 
            for wind, lat, lng in zip(u_msg.data(lat1=minlat, lat2=maxlat, lon1=minlng, lon2=maxlng)[0][i],
                                        u_msg.data(lat1=minlat, lat2=maxlat, lon1=minlng, lon2=maxlng)[1][i], 
                                        u_msg.data(lat1=minlat, lat2=maxlat, lon1=minlng, lon2=maxlng)[2][i],
                                        )
            ]
        u_df = pd.DataFrame(u_results)
        v_results = [ 
            { "northward wind": val0} 
            for u_msg in v_messages 
            for i in range(len(u_msg.data(lat1=minlat, lat2=maxlat, lon1=minlng, lon2=maxlng)[0])) 
            for val0, in zip(u_msg.data(lat1=minlat, lat2=maxlat, lon1=minlng, lon2=maxlng)[0][i])
            ]
        v_df = pd.DataFrame(v_results)
        wind_df = pd.concat([u_df, v_df], axis=1)
        wind_df["eastward wind"] = wind_df["eastward wind"].astype(float)
        wind_df["northward wind"] = wind_df["northward wind"].astype(float)
        wind_df["wind speed"] = np.sqrt(np.pow(wind_df["eastward wind"], 2) + np.pow(wind_df["northward wind"], 2))
        conditions = [(wind_df["eastward wind"] > 0.01) & (wind_df["northward wind"] > 0.01), 
                    (wind_df["eastward wind"] < -0.01) & (wind_df["northward wind"] > 0.01),
                    (wind_df["eastward wind"] > 0.01) & (wind_df["northward wind"] < -0.01),
                    (wind_df["eastward wind"] < -0.01) & (wind_df["northward wind"] < -0.01),
                    (np.abs(wind_df["eastward wind"]) < 0.01) & (wind_df["northward wind"] > 0.01),
                    (np.abs(wind_df["eastward wind"]) < 0.01) & (wind_df["northward wind"] < -0.01),
                    (wind_df["eastward wind"] > 0.01) & (np.abs(wind_df["northward wind"]) < 0.01),
                    (wind_df["eastward wind"] < -0.01) & (np.abs(wind_df["northward wind"]) < 0.01),
                    (np.abs(wind_df["eastward wind"]) < 0.01) & (np.abs(wind_df["northward wind"]) < 0.01),
                    ]
        direction = ['南西', '南東','北西','北東', '南', '北', '西', '東', '無風']
        wind_df["wind direction"] = np.select(conditions, direction, default="not specified")
        print(wind_df)
        #wind_df.mask(wind_df["wind direction"] == "無風", inplace=True)
        #wind_df.dropna(inplace=True)
        gpv_file.close()
        return wind_df
    except KeyError:
        gpv_file.close()
        return "Latitude longitude is not valid"

def getAlldata():
    #gpv_file = pygrib.open("XR183_User11_20241108_1600.grb2")
    gpv_file = pygrib.open("XR183_User11_20241107_1800_grib2.bin")
    u_messages = gpv_file.select(parameterName='u-component of wind', level = 50)
    v_messages = gpv_file.select(parameterName='v-component of wind', level = 50)
    #print(u_messages[0].keys())
    #print(u_messages[1].hour)
    time_diff = timedelta(hours=9)
    u_lat_lons = [ 
            {  
                "lat": lat, 
                "lng": lng, 
            }
            for i in range(len(u_messages[0].latlons()[0])) 
            for lat, lng in zip(
                    u_messages[0].latlons()[0][i], 
                    u_messages[0].latlons()[1][i],
                    )
            ]
    wind_df = pd.DataFrame(u_lat_lons)
    #print(type(u_messages[0].validDate + time_diff))
    for i in range(len(u_messages)):
        result_at_time = [ 
            {"WEWind": val0,
            "NSWind": val1} 
            for j in range(len(u_messages[i].data()[0])) 
            for val0, val1 in zip(u_messages[i].data()[0][j], v_messages[i].data()[0][j])
        ]
        temp_df = pd.DataFrame(result_at_time)
        temp_df["WEWind"] = temp_df["WEWind"].astype(float)
        temp_df["NSWind"] = temp_df["NSWind"].astype(float)
        temp_df["Speed " + str(u_messages[i].validDate + time_diff)] = np.sqrt(np.pow(temp_df["WEWind"], 2) + np.pow(temp_df["NSWind"], 2))
        temp_df["bearing_angle"] =(np.degrees(np.arctan2(temp_df['WEWind'], temp_df['NSWind'])) + 360) % 360
        condition = (np.abs(temp_df["WEWind"]) < 0.01) & (np.abs(temp_df["NSWind"]) < 0.01)
        temp_df['Angle ' + str(u_messages[i].validDate + time_diff)] = np.where(condition, -1, temp_df["bearing_angle"])
        temp_df.drop('WEWind', axis=1, inplace=True)
        temp_df.drop('NSWind', axis=1, inplace=True)
        temp_df.drop("bearing_angle", axis=1, inplace=True)
        wind_df = pd.concat([wind_df, temp_df], axis=1)
        #print(u_messages[i].validDate)
    #print(wind_df)
    gpv_file.close()
    return wind_df    
    wind_df.mask(temp_df["direction"] == "無風", inplace=True)
    wind_df.dropna(inplace=True)
    print(len(wind_df.index))
    wind_json = wind_df.to_json(orient="values")
    parsed = loads(wind_json)
    #print(parsed)
    
    
    #print(ne_wind)

getAlldata()



if __name__ == '__main__':
    app.run(debug=True, port=8000) 

"""
    34.665 <= lat <= 34.70125
    135.36125 <= lng <= 135.44875
"""