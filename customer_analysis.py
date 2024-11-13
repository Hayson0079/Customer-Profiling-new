import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.cluster import KMeans

from data_functions import read_customer_info

customer_stat = pd.read_csv('result/Customer stat.csv')
customer_stat = customer_stat.fillna(0)
customer_stat['last_bet_time'] = pd.to_datetime(customer_stat['last_bet_time'])
customer_stat['last_bet_time_day'] = (pd.Timestamp('2024-11-01').tz_localize('UTC') - customer_stat['last_bet_time']).dt.days
learning_stat = customer_stat[['no_of_diff_bet', 'rejected_bet_rate', 'alert_IP_rate', 'avg_max_bet_rate', 'follow_sharp_bet_rate',
                                'opposite_sharp_bet_rate', 'avg_point_diff_with_sharp_bet', 'avg_mean_stake', 'avg_pnl',
                                'ir_bet_rate', 'bet_frequency', 'roi', 'roi_level_stake', 'last_bet_time_day']]

'''
# outlier model
isolation_model = IsolationForest(contamination=0.05, random_state=0)
learning_stat['Outlier_Scores'] = isolation_model.fit_predict(learning_stat.iloc[:, 1:].to_numpy())
learning_stat['Is_Outlier'] = [1 if x == -1 else 0 for x in learning_stat['Outlier_Scores']]
'''

# corr map
sns.set_style('whitegrid')
corr = learning_stat.corr()
colors = ['#ff6200', '#ffcaa8', 'white', '#ffcaa8', '#ff6200']
my_cmap = LinearSegmentedColormap.from_list('custom_map', colors, N=256)
mask = np.zeros_like(corr)
mask[np.triu_indices_from(mask, k=1)] = True

plt.figure(figsize=(12,10))
sns.heatmap(corr, mask=mask, cmap=my_cmap, annot=True, center=0, fmt='.2f', linewidths=2)
plt.title('Correlation Matrix', fontsize=14)
plt.show()

# scale
scaler = StandardScaler()
scaled_learning_stat = scaler.fit_transform(learning_stat)

# PCA
pca = PCA().fit(scaled_learning_stat)
explained_variance_ratio = pca.explained_variance_ratio_
cumulative_explained_variance = np.cumsum(explained_variance_ratio)

optimal_k = 9
plt.figure(figsize=(20, 10))
barplot = sns.barplot(x=list(range(1, len(cumulative_explained_variance) + 1)),
                      y=explained_variance_ratio,
                      color='#fcc36d',
                      alpha=0.8)
lineplot, = plt.plot(range(0, len(cumulative_explained_variance)), cumulative_explained_variance,
                     marker='o', linestyle='--', color='#ff6200', linewidth=2)
optimal_k_line = plt.axvline(optimal_k - 1, color='red', linestyle='--', label=f'Optimal k value = {optimal_k}') 
plt.xlabel('Number of Components', fontsize=14)
plt.ylabel('Explained Variance', fontsize=14)
plt.title('Cumulative Variance vs. Number of Components', fontsize=18)
plt.xticks(range(0, len(cumulative_explained_variance)))
plt.legend(handles=[barplot.patches[0], lineplot, optimal_k_line],
           labels=['Explained Variance of Each Component', 'Cumulative Explained Variance', f'Optimal k value = {optimal_k}'],
           loc=(0.62, 0.1),
           frameon=True,
           framealpha=1.0,  
           edgecolor='#ff6200')  
x_offset = -0.3
y_offset = 0.01
for i, (ev_ratio, cum_ev_ratio) in enumerate(zip(explained_variance_ratio, cumulative_explained_variance)):
    plt.text(i, ev_ratio, f"{ev_ratio:.2f}", ha="center", va="bottom", fontsize=10)
    if i > 0:
        plt.text(i + x_offset, cum_ev_ratio + y_offset, f"{cum_ev_ratio:.2f}", ha="center", va="bottom", fontsize=10)

plt.grid(axis='both')   
plt.show()


pca = PCA(n_components=9)
learning_stat_pca = pca.fit_transform(scaled_learning_stat)

def elbow_method(data):
    inertia = []
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, n_init=10, init='k-means++', random_state=42)
        kmeans.fit(data)
        inertia.append(kmeans.inertia_)

    plt.plot(range(1, 11), inertia, marker='o')
    plt.xlabel('Number of clusters')
    plt.ylabel('Inertia')
    plt.title('Elbow Method for Optimal k')
    plt.show()

def silhouette_scores(data):
    silhouette_scores = []
    k_values = range(2, 20)
    for k in k_values:
        kmeans = KMeans(n_clusters=k, n_init=10, init='k-means++', random_state=42)
        cluster_labels = kmeans.fit_predict(data)
        silhouette_avg = silhouette_score(data, cluster_labels)
        silhouette_scores.append(silhouette_avg)

    # Plot the silhouette scores
    plt.figure(figsize=(10, 6))
    plt.plot(k_values, silhouette_scores, marker='o')
    plt.title('Silhouette Score Method for Optimal k')
    plt.xlabel('Number of clusters')
    plt.ylabel('Silhouette Score')
    plt.grid(True)
    plt.show()

elbow_method(scaled_learning_stat)
silhouette_scores(scaled_learning_stat)

kmeans = KMeans(n_clusters=5, init='k-means++', n_init=10, max_iter=100, random_state=0)
clusters = kmeans.fit_predict(scaled_learning_stat)

result = customer_stat[['name', 'no_of_diff_bet', 'rejected_bet_rate', 'alert_IP_rate', 'avg_max_bet_rate', 'follow_sharp_bet_rate',
                        'opposite_sharp_bet_rate', 'avg_point_diff_with_sharp_bet', 'avg_mean_stake', 'avg_pnl',
                        'ir_bet_rate', 'bet_frequency', 'roi', 'roi_level_stake', 'last_bet_time_day']]

result['Cluster'] = clusters

