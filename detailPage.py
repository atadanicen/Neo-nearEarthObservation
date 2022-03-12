from datetime import timedelta
import streamlit as st
import requests
import json
import pandas as pd


def Observe(apiKey, startDate, endDate):
    apiResponse = requests.get(
        "https://api.nasa.gov/neo/rest/v1/feed?start_date="+str(startDate)+"&end_date="+str(endDate)+"&api_key="+apiKey)

    dayDifference = (endDate-startDate).days
    objects = "near_earth_objects"
    date = startDate
    nameList = []
    approachDateList = []
    relVelocityList = []
    minEstDiameterList = []
    maxEstDiameterList = []
    auMissDistanceList = []
    absMagnitudeList = []
    isHazardousList = []

    if apiResponse.status_code == 200:
        remainRateLimit = apiResponse.headers["X-RateLimit-Remaining"]
        apiAnswer = json.loads(apiResponse.text)
        asteroidList = apiAnswer[objects]
        for i in range(dayDifference+1):
            for asteroid in asteroidList[str(date)]:
                nameList.append(asteroid["name"])
                approachDateList.append(
                    asteroid["close_approach_data"][0]["close_approach_date_full"])
                relVelocityList.append(
                    asteroid["close_approach_data"][0]["relative_velocity"]["kilometers_per_second"])
                minEstDiameterList.append(
                    asteroid["estimated_diameter"]["kilometers"]["estimated_diameter_min"])
                maxEstDiameterList.append(
                    asteroid["estimated_diameter"]["kilometers"]["estimated_diameter_max"])
                auMissDistanceList.append(
                    asteroid["close_approach_data"][0]["miss_distance"]["astronomical"])
                absMagnitudeList.append(asteroid["absolute_magnitude_h"])
                isHazardousList.append(
                    asteroid["is_potentially_hazardous_asteroid"])
            date += timedelta(days=1)
        df = pd.DataFrame(data={
                          "Name": nameList, "Approach Date": approachDateList, "Relative Velocity": relVelocityList, "Min Estimated Diameter": minEstDiameterList, "Max Estimated Diameter": maxEstDiameterList, "Miss Distance (AU)": auMissDistanceList, "Absolute Magnitude": absMagnitudeList, "Hazardous": isHazardousList})
        return df, df.to_csv(sep=',', index=False), remainRateLimit
    else:
        st.error("API Key is wrong")


def detailPage():

    st.write("""  # Neo: Near Earth Observation""")
    st.write("""   This app aims to simplify the usage of Nasa Public API for who wanna observe asteroids approaching to the Earth. """)
    st.write("")

    col1, col2, col3 = st.columns(3)
    apiKey = col1.text_input("Nasa API Key")
    startDate = col2.date_input("Start Date")
    endDate = col3.date_input("End Date")

    st.write()
    if startDate > endDate:
        st.error("The start date can't be greater than the end date !")
    elif (endDate-startDate) <= timedelta(days=7):
        if apiKey != "" and len(apiKey) == 40:
            observationResult = Observe(
                apiKey, startDate, endDate)
            if observationResult != None:
                observationDataDf, observationDataCsv, apiLimit = observationResult
                col1.download_button("Download CSV", observationDataCsv,
                                     "asteroidData.csv", "text/csv")
                st.dataframe(observationDataDf)
                col2.write("API Remain Usage Limit: "+apiLimit)
        elif apiKey != "" and len(apiKey) != 40:
            st.warning("API Key length should be 40.")
    else:
        st.error(
            "The end date can be a maximum of 7 days greater than the start date !")
