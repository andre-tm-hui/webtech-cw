import pandas as pd
import numpy as np
import random, json, sys, os
from flask import Flask, render_template, request, redirect, Response
from scipy.sparse.linalg import svds
from statistics import mean
import matplotlib.pyplot as pyplot
from scipy.stats.stats import pearsonr

ratings = pd.read_csv("/ratings_parsed.csv")
books = pd.read_csv("/books_parsed.csv")
#print(books)
users = pd.read_csv("/users_parsed.csv")
users["username"] = users["username"].astype(str)
with open("tags.txt", "r") as f:
	filters = f.read().split("\n")
	filters = filters[:-1]

similarBooksDict = {}

# initiate a sorted dataframe of books by rating
book_data = pd.merge(ratings, books, on="book_id")
avg = book_data.groupby("book_id")["rating"].mean()
count = book_data.groupby("book_id")["rating"].count()

ratings_mean_count = pd.DataFrame(avg)
ratings_mean_count["rating_counts"] = pd.DataFrame(count)
ratings_mean_count = ratings_mean_count[ratings_mean_count["rating"] > 4].sort_values("rating_counts", ascending = False)

# matrix factorization
r_df = ratings.pivot(index = "user_id", columns = "book_id", values = "rating").fillna(0)
r_df.head()

r = r_df.as_matrix()
user_ratings_mean = np.mean(r, axis = 1)
r_demeaned = r - user_ratings_mean.reshape(-1,1)

# U is user "features" matrix, Vt is movie "features" matrix,
# sigma is diagonal matrix of singular values (weights)
U, sigma, Vt = svds(r_demeaned, k = 50)
sigma = np.diag(sigma)

# generate all the predicted ratings for every book for each user
all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) + user_ratings_mean.reshape(-1,1)
preds = pd.DataFrame(all_user_predicted_ratings, columns = r_df.columns)

# function to ask for recommendation
def recommend_books(predictions, user_id, books, original_ratings, num_recommendations = 5):
	# check if user is part of the pre-generated recommendations matrix
	if user_id in r_df.index.values.tolist():
		user_row_number = user_id - 1
		sorted_user_predictions = predictions.iloc[user_row_number].sort_values(ascending = False)

		# get user data and merge in book info
		user_data = original_ratings[original_ratings.user_id == user_id]
		user_full = (user_data.merge(books, how = "left", left_on = "book_id", right_on = "book_id").sort_values(["rating"], ascending = False))

		print("User {0} has already rated {1} books".format(user_id, user_full.shape[0]))
		print("Recommending the highest {0} predicted ratings books not already rated".format(num_recommendations))

		# recommend the highest predicted rating books that the user hasn't seen yet
		recommendations = (books[~books["book_id"].isin(user_full["book_id"])].
			merge(pd.DataFrame(sorted_user_predictions).reset_index(), how = "left",
				left_on = "book_id",
				right_on = "book_id").
			rename(columns = {user_row_number: "predictions"}).
			sort_values("predictions", ascending = False).
			iloc[:num_recommendations, :-1])
	else:
		user_books = ratings.loc[ratings["user_id"] == user_id]["book_id"].tolist()
		# check if the user has rated any books yet
		if len(user_books) == 0:
			# if not, return highest rated books in database
			book_ids = list(ratings_mean_count.index.values)[:num_recommendations]
			return books.loc[books["book_id"].isin(book_ids)]

		# filter ratings so that only users who have rat


		# make row for new user
		newr = ratings.pivot(index = "user_id", columns = "book_id", values = "rating").fillna(0)
		i = 0
		while newr.shape[0] > 1 and i < len(user_books):
			newr = newr.loc[newr[user_books[i]] > 0]
			i += 1
		already_rated = newr.iloc[int(user_id) - 1].head(r_df.shape[1])
		grouped_ratings = ratings.groupby("user_id")
		newr.drop(int(user_id), inplace=True)

		# find closely correlated users
		correlation = r_df.corrwith(already_rated, axis=1)
		corrs = pd.DataFrame(correlation, columns=["corr"])
		closest_corr = corrs.sort_values("corr", ascending=False).head(1)

		# get recommendations from the closely correlated user
		recommendations = recommend_books(predictions, closest_corr.index.values[0], books, original_ratings, num_recommendations)
	return recommendations

# check for similar books by comparing genres
def similarBooks(book_id, genres):
	genres = genres.split("|")
	genres.sort()
	numBooks = books.shape[0]
	b = books.copy()
	i = 0
	print(genres)
	while numBooks > 5 and i < len(genres):
		g ="|".join(genres[i:len(genres)])
		print(g)
		if b.loc[b["genre"].str.contains(genres[i])].shape[0] > 0:
			b = b.loc[b["genre"].str.contains(g)]
			numBooks = b.shape[0]
		i += 1
	similarBooksDict[book_id] = b["book_id"].tolist()
	return 0

# get a list of books similar to any books in book_ids
def checkSimilarBooks(book_ids):
	out = []
	for b in similarBooksDict:
		if bool(set(book_ids).intersection(similarBooksDict[b])):
			out += [b]
	return out


# init the flask server
app = Flask(__name__)
app._static_folder = os.path.abspath("templates/static")

@app.route("/")
def output():
	return render_template("/index.html", name="Yeet")

@app.route("/login", methods = ["POST"])
def checkID():
	data = request.get_json()
	try:
		user_id = users.loc[users["username"] == str(data["user_id"])]["user_id"].tolist()[0]
		print(user_id, data["user_id"])
		return "True"
	except:
		return "False"

@app.route("/mybooks", methods = ["POST"])
def getBooks():
	data = request.get_json()
	user_id = users.loc[users["username"] == str(data["user_id"])]["user_id"].tolist()[0]
	number = int(data["number"])
	filters = data["filters"]
	b = books.copy()
	for f in filters:
		b = b.loc[b["genre"].str.find(f) > -1]
	rating_table = ratings.loc[ratings["user_id"] == int(user_id)]
	book_id = rating_table["book_id"].tolist()
	rating = rating_table["rating"].tolist()
	titles = []
	book_ids = []
	temp_ratings = []
	for i in range(len(book_id)):
		if book_id[i] in b["book_id"].tolist():
			title = b.loc[b["book_id"] == book_id[i]]["title"].tolist()
			titles += title
			book_ids += [book_id[i]]
			temp_ratings += [rating[i]]
	if number == 0:
		number = len(titles)
	return {"book_id": book_ids[:number], "rating": temp_ratings[:number], "title": titles[:number]}

@app.route("/recommendations", methods = ["POST"])
def getRecommendations():
	data = request.get_json()
	user_id = int(users.loc[users["username"] == str(data["user_id"])]["user_id"].tolist()[0])
	number = int(data["number"])
	filters = data["filters"]
	b = books.copy()
	for f in filters:
		print(f)
		b = b.loc[books["genre"].str.find(f) > -1]
	if number == 0:
		number = 100
	predictions = recommend_books(preds, user_id, b, ratings, number)
	book_ids = predictions["book_id"].tolist()
	book_ids += list(dict.fromkeys(checkSimilarBooks(book_ids)))
	titles = books.loc[books["book_id"].isin(book_ids)]["title"].tolist()
	rs = []
	for bid in book_ids:
		temp = ratings.loc[ratings["book_id"] == bid]["rating"].tolist()
		if len(temp) > 0:
			thismean = mean(temp)
			rs += [round(thismean, 2)]
		else:
			rs += [3.00]
	return {"book_id": book_ids, "title": predictions["title"].tolist(), "rating": rs}

@app.route("/book", methods = ["POST"])
def getBook():
	data = request.get_json()
	bookid = int(data["book_id"])
	user_id = users.loc[users["username"] == str(data["user_id"])]["user_id"].tolist()[0]
	title = books.loc[books["book_id"] == bookid]["title"].tolist()[0]
	genres = books.loc[books["book_id"] == bookid]["genre"].tolist()[0]
	mean = ratings.loc[ratings["book_id"] == bookid]["rating"].mean()
	rated = ratings.loc[ratings["user_id"] == user_id]
	userrating = rated.loc[rated["book_id"] == bookid]["rating"].tolist()
	if len(userrating) > 0:
		userrating = round(userrating[0], 2)
	else:
		userrating = 0
	return {"book_id":bookid, "title": title, "rating": mean, "genre": genres, "userrating":userrating}

@app.route("/search", methods = ["POST"])
def search():
	data = request.get_json()
	query = data["query"]
	filters = data["filters"]
	b = books.copy()
	results = b.loc[b["title"].str.lower().str.find(query.lower()) > -1]
	book_ids = results["book_id"].tolist()
	rs = []
	for bid in book_ids:
		mean = ratings.loc[ratings["book_id"] == bid]["rating"].mean()
		rs += [round(mean, 2)]
	return {"book_id": book_ids, "title": results["title"].tolist(), "rating": rs}

@app.route("/filterlist", methods = ["POST"])
def getFilterList():
	return {"filters":filters}

@app.route("/rate", methods = ["POST"])
def rate():
	global ratings
	data = request.json
	user_id = users.loc[users["username"] == str(data["user_id"])]["user_id"].tolist()[0]
	rating = int(data["rating"])
	book_id = int(data["book_id"])
	try:
		rated = ratings.loc[ratings["user_id"] == user_id]
		rIndex = rated.loc[rated["book_id"] == book_id]
		ratings.at[rIndex.index.tolist()[0], "rating"] = rating
	except:
		newRating = pd.DataFrame([[user_id, book_id, rating]], columns = ["user_id", "book_id", "rating"])
		ratings = ratings.append(newRating, ignore_index = True)
	return "Success"

@app.route("/register", methods = ["POST"])
def register():
	data = request.json
	username = data["username"]
	global users
	if len(users.loc[users["username"] == username]["username"].tolist()) == 0:
		user_id = int(users.shape[0]) + 1
		userdata = pd.DataFrame([[user_id, username]], columns = ["user_id", "username"])
		users = users.append(userdata, ignore_index = True)
		return "Success"
	else:
		return "Fail"

@app.route("/top", methods = ["POST"])
def top():
	data = request.json
	n = data["number"]
	titles = []
	book_ids = list(ratings_mean_count.index.values)
	book_ids = [int(b) for b in book_ids]
	rs = ratings_mean_count["rating"].tolist()
	rs = [float(round(r,2)) for r in rs]
	for b in book_ids:
		titles += books.loc[books["book_id"] == b]["title"].tolist()
	return {"book_id": book_ids[:n], "title": titles[:n], "rating": rs[:n]}

@app.route("/newbook", methods = ["POST"])
def addBook():
	global books
	global ratings
	data = request.json
	title = data["title"]
	genres = data["genres"]
	rating = int(data["rating"])
	user_id = users.loc[users["username"] == str(data["user_id"])]["user_id"].tolist()[0]
	book_id = books.shape[0] + 1
	similarBooks(book_id, genres)
	newBook = pd.DataFrame([[book_id, title, genres]], columns = ["book_id", "title", "genre"])
	newRating = pd.DataFrame([[user_id, book_id, rating]], columns = ["user_id", "book_id", "rating"])
	books = books.append(newBook, ignore_index = True)
	ratings = ratings.append(newRating, ignore_index = True)
	return {}


if __name__ == "__main__":
	app.run()