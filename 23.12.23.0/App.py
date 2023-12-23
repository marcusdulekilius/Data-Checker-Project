import json
from faker import Faker
import random
from tqdm import tqdm  # tqdm kütüphanesini ekleyin
import matplotlib.pyplot as plt
from collections import Counter

fake = Faker()

def generate_user(unique_usernames, common_usernames):
    username = fake.user_name()
    name = fake.name()
    followers_count = random.randint(30, 200)
    following_count = random.randint(30, 200)

    # Ensure common usernames are present in both followers and followings
    user_followers = random.sample(common_usernames, min(followers_count, len(common_usernames)))
    user_followings = random.sample(common_usernames, min(following_count, len(common_usernames)))

    # Generate some unique usernames
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
    # Generate common usernames
    common_usernames = [fake.user_name() for _ in range(50)]  # Adjust the number as needed

    # Generate unique usernames
    unique_usernames = set()
    while len(unique_usernames) < num_users:
        unique_usernames.add(fake.user_name())

    dataset = []

    for _ in range(num_users):
        user_data = generate_user(unique_usernames, common_usernames)
        dataset.append(user_data)

    return dataset

if __name__ == "__main__":
    num_users = 50

    dataset = generate_dataset(num_users)

    with tqdm(total=len(dataset), desc="Generating Dataset", unit="users") as pbar:
        for idx, user_data in enumerate(dataset):
            pbar.set_postfix(current_user=f"User {idx+1}/{num_users}")
            pbar.update(1)
    # Convert the dataset to JSON format
    json_dataset = json.dumps(dataset, indent=4)

    # Save the dataset to a file
    with open("Similarity_Dataset.json", "w") as file:
        file.write(json_dataset)
        
     # Tweetlerdeki tüm kelimeleri toplama
    all_tweets = [tweet for user in dataset for tweet in user['tweets']]
    
    # Tüm tweetleri birleştirerek tek bir metin oluşturma
    combined_text = ' '.join(all_tweets)
    
    # Metni kelimelere ayırarak kelime frekanslarını hesaplama
    words = combined_text.split()
    word_counts = Counter(words)
    
    # En çok tekrar eden kelimeleri ve frekanslarını seçme
    top_words = word_counts.most_common(10)  # En çok tekrar eden ilk 10 kelime
    
    # Grafik oluşturma
    top_words, top_counts = zip(*top_words)
    plt.figure(figsize=(18, 6))

    # Tweetlerde en çok tekrar eden kelimelerin grafiği
    plt.subplot(1, 3, 1)
    plt.bar(top_words, top_counts, color='skyblue')
    plt.xlabel('Kelimeler')
    plt.ylabel('Tekrar Sayısı')
    plt.title('Tweetlerde En Çok Tekrar Eden Kelimeler')
    plt.xticks(rotation=45)  

    # Kelime ve tekrar sayısını gösteren metin
    text = '\n'.join([f"{word}: {count}" for word, count in zip(top_words, top_counts)])
    plt.subplot(1, 3, 2)
    plt.text(0.5, 0.5, text, ha='center', va='center', fontsize=12)
    plt.axis('off')

    # Kullanıcıların takipçi sayılarının grafiği
    followers_counts = [user['followers_count'] for user in dataset]
    plt.subplot(1, 3, 3)
    plt.hist(followers_counts, bins=10, color='lightgreen')
    plt.xlabel('Takipçi Sayısı Aralığı')
    plt.ylabel('Kullanıcı Sayısı')
    plt.title('Kullanıcıların Takipçi Sayıları')

    plt.tight_layout()
    plt.show()
