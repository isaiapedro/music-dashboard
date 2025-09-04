# Dashboard for 1001 Albums by Pedro
from narwhals import col
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import math
from PIL import Image

# Page config
st.set_page_config(page_title="1001 Albums by Pedro", layout="wide")
# --- Custom CSS Styling ---
st.markdown("""
    <style>
        body {
            background-color: #f4f4f4;
        }
        .main-title {
            background-color: #636EFA;
            padding: 20px;
            border-radius: 8px;
            color: white;
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        footer {visibility: hidden;}

    background-color: #f4f4f4;

    </style>
""", unsafe_allow_html=True)


# Load datasets
# Current Album data
df1 = pd.read_json('current_album.json', lines=True)
df1.columns = df1.columns.str.strip().str.lower()

# Past Albums data
df2 = pd.read_json("albums.json", lines=True)
df2.columns = df2.columns.str.strip().str.lower()

# Calculate the difference between personal and global ratings
df2['rating_diff'] = df2['rating'] - df2['globalrating']

# KPIs
average_rate = df2['rating'].mean()
total_albums = df2.shape[0]
best_streak = df2['streak'].max()
worst_streak = df2['streak'].min()

# Count the frequency of each genre
genre_counter = Counter()
df2['allgenres'].str.split(', ').apply(genre_counter.update)
most_common_genres = genre_counter.most_common(10)


# Divide release date by decades
def get_decade(year):
    return f"{year // 10 * 10}s"


df2['releasedate'] = pd.to_numeric(df2['releasedate'], errors='coerce')
df2['decade'] = df2['releasedate'].apply(get_decade)


# --- Dashboard Layout ---
# Title

st.markdown('<div class="main-title">1001 Albums by Pedro</div>', unsafe_allow_html=True)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("🔁 Average Rating", f"{average_rate:.2} stars")
kpi2.metric("👥 Albums Listened", f"{total_albums:,}")
kpi3.metric("🌟 Best Streak", f"{best_streak:.2} stars")
kpi4.metric("⚠️ Worst Streak", f"{worst_streak:.2} stars")
st.markdown('---')

col1, col2, col3 = st.columns([1, 1, 2])
# Current Album
with col1:
    st.subheader("🎶 Current Album")

    # Display current album details in grid
    st.image(df1['images'].iloc[0])

with col2:
    st.subheader("")
    st.markdown(
        f'''
        <p style='font-size:40px; color: violet; margin-bottom: -5px; font-weight:bold;'>{df1['name'].iloc[0]}</p>
        <p style='font-size:28px; color: white; margin-bottom: -2px;'>{df1['artist'].iloc[0]}</p>
        <p style='font-size:24px; color: white; margin-bottom: -4px; font-weight:bold;'>{df1['releasedate'].iloc[0]}</p>
        <p style='font-size:20px; color: white; '>{df1['genres'].iloc[0]}</p>
        ''', unsafe_allow_html=True)
    st.markdown('')
    st.link_button(label="Youtube",  icon="▶️", type='primary', url="https://youtube.com/playlist?list=" + df1['youtubemusicid'].iloc[0])
    st.link_button(label="Spotify", icon="🎧", type='secondary', url="https://open.spotify.com/album/" + df1['spotifyid'].iloc[0])      

# Show Top Rated Albums and Lowest Rated Albums
with col3:
    st.subheader("🌟 Top Rated Albums")
    top_rated = df2.nlargest(3, 'rating')
    st.markdown("""
        <style>
            .stTable tr {
            }
        </style>
    """, unsafe_allow_html=True)
    st.table(top_rated[['name', 'artist', 'rating']].set_index('name'))

    st.subheader("⚠️ Lowest Rated Albums")
    lowest_rated = df2.nsmallest(3, 'rating')
    st.table(lowest_rated[['name', 'artist', 'rating']].set_index('name'))

st.markdown('---')

# 📅 Albums over the years
st.subheader("📅 Albums over the Years")

# Get counts per decade and sort by decade
plot_df_decades = pd.DataFrame()
if not df2.empty and 'decade' in df2.columns:
    decade_counts = df2['decade'].value_counts().sort_index()
    if not decade_counts.empty:
        plot_df_decades = pd.DataFrame({'count': decade_counts}).reset_index()
        plot_df_decades.rename(columns={'index': 'decade'}, inplace=True)

if not plot_df_decades.empty:
    # Generate image paths for each decade, assuming they are in an 'assets' folder
    plot_df_decades['image_path'] = plot_df_decades['decade'].apply(lambda d: f"assets/{d}.jpg")

    # Check if all decade images exist, otherwise fallback to a bar chart
    fallback_to_bar_decades = False
    for image_path in plot_df_decades['image_path']:
        try:
            with Image.open(image_path):
                pass
        except FileNotFoundError:
            st.warning(f"Decade image not found at '{image_path}'. Displaying a standard bar chart for decades.")
            fallback_to_bar_decades = True
            break

    if fallback_to_bar_decades:
        fig_decades = px.bar(plot_df_decades, x='decade', y='count', text='count', color_discrete_sequence=['#636EFA'], category_orders={"decade": sorted(df2['decade'].unique())})
        fig_decades.update_traces(textposition='outside')
    else:
        fig_decades = go.Figure()
        fig_decades.add_trace(go.Bar(
            x=plot_df_decades['decade'], y=plot_df_decades['count'], text=plot_df_decades['count'],
            textposition='outside', marker_color='rgba(0,0,0,0)'
        ))
        for _, row in plot_df_decades.iterrows():
            fig_decades.add_layout_image(
                source=Image.open(row['image_path']),
                xref="x", yref="y", x=row['decade'], y=row['count'] / 2,
                sizex=0.8, sizey=row['count'],
                xanchor="center", yanchor="middle",
                sizing="stretch", layer="below"
            )

    max_count_decades = plot_df_decades['count'].max()
    fig_decades.update_layout(yaxis_title="Number of Albums", showlegend=False, template="plotly_white", xaxis={'categoryorder': 'category ascending'})
    fig_decades.update_yaxes(dtick=1, range=[0, max_count_decades * 1.15 if max_count_decades > 0 else 1])
    fig_decades.update_xaxes(tickfont_size=17)
    st.plotly_chart(fig_decades, use_container_width=True)
else:
    st.info("No decade data to display.")

st.markdown("---")

# Show three latest reviews
st.subheader("📝 Latest Reviews")

# Get the last 3 albums, ensuring we don't go out of bounds if there are fewer than 3
# .iloc[::-1] reverses the order to show the most recent first
if not df2.empty:
    num_reviews = min(3, len(df2))
    latest_reviews_df = df2.tail(num_reviews).iloc[::-1]

    for _, row in latest_reviews_df.iterrows():
        col_img, col_info, col_video = st.columns([1, 2, 2])  # Add column for video

        with col_img:
            st.markdown('')
            st.image(row['images'])

        with col_info:
            st.markdown(
                f"""
                <p style='font-size:28px; color: #ba55d3; font-weight:bold; margin-bottom: -10px;'>{row['name']}</p>
                <p style='font-size:20px; color: white; margin-bottom: -4px;'>{row['artist']}</p>
                <p style='font-size:17px; color: white; margin-bottom: -4px;'>{row['releasedate']}</p>
                """, unsafe_allow_html=True)
            st.subheader(f"⭐ Rating: {row['rating']}")
            review_text = row['review']
            if pd.notna(review_text) and review_text:
                # Format review to replace both newlines and slashes with HTML line breaks
                formatted_review = str(review_text).replace('\n', '<br>').replace('/', '<br>')
                st.markdown(f"<p style='font-size:18px; color: white;'>{formatted_review}</p>", unsafe_allow_html=True)

        with col_video:
            if 'youtubemusicid' in row and pd.notna(row['youtubemusicid']):
                playlist_id = row['youtubemusicid']
                # The recommended URL for embedding a playlist
                embed_url = f"https://www.youtube.com/embed/videoseries?list={playlist_id}"
                components.html(f'<iframe src="{embed_url}" width="80%" height="280" frameborder="0" allowfullscreen></iframe>', height=315)

        st.markdown("---")  # Separator for each review
else:
    st.info("No reviews to display.")

# Top genres
st.subheader("🎵 Top Genres")
genres, counts = zip(*most_common_genres)
fig2 = px.bar(x=genres, y=counts, labels={'x': 'Genre', 'y': 'Count'})
# Customize colors, make barsize bigger and make xlabel bigger
fig2.update_yaxes(title_text='Number of Albums', dtick=1)
color = px.colors.qualitative.Plotly
fig2.update_layout(showlegend=False)
fig2.update_traces(marker_color=color, marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.8)
fig2.update_xaxes(tickangle=-45, title_text=None, tickfont_size=14)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Show Highest Rated and Lowest Rated Albums vs Global Ratings
col17, col18 = st.columns(2, gap="large")
with col17:
    st.markdown("<p style='font-weight:bold; text-align:center; font-size: 20px; color:#636EFA;'>📈 Highest Rated Album vs Global Rating", unsafe_allow_html=True)
    # Get top ncols albums where my rating is highest compared to global
    ncols = 3
    overrated_albums = df2.nlargest(ncols, 'rating_diff')

    # Create a ncols-column grid
    cols = st.columns(ncols)

    # Iterate over the columns and the album data simultaneously
    for i, col in enumerate(cols):
        if i < len(overrated_albums):
            album = overrated_albums.iloc[i]
            with col:
                st.image(album['images'], use_container_width=True)
                st.markdown(f"<p style='text-align:center; color: #33ff33; font-size: 18px; font-weight:bold;'>+{album['rating_diff']:.2f}</p>", unsafe_allow_html=True)

with col18:
    st.markdown("<p style='font-weight:bold; text-align:center; font-size: 20px; color:#ff4d4d;'> 📉 Lowest Rated Album vs Global Rating", unsafe_allow_html=True)
    # Get top ncols albums where my rating is lowest compared to global
    # Sort descending to show the album with the most negative difference last.
    underrated_albums = df2.nsmallest(ncols, 'rating_diff').sort_values(by='rating_diff', ascending=False)

    # Create a ncols-column grid
    cols = st.columns(ncols)

    # Iterate over the columns and the album data simultaneously
    for i, col in enumerate(cols):
        if i < len(underrated_albums):
            album = underrated_albums.iloc[i]
            with col:
                st.image(album['images'], use_container_width=True)
                st.markdown(f"<p style='text-align:center; color: #ff4d4d; font-size: 18px; font-weight:bold;'>{album['rating_diff']:.2f}</p>", unsafe_allow_html=True)

st.markdown("---")

# Plot Albums by Location
st.subheader("📍 Albums by Location")

# Get counts for USA, UK, and Other
origin_counts = df2['artistorigin'].value_counts()
usa_data = int(origin_counts.get('us', 0))
uk_data = int(origin_counts.get('uk', 0))
other_data = total_albums - usa_data - uk_data

# Data for plotting
origins = ['USA', 'UK', 'Other']
counts = [usa_data, uk_data, other_data]
flag_paths = ['assets/us_flag.png', 'assets/uk_flag.jpg', 'assets/other_flag.jpg']

# Filter out origins with 0 albums and prepare data for plotting
plot_data = [{'origin': o, 'count': c, 'flag': f} for o, c, f in zip(origins, counts, flag_paths) if c > 0]

if plot_data:
    plot_df = pd.DataFrame(plot_data)

    # Check if all flag images exist
    images_exist = True
    for flag_path in plot_df['flag']:
        try:
            with Image.open(flag_path):
                pass
        except FileNotFoundError:
            st.warning(f"Flag image not found at '{flag_path}'. The pie chart will be displayed without images.")
            images_exist = False
            # We don't break, so the pie chart still renders without images.

    # Define a color map for the pie chart slices
    color_map = {'USA': '#ff4d4d', 'UK': '#636EFA', 'Other': 'white'}
    plot_colors = plot_df['origin'].map(color_map).tolist()

    # Create the pie chart
    fig_location = go.Figure(go.Pie(
        labels=plot_df['origin'],
        values=plot_df['count'],
        hoverinfo='label+value+percent',
        textinfo='percent',
        marker=dict(colors=plot_colors),
        sort=False
    ))

    # If images exist, overlay them on the pie chart
    if images_exist:
        # Make the percentage text on the slices transparent to not clash with the image
        fig_location.update_traces(textfont=dict(color='rgba(0,0,0,0)'))

        total_count = plot_df['count'].sum()
        cumulative_percent = 0
        normalized_values = plot_df['count'] / total_count

        for i, val in enumerate(normalized_values):
            # Calculate the middle angle of the slice
            slice_angle = val * 2 * math.pi
            mid_angle = (cumulative_percent * 2 * math.pi) + (slice_angle / 2)

            # Position the image inside the slice. The pie is in a [0,1] x [0,1] paper domain.
            # Center is (0.5, 0.5). We place the image at a certain radius from the center.
            radius = 0.35  # Adjust this to position the image
            x_pos = 0.5 + radius * math.cos(mid_angle)
            y_pos = 0.5 + radius * math.sin(mid_angle)

            fig_location.add_layout_image(
                source=Image.open(plot_df['flag'].iloc[i]),
                xref="paper", yref="paper",
                x=x_pos, y=y_pos,
                sizex=0.2, sizey=0.2,  # Adjust size as needed
                xanchor="center", yanchor="middle",
                sizing="contain", layer="above"
            )
            cumulative_percent += val

    fig_location.update_layout(
        showlegend=True,
        template="plotly_white",
    )
    st.plotly_chart(fig_location, use_container_width=True)
else:
    st.info("No location data to display.")
