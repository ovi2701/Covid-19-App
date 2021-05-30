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

    class Forecast_data_DB:
        def __init__(self, cases, data):
            self.cases = cases
            self.data = data

    st.title('Forecasting App')
    st.write('Welcome to Covid-19 Forecasting App! With this app you will be able to see how Covid-19 cases may increase or decrease in the future.')
    # LOADING DATA IN FIREBASE
    firebase = firebase.FirebaseApplication("https://covid-19-535b8-default-rtdb.firebaseio.com/", None)
    st.sidebar.title("Forecasting parameters")

    image = Image.open('D:\Python_implements\Proiect_IPDP\covid-cells.jpg')
    st.image(image)

    countries_list = ["Germany", "Italy", "Romania", "Spain", "Greece", "Switzerland", "Hungary", "Belarus", "Austria",
                      "Croatia", "Slovenia"]
    i = random.randint(0, 100000000)
    selected_country = st.sidebar.selectbox("Select country", countries_list)
    cred_obj = firebase_admin.credentials.Certificate('covid-19-535b8-firebase-adminsdk-75wgs-65e6050775.json')
    default_app = firebase_admin.initialize_app(cred_obj, {'databaseURL': 'https://covid-19-535b8-default-rtdb.firebaseio.com/'}, str(selected_country) + str(i))

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
        break

    for country in countries_list:
        if country == selected_country:
            country_api = "https://api.covid19api.com/country/"
            db_field = '/covid-19-535b8-default-rtdb/'
            country_api += country
            country_api += "/status/confirmed/live"
            response = requests.get(country_api)
            db_field += country

            for i in range(100, len(response.json())):
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

                if (int(year_api) > int(year_db)) or (int(year_api) == int(year_db) and int(month_api) > int(month_db)) or (int(year_api) == int(year_db) and int(month_api) == int(month_db) and int(day_api) > int(day_db)):
                    obj = Forecast_data_DB(str(int(response.json()[i]["Cases"]) - int(response.json()[i - 1]["Cases"])), response.json()[i]["Date"])
                    if int(obj.cases) != 0:
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

    # STREAMLIT APP
    START = "2021-01-22"

    db_name = "/covid-19-535b8-default-rtdb/"
    db_name += selected_country
    print("db_name " + db_name)
    data_country = db.reference(db_name, default_app).get()
    for key, value in reversed(list(ref.items())):
        FINAL = value["date"]
        break

    days = []
    for i in range(20, 60):
        days.append(i)
    n_days = st.sidebar.selectbox("Select number of days for prediction:", days)
    period = n_days


    @st.cache
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
    # data.fillna(method='ffill')

    st.subheader('Raw data')
    st.write(data.tail())


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

    # Forecasting
    df_train = data[['date', 'cases']]
    df_train = df_train.rename(columns={"date": "ds", "cases": "y"})

    # df_train['y'] = df_train['y'] + 1
    # df_train['y'] = np.log(df_train['y'])
    m = Prophet(weekly_seasonality=True, yearly_seasonality=True)
    m.fit(df_train)
    future = m.make_future_dataframe(periods=period)
    forecast = m.predict(future)

    # forecast['yhat'] = np.exp(forecast['yhat'])-1
    for x in range(len(forecast['yhat'])):
        if forecast['yhat'][x] <= 0:
            forecast['yhat'][x] = 0
    print(forecast)
    st.subheader('Forecast data')
    st.write(forecast.tail())

    st.write('forecast data')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    st.write('forecast components')
    fig2 = m.plot_components(forecast)
    st.write(fig2)
