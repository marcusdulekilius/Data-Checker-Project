import json
from faker import Faker
import random
from tqdm import tqdm
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import networkx as nx

fake = Faker()

def generate_user(unique_usernames, common_usernames):
    username = fake.user_name()
    name = fake.name()
    followers_count = random.randint(30, 200)
    following_count = random.randint(30, 200)

    user_followers = random.sample(common_usernames, min(followers_count, len(common_usernames)))
    user_followings = random.sample(common_usernames, min(following_count, len(common_usernames)))

    unique_followers = random.sample(unique_usernames, min(followers_count - len(user_followers), len(unique_usernames)))
    unique_followings = random.sample(unique_usernames, min(following_count - len(user_followings), len(unique_usernames)))

    user_followers.extend(unique_followers)
    user_followings.extend(unique_followings)

    return {
        "username": username,
        "name": name,
        "followers_count": followers_count,
        "following_count": following_count,
        "language": fake.language_code(),
        "region": fake.country_code(),
        "tweets": [fake.sentence() for _ in range(random.randint(10, 50))],
        "followers": user_followers,
        "following": user_followings
    }

def generate_dataset(num_users):
    common_usernames = [fake.user_name() for _ in range(50)]

    unique_usernames = set()
    while len(unique_usernames) < num_users:
        unique_usernames.add(fake.user_name())

    dataset = []

    for _ in range(num_users):
        user_data = generate_user(unique_usernames, common_usernames)
        dataset.append(user_data)

    return dataset

# Kullanıcı ilgi alanlarını gruplama fonksiyonu
def group_users_by_interest_similarity(dataset, similarity_scores):
    interest_similarity = defaultdict(list)

    for (username1, username2), similarity in similarity_scores.items():
        if similarity > 0.5:  # Benzerlik eşiği (istenilen benzerlik seviyesine göre ayarlanabilir)
            for interest in dataset[username1]['interests']:
                interest_similarity[(username1, username2)].append(interest)

if __name__ == "__main__":
    num_users = 50
    dataset = generate_dataset(num_users)

    with tqdm(total=len(dataset), desc="Generating Dataset", unit="users") as pbar:
        for idx, user_data in enumerate(dataset):
            pbar.set_postfix(current_user=f"User {idx+1}/{num_users}")
            pbar.update(1)
            
    json_dataset = json.dumps(dataset, indent=4)

    with open("Similarity_Dataset.json", "w") as file:
        file.write(json_dataset)
        
     # Tweetlerdeki tüm kelimeleri toplama
    all_tweets = [tweet for user in dataset for tweet in user['tweets']]
    
    # Tüm tweetleri birleştirerek tek bir metin oluşturma
    combined_text = ' '.join(all_tweets)
    
    # Metni kelimelere ayırarak kelime frekanslarını hesaplama
    words = combined_text.split()
    word_counts = Counter(words)
    # Tüm kullanıcıların takipçi sayılarını içeren liste
    followers_counts = [user['followers_count'] for user in dataset]
    # En çok tekrar eden kelimeleri ve frekanslarını seçme
    top_words = word_counts.most_common(25)  # En çok tekrar eden ilk 25 kelime
     # Her bir kullanıcının en çok tekrar eden kelimeleri tutacak bir sözlük oluşturulması
    user_top_words = {}
    for user in dataset:
        user_tweets = user['tweets']
        all_user_words = [tweet.split() for tweet in user_tweets]
        user_words = [word for sublist in all_user_words for word in sublist]
        user_word_counts = Counter(user_words)
        user_top_words[user['username']] = user_word_counts.most_common(200)  # Her kullanıcının en çok tekrar eden 200 kelimesi

    # Benzerlikleri tutacak bir sözlük oluşturulması
    similarity_scores = {}
    for username1, top_words1 in user_top_words.items():
        for username2, top_words2 in user_top_words.items():
            if username1 != username2 and (username2, username1) not in similarity_scores:
                # Jaccard benzerlik indeksi hesaplama
                intersection = len(set(dict(top_words1).keys()) & set(dict(top_words2).keys()))
                union = len(set(dict(top_words1).keys()) | set(dict(top_words2).keys()))
                similarity = intersection / union if union != 0 else 0
                similarity_scores[(username1, username2)] = similarity
               
    # Kullanıcıları ilgi alanlarına göre gruplama
    interest_similarity = group_users_by_interest_similarity(dataset, similarity_scores)
    G = nx.Graph()
    for user_data in dataset:
        username = user_data['username']
        followers = user_data['followers']
        for follower in followers:
            G.add_edge(username, follower)
        
    interest_similarity = group_users_by_interest_similarity(dataset, similarity_scores)

    for (username1, username2), similarity in similarity_scores.items():
        if similarity > 0.3:  # İstenilen benzerlik eşiği
            G.add_edge(username1, username2, weight=1 / similarity)  # Ağırlık, benzerlik skorunun tersi olarak atanır

    # Minimum Spanning Tree oluşturma
    mst = nx.minimum_spanning_tree(G)

    # Ağı çizme
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(mst)
    nx.draw(mst, pos, with_labels=True, node_size=200, font_size=8)
    plt.title('Benzer İlgi Alanlarına Sahip Kullanıcılar Arasındaki İlişkiler')

    # Benzerlik skorlarını en yüksekten sıralayarak al
    top_100_similarities = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)[:100]
    top_100_user_pairs = [f"{users[0]} - {users[1]}" for (users, similarity) in top_100_similarities]
    top_100_similarities_values = [similarity for (users, similarity) in top_100_similarities]

    # Benzerlik skorlarını yatay histogram şeklinde gösterme
    plt.figure(figsize=(12, 10))
    plt.barh(top_100_user_pairs, top_100_similarities_values, color='skyblue')
    plt.xlabel('Benzerlik Skoru')
    plt.ylabel('Kullanıcı Çiftleri')
    plt.title('En Yüksek Benzerlik Skorları (Top 100)')
    plt.tight_layout()

    # Benzerlik skorlarını çubukların ucuna yazma
    for i, similarity in enumerate(top_100_similarities_values):
        plt.text(similarity + 0.01, i, round(similarity, 2), ha='left', va='center', fontsize=8)

    # Tweetlerde en çok tekrar eden kelimelerin grafiği
    top_words, top_counts = zip(*top_words)
    plt.figure(figsize=(10, 6))
    plt.bar(top_words, top_counts, color='skyblue')
    plt.xlabel('Kelimeler')
    plt.ylabel('Tekrar Sayısı')
    plt.title('Tweetlerde En Çok Tekrar Eden Kelimeler')
    plt.xticks(rotation=45)
    
    # Her çubuğun üstüne tekrar sayısını yazma
for i, count in enumerate(top_counts):
    plt.text(i, count + 0.1, str(count), ha='center', va='bottom', fontsize=8)
  
# Ağı çizme
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G) 
nx.draw(G, pos, with_labels=True, node_size=200, font_size=8)
plt.title('Kullanıcı Takipçileri Arasındaki İlişkiler')
    
# Tüm kullanıcıların takipçi sayılarını tek bir çubuk grafikte gösterme
plt.figure(figsize=(10, 6))
bars = plt.bar(range(len(followers_counts)), followers_counts, color='skyblue')
plt.xlabel('Kullanıcılar')
plt.ylabel('Takipçi Sayısı')
plt.title('Tüm Kullanıcıların Takipçi Sayıları')
plt.xticks(range(len(followers_counts)), [user['username'] for user in dataset], rotation=90)
plt.tight_layout()

# Kullanıcı adlarını çubukların üzerine yazdırma
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval), ha='center', va='bottom', color='black', fontsize=8)

plt.show()
