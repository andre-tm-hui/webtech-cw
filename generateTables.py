import pandas as pd
import numpy as np

max_genres = 5

ratings = pd.read_csv("ratings.csv")
books = pd.read_csv("books.csv")
book_tags = pd.read_csv("book_tags.csv")
tags = pd.read_csv("tags.csv")
with open("tag_filter.txt", "r") as f:
	tag_filter = f.read().split("\n")
print(tag_filter)
#tag_filter = ["to-read", "currently-reading", "favorites", "books-i-own", "owned", "book_club", "default", "ya"]
tag_list = {}

books.drop(["best_book_id","work_id","books_count","isbn","isbn13","authors","original_publication_year","original_title","average_rating","ratings_count","work_ratings_count","work_text_reviews_count","ratings_1","ratings_2","ratings_3","ratings_4","ratings_5","image_url","small_image_url", "language_code"], axis = 1, inplace = True)

genre_list = []

for index, row in books.iterrows():
	goodreads_book_id = row["goodreads_book_id"]
	tags_by_id = book_tags.loc[book_tags["goodreads_book_id"] == goodreads_book_id]
	genres = []
	num_genres = 0
	i = 0
	while num_genres < max_genres:
		tag_id = tags_by_id["tag_id"].iloc[[i]].tolist()[0]
		genre = tags.loc[tags["tag_id"] == tag_id]["tag_name"].tolist()[0]
		if genre not in tag_filter:
			with open("tags.txt","a+") as f:
				try:
					if genre not in tag_list:
						f.write(genre + "\n")
						tag_list[genre] = 1
					else:
						tag_list[genre] += 1
					num_genres += 1
					genres += [genre]
				except:
					print(genre)
		i += 1
	genres.sort()
	genres = "|".join(genres)
	genre_list += [genres]

books["genre"] = genre_list
tags = ""
for tag in tag_list:
	if tag_list[tag] > 30:
		tags += tag + "\n"
with open("tags.txt", "w") as f:
	f.write(tags)

user_ids = list(set(ratings["user_id"].tolist()))
usernames = [str(i) for i in user_ids]
users = pd.DataFrame(columns = ["user_id", "username"])
users["user_id"] = user_ids
users["username"] = usernames

ratings = ratings.sort_values(by=["book_id"])

books.drop(["goodreads_book_id"], axis = 1, inplace = True)
books.to_csv("books_parsed.csv", index = False)
ratings.to_csv("ratings_parsed.csv", index = False)
users.to_csv("users_parsed.csv", index = False)

