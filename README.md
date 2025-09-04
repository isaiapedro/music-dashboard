# Music Dashboard

## Contents

- [How to run](#how-to-run)
- [Introduction](#introduction)
- [Data Overview](#data-overview)
- [Results](#results)
- [Conclusion](#conclusion)
  
## How to Run

<br>

For now to run the app it is needed to install the python libraries located in the requirements file, but in the future i'll make a docker image to make the process a little easier. Follow the command below.

<br>

```
pip install -r requirements.txt
```

<br>

And run the stremlit app as it's shown below.

<br>

```
streamlit run Dashboard.py
```

## Introduction

This is the first part of a project to show data in a comprehensive way using the common APIs like Apple and Spotify. We're also working on a recommendation system.

<br/>

The data was used via an API from the website [www.1001albumsgenerator.com](www.1001albumsgenerator.com). The collected data was cleaned using two Json files, for the current album that's being used and the previous albums on the
user history section. Some transformations were made and the data was stored in the same Json files. Then the data was display using Streamlit and Plotly libraries.

<br/>

## Data Overview

The data given by the website is very nested. So i had to untangle the nested lists into new dataframes. The first dataframe is based on the content inside 'currentAlbum', which is a label that shows basic information about the 
current album being listened.

<br>

shareableUrl | currentAlbum | currentAlbumNotes |	updateFrequency |	history |	name
--- | --- | --- | --- | --- | ---
link | nested list | string | string | nested list | string

<br>

The second dataframe was based on 'album', that's a nested label inside 'history'. Using different dataframes for each level of the nested list was very useful to recover data for different levels. For instance, collecting ratings for the albums
that was in the upper level of nested list. 
After collecting the data, it weas necessary to apply lambda functions to get single elements from list elements and to transform lists as string elements.

<br>

The last step is to display data in a comprehensive way, using different plots for ratings, years, genres and nationality. This was done importing the Json file directly in the streamlit app.

## Results

**Images of the application that can be acessed with [this link](https://churn-dash.streamlit.app/).**

![](https://github.com/isaiapedro/music-dashboard/blob/main/assets/homepage1.png)

<br>
<br>

![](https://github.com/isaiapedro/music-dashboard/blob/main/assets/homepage2.png)

## Conclusion

Thanks for reading up until here. I had a ton of fun doing this project and got a lot of useful insights on APIs, Python scripts and how to work with Streamlit applications.

If you want to see more projects, see the [Basketball Statistics App](https://github.com/isaiapedro/nba-app) or go to my github page. Feel free to reach me on [LinkedIn](https://www.linkedin.com/in/isaiapedro/) or my [Webpage](https://github.com/isaiapedro/Portfolio-Website).

Bye! 👋
