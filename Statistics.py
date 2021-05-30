import streamlit as st

def app():
    import logging
    logger = logging.getLogger('Statistics')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('covid-19.log')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    import requests
    import random
    import pandas as pd
    from firebase import firebase
    import firebase_admin
    from firebase_admin import db


    class Statistics_data_DB:
        def __init__(self, confirmed, deaths, recovered, data):
            self.confirmed = confirmed
            self.deaths = deaths
            self.recovered = recovered
            self.data = data

    firebase = firebase.FirebaseApplication("https://covid-19-535b8-default-rtdb.firebaseio.com/", None)
    st.title('Statistics')
    st.write('Welcome to Covid-19 App! Here you will see some graphics data about number of active cases, recovered and so on...')
    st.sidebar.title("Statistics paramteres")
    countries_list = ["Germany", "Italy", "Romania", "Spain", "Greece", "Switzerland", "Hungary", "Belarus", "Austria",
                      "Croatia", "Slovenia"]
    i = random.randint(0, 100000000)
    selected_country = st.sidebar.selectbox("Select country", countries_list)
    cred_obj = firebase_admin.credentials.Certificate('covid-19-535b8-firebase-adminsdk-75wgs-65e6050775.json')
    default_app = firebase_admin.initialize_app(cred_obj,
                                                {'databaseURL': 'https://covid-19-535b8-default-rtdb.firebaseio.com/'},
                                                str(selected_country) + str(i))
    node = ""
    node += '/Statistics/'
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
            db_field = '/Statistics/'
            country_api += country
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
                    obj = Statistics_data_DB(str(int(response.json()[i]["Confirmed"]) - int(response.json()[i - 1]["Confirmed"])), str(int(response.json()[i]["Deaths"]) - int(response.json()[i - 1]["Deaths"])), str(int(response.json()[i]["Recovered"]) - int(response.json()[i - 1]["Recovered"])), response.json()[i]["Date"])
                    if int(obj.confirmed) > 0 and int(obj.deaths) >= 0 and int(obj.recovered) >= 0:
                        json = {
                            "confirmed": obj.confirmed,
                            "deaths": obj.deaths,
                            "recovered": obj.recovered,
                            "date": obj.data
                        }
                        print(selected_country)
                        print(year_api)
                        print(month_db)
                        print(day_api)
                        result = firebase.post(db_field, json)
                        if result == 200:
                            logger.info('Api dataset in %s from %s has been succesfully added in database!' %obj.data %selected_country)
                        else:
                            logger.warning('Dataset in %s from %s has not been added' %obj.data %selected_country)
            logger.info("Statistics dataset for %s has been succesfully updated!" %selected_country)
            break

    chart_type = st.sidebar.selectbox("Select type of chart", ('Line Chart', 'Area Chart', 'Bar Chart'))
    confirmed = []
    deaths = []
    recovered = []
    data = []
    for key, value in list(ref.items()):
        if int(value['confirmed']) >= 0 and int(value['deaths']) >= 0 and int(value['recovered']) >= 0:
            confirmed.append(int(value['confirmed']))
            deaths.append((int(value['deaths'])))
            recovered.append((int(value['recovered'])))
    data = {
        "confirmed": confirmed,
        "deaths": deaths,
        "recovered": recovered
    }
    df = pd.DataFrame(data)
    if chart_type == 'Line Chart':
        st.line_chart(df, width=900, height=600)
    if chart_type == "Area Chart":
        st.area_chart(df, width=900, height=600)
    if chart_type == "Bar Chart":
        st.bar_chart(df, width=900, height=600)




