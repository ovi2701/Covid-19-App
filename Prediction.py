import streamlit as st
def app():
    from firebase import firebase
    import requests
    import firebase_admin
    from firebase_admin import db
    import random
    import numpy as np
    from fbprophet import Prophet
    from fbprophet.plot import plot_plotly
    from plotly import graph_objects as go
    import pandas as pd
    from PIL import Image
    import logging

    #defining logging file, covid-19.log, in which program writes warnings, info message, errors etc
    logger = logging.getLogger('Prediction')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('covid-19.log', 'w+')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    #this class is used for inserating in Firebase data
    class Forecast_data_DB:
        def __init__(self, cases, data):
            self.cases = cases
            self.data = data

    #initializing database
    firebase = firebase.FirebaseApplication("https://covid-19-535b8-default-rtdb.firebaseio.com/", None)

    st.title('Forecasting App')
    st.write('Welcome to Covid-19 Forecasting App! With this app you will be able to see how Covid-19 cases may increase or decrease in the future.')

    st.sidebar.title("Forecasting parameters")

    #printing a Covid-19 image in forecasting page
    image = Image.open('"D:\Python_implements\Covid-19-App\covid_image.jpg"')
    st.image(image)

    #List of countries we select for prediction or statistics data
    countries_list = ["Germany", "Italy", "Romania", "Spain", "Greece", "Switzerland", "Hungary", "Belarus", "Austria",
                      "Croatia", "Slovenia"]

    #this i variable (which takes random values) was required because we need different name for each app calling
    i = random.randint(0, 100000000)
    selected_country = st.sidebar.selectbox("Select country", countries_list)
    cred_obj = firebase_admin.credentials.Certificate('covid-19-535b8-firebase-adminsdk-75wgs-65e6050775.json')
    default_app = firebase_admin.initialize_app(cred_obj, {'databaseURL': 'https://covid-19-535b8-default-rtdb.firebaseio.com/'}, str(selected_country) + str(i))

    #This code gives us the last date which was inserated in database, in /covid-19-535b8-default-rtdb field
    node = ""
    node += '/covid-19-535b8-default-rtdb/'
    node += selected_country
    node += '/'
    ref = db.reference(node, default_app).get()
    for key, value in reversed(list(ref.items())):
        counter = 0
        year_db = ""
        month_db = ""
        day_db = ""
        for elem in value['date']:
            if elem == "-":
                counter += 1
                continue
            elif counter < 4:
                year_db += elem
                counter += 1
            elif counter >= 5 and counter < 7 and elem != "-":
                month_db += elem
                counter += 1
            elif elem != "-" and elem != "T":
                day_db += elem
            else:
                break
        logger.info("INFO : %s - Last dataset in Prediction DB is from %s - %s - %s", selected_country, str(year_db), str(month_db), str(day_db))
        break
    for country in countries_list:
        if country == selected_country:
            #take data(active cases and date) from selected country API
            country_api = "https://api.covid19api.com/country/"
            country_api += country
            country_api += "/status/confirmed/live"
            response = requests.get(country_api)

            #field in DB in wich we write data
            db_field = '/covid-19-535b8-default-rtdb/'
            db_field += country

            #take data from API starting with row 100
            for i in range(100, len(response.json())):
                #taking date for each row in API
                counter = 0
                year_api = ""
                month_api = ""
                day_api = ""
                for elem in response.json()[i]["Date"]:
                    if elem == "-":
                        counter += 1
                        continue
                    elif counter < 4:
                        year_api += elem
                        counter += 1
                    elif counter >= 5 and counter < 7 and elem != "-":
                        month_api += elem
                        counter += 1
                    elif elem != "-" and elem != "T":
                        day_api += elem
                    else:
                        break

                #Write new data in API only if API date for each dataset row is greater than last date inserted in Database
                if (int(year_api) > int(year_db)) or (int(year_api) == int(year_db) and int(month_api) > int(month_db)) or (int(year_api) == int(year_db) and int(month_api) == int(month_db) and int(day_api) > int(day_db)):
                    obj = Forecast_data_DB(str(int(response.json()[i]["Cases"]) - int(response.json()[i - 1]["Cases"])), response.json()[i]["Date"])
                    if int(obj.cases) > 0:
                        json = {
                            "cases": obj.cases,
                            "date": obj.data
                        }
                        print(selected_country)
                        print(year_api)
                        print(month_db)
                        print(day_api)
                        result = firebase.post(db_field, json)
                        print(json["date"])
                        logger.info("INFO : %s - %s : Dataset has been added succesfully!", selected_country, obj.data)
                    else:
                        logger.warning("WARNING : %s - %s : Dataset has not been added because number of cases is negative or 0!", selected_country, obj.data)

            break

    db_name = "/covid-19-535b8-default-rtdb/"
    db_name += selected_country
    print("db_name " + db_name)
    data_country = db.reference(db_name, default_app).get()

    #Number of days for prediction
    days = [7, 14, 30]
    n_days = st.sidebar.selectbox("Select number of days for prediction:", days)
    period = n_days


    @st.cache
    #this function takes data from database and puts in a dataframe number of cases and date
    #if number of cases is 0, value is replaced with nan
    def load_data(data_country):
        data = {'cases': [],
                'date': []}

        for key, value in list(data_country.items()):
            if int(value['cases']) <= 0:
                data['cases'].append(np.nan)
            else:
                data['cases'].append(int(value['cases']))
            dt = ""
            for elem in value['date']:
                if elem != "T":
                    dt += elem
                else:
                    break
            data['date'].append(dt)

        df = pd.DataFrame(data)
        return df


    data_load_state = st.text("Load data...")
    data = load_data(data_country)
    data_load_state.text("Loading data...done!")
    print(data)

    st.subheader('Raw data')
    st.write(data.tail())

    #function for data processing before forecasting and plotting data
    #if it is found nan data, it is replaced with 0
    def plot_raw_data():
        fig = go.Figure()
        newdata = []
        for ix in data.index:
            if np.isnan(data.loc[ix]['cases']):
                newdata.append(0)
            else:
                newdata.append(data.loc[ix]['cases'])

        for index in range(1, len(newdata) - 1):
            if newdata[index] == 0:
                newdata[index] = newdata[index-1]
            if np.isnan(newdata[index]):
                newdata[index] = newdata[index - 1]

        fig.add_trace(go.Scatter(x=data['date'], y=newdata, name='active cases'))
        fig.layout.update(title_text="Time Series Data", xaxis_rangeslider_visible=True)
        st.plotly_chart(fig)


    plot_raw_data()

    # Forecasting part

    #Training data
    df_train = data[['date', 'cases']]
    df_train = df_train.rename(columns={"date": "ds", "cases": "y"})

    #Prediction
    m = Prophet(weekly_seasonality=True, yearly_seasonality=True)
    m.fit(df_train)
    future = m.make_future_dataframe(periods=period)
    forecast = m.predict(future)

    #Because it happens to have descending trend more time, we could have negative values resulted from prediction
    #As a precautionary measure, replace negative predicted data with 0
    for x in range(len(forecast['yhat'])):
        if forecast['yhat'][x] <= 0:
            forecast['yhat'][x] = 0

    #Print last predicted data
    st.subheader('Forecast data')
    st.write(forecast.tail())

    #Plot forecast data
    st.write('forecast data')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    #Plot some components such as trend, weekly, yearly etc
    st.write('forecast components')
    fig2 = m.plot_components(forecast)
    st.write(fig2)

    logger.removeHandler(fh)