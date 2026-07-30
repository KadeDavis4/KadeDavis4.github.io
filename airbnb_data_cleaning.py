import pandas


cal_2026 = pandas.read_csv('calendar.csv.gz')
cal_2025 = pandas.read_csv('calendar2025.csv.gz')       
listings_2026 = pandas.read_csv('listings.csv.gz')      
listings_2025 = pandas.read_csv('listings2025.csv.gz')

#Cleanup needed prices for calendar and listings
listings_2026['price'] = listings_2026['price'].replace('[\$,]', '', regex=True).astype(float)
cal_2025['adjusted_price'] = cal_2025['adjusted_price'].replace('[\$,]', '', regex=True).astype(float)


#Make 2025 trendline data
cal_2025['month_name'] = pandas.to_datetime(cal_2025['date']).dt.strftime('%b')
cal_2025['month_num'] = pandas.to_datetime(cal_2025['date']).dt.month

cal_2025 = cal_2025.merge(listings_2025[['id', 'neighbourhood_group_cleansed']], left_on='listing_id', right_on='id')

monthly = cal_2025.groupby(['neighbourhood_group_cleansed', 'month_num', 'month_name']).agg(
    avg_price=('adjusted_price', 'mean'),
    occupancy=('available', lambda x: 1 - x.eq('t').mean())
).reset_index()

monthly.to_csv('calendar_clean.csv', index=False)



# --------------------------------------------------------------
# Main summary data and host delta
# --------------------------------------------------------------


#Primary summary data
cal_2026['month'] = pandas.to_datetime(cal_2026['date']).dt.month

cal_2026 = cal_2026.merge(listings_2026[['id', 'neighbourhood_group_cleansed']], left_on='listing_id', right_on='id')

occupancy_2026 = cal_2026.groupby('neighbourhood_group_cleansed').agg(
    occupancy=('available', lambda x: 1 - x.eq('t').mean())
).reset_index()

price_2026 = listings_2026.groupby('neighbourhood_group_cleansed').agg(
    avg_price=('price', 'mean')
).reset_index()

neighbourhood_summary = occupancy_2026.merge(price_2026, on='neighbourhood_group_cleansed')


#Host delta
hosts_current = listings_2026.groupby('neighbourhood_group_cleansed')['id'].count().reset_index()
hosts_current.columns = ['neighbourhood_group_cleansed', 'host_count_current']

hosts_2025 = listings_2025.groupby('neighbourhood_group_cleansed')['id'].count().reset_index()
hosts_2025.columns = ['neighbourhood_group_cleansed', 'host_count_2025']

host_delta = hosts_current.merge(hosts_2025, on='neighbourhood_group_cleansed')
host_delta['host_delta'] = host_delta['host_count_current'] - host_delta['host_count_2025']

host_delta.to_csv('host_delta.csv', index=False)


#Merge host delta onto summary
neighbourhood_summary = neighbourhood_summary.merge(
    host_delta[['neighbourhood_group_cleansed', 'host_count_current', 'host_count_2025', 'host_delta']],
    on='neighbourhood_group_cleansed'
)


#Save csv
neighbourhood_summary.to_csv('neighbourhood_summary_2026.csv', index=False)

