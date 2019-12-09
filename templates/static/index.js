var url = window.location.href
var id
var filters
var active_filters = []
var rate = false
var current_book

$.ajaxSetup({
	contentType: "application/json; charset=utf-8"
});

function login() {
	userid = $("#userid").val().toString()
	if(userid) {
		obj = JSON.stringify({"user_id":userid})
		$.post("login", obj, function(data){
			var x = document.getElementById("wronguserid");
			if (data === "False") {
				x.innerHTML = "User ID does not exist. Try again."
				x.style.display = "block";
			} else {
				x.style.display = "none";
				var y = document.getElementById("login")
				y.style.display = "none";
				document.getElementById("main").style.display = "block"
				id = userid;
				getFilters();
				loadHome(false);
			}
		})
	}
	event.preventDefault();
}

function loadHome(newUser){
	console.log(1)
	loadBooks(10);
	if (newUser) {
		console.log(2)
		topBooks(10)
	} else {
		recommendations(10);
	}
	document.getElementById("allbooks").style.display = "none"
	document.getElementById("allrecs").style.display = "none"
	document.getElementById("home").style.display = "block"
}

function loadBooks(number) {
	$.post("mybooks", JSON.stringify({"user_id":id, "number":number.toString(), "filters":active_filters}), function(data){
		document.getElementById("yourbooks").innerHTML = book2buttons(data, false);
	})
}

function recommendations(number) {
	document.getElementById("main").style.display = "none"
	$.post("recommendations", JSON.stringify({"user_id":id, "filters":active_filters, "number":number}), function(data){
		document.getElementById("recommendations").innerHTML = book2buttons(data, false);
		document.getElementById("searchresults").style.display = "none"
		document.getElementById("main").style.display = "block"
	})
}

function yourbooks() {
	document.getElementById("main").style.display = "none"
	$.post("mybooks", JSON.stringify({"user_id":id, "number":0, "filters": active_filters}), function(data){
		console.log(data)
		html_string = book2buttons(data, true)
		console.log(html_string)
		document.getElementById("allbooks").innerHTML = html_string
		document.getElementById("home").style.display = "none"
		document.getElementById("allrecs").style.display = "none"
		document.getElementById("allbooks").style.display = "block"
		document.getElementById("searchresults").style.display = "none"
		document.getElementById("main").style.display = "block"
	})
}

function yourrec() {
	document.getElementById("main").style.display = "none"
	$.post("recommendations", JSON.stringify({"user_id":id, "filters":active_filters, "number":0}), function(data){
		document.getElementById("allrecs").innerHTML = book2buttons(data, true);
		document.getElementById("home").style.display = "none"
		document.getElementById("allbooks").style.display = "none"
		document.getElementById("allrecs").style.display = "block"
		document.getElementById("searchresults").style.display = "none"
		document.getElementById("main").style.display = "block"
	})
}

function book2buttons(data, whole_page) {
	book_id = data["book_id"];
	title = data["title"];
	rating = data["rating"];
	if(book_id.length == 0 || title.length == 0 || rating.length == 0) {
		return "No books found";
	}
	html_string = ""
	for(i = 0; i < book_id.length; i++){
		if(whole_page && i%5 == 0) {
			html_string += "<div class='row'>"
		}
		html_string += '<button class="btn btn-primary col-sm-2 p-1 m-1 btn-block" data-toggle="modal" data-target="#bookModal" onclick="getBook(' + book_id[i].toString() + ')"><p style="overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 5; line-height: 22px; max-height: 110px">' + title[i] + /**'</p><p>You Rated: ' + rating[i].toString() + '</p><p>Book ID: ' + book_id[i].toString() + **/'</p></button>'
		if(whole_page && i%5 == 4) {
			html_string += "</div>"
		}
	}
	return html_string;
}

function getFilters() {
	$.post("filterlist", {}, function(data){
		filters = data["filters"];
		html_string = ""
		for(i = 0; i < filters.length; i++){
			html_string += '<div class="radio"><label><input name="' + filters[i].toString() + '"type="checkbox" name="filter" onclick="updateFilter(\'' + filters[i].toString() + '\')">   ' + filters[i].toString() + '</label></div>'
		}
		document.getElementById("filterlist").innerHTML = html_string
	});
}

function search() {
	query = $("#searchform").val()
	$.post("search", JSON.stringify({"query": query, "filters":active_filters}), function(data){
		console.log(data)
		html_string = book2buttons(data, true)
		document.getElementById("results").innerHTML = html_string
		document.getElementById("query").innerHTML = "Search results for: " + query
		toggleSearch()
	})
	event.preventDefault();
}

function getBook(book_id) {
	$.post("book", JSON.stringify({"book_id":book_id, "user_id":id}), function(data){
		console.log(data)
		document.getElementById("booktitle").innerHTML = data["title"]
		document.getElementById("bookbody").innerHTML = "<p>Rating: " + data["rating"].toString() + "</p><p>Genres: " + data["genre"].split("|").join(", ") + "</p>" 
		console.log(data["userrating"])
		if(data["userrating"] > 0) {
			document.getElementById("yourrating").innerHTML = "<p>You rated this book: " + data["userrating"].toString() + "/5</p>"
			document.getElementById("rateButton").innerHTML = "Change Rating"
		} else {
			document.getElementById("yourrating").innerHTML = "<p>You have not rated this book</p>"
			document.getElementById("rateButton").innerHTML = "Rate"
		}
		document.getElementById("bookModal").style.display = "block"
		document.getElementById("bookModal").style.opacity = "1"
		current_book = book_id
		rate = false
	})
}

function closeModal() {
	document.getElementById("bookModal").style.display = "none"
	document.getElementById("bookModal").style.opacity = "0"
}

function changeRating() {
	if(!rate) {
		document.getElementById("yourrating").innerHTML = "<select id='selectrating' class='mdb-select md-form'><option value='' disabled selected>Choose your rating</option><option value='1'>1</option><option value='2'>2</option><option value='3'>3</option><option value='4'>4</option><option value='5'>5</option></select>"
		document.getElementById("rateButton").innerHTML = "Save"
		rate = true
	} else {
		rating = $("#selectrating").val()
		obj = JSON.stringify({"book_id": current_book.toString(), "user_id": id.toString(), "rating": rating.toString()})
		$.post("rate", obj, function(data){
			getBook(current_book)
		})
	}
}

function toggleSearch() {
	div = document.getElementById("searchresults")
	main = document.getElementById("main")
	console.log(div.style.display)
	if(div.style.display === "none") {
		div.style.display = "block"
		main.style.display = "none"
	} else {
		div.style.display = "none"
		main.style.display = "block"
	}
}

function updateFilter(filter) {
	i = active_filters.indexOf(filter)
	if(i > -1) {
		console.log(i)
		active_filters.splice(i, 1)
	} else {
		active_filters.push(filter)
	}
	console.log(active_filters)
	if(document.getElementById("home").style.display === "block") {
		loadHome()
	} else if(document.getElementById("allbooks").style.display === "block") {
		yourbooks()
	} else if(document.getElementById("allrecs").style.display === "block") {
		yourrec()
	}
}

function register() {
	userid = $("#userid").val().toString()
	console.log(userid)
	if (userid) {
		$.post("register", JSON.stringify({"username": userid}), function(data) {
			if (data === "Success") {
				document.getElementById("wronguserid").style.display = "none";
				document.getElementById("login").style.display = "none";
				document.getElementById("main").style.display = "block"
				id = userid;
				getFilters();
				loadHome(true);
			} else {
				x = document.getElementById("wronguserid")
				x.innerHTML = "This username is already taken."
				x.style.display = "block"
			}
		})
	}
	event.preventDefault()
}

function topBooks(int) {
	$.post("top", JSON.stringify({"number": int}), function(data) {
		document.getElementById("recommendations").innerHTML = book2buttons(data, false);
	})
}

function addBook() {
	if (document.getElementById("newBookModal").style.display === "block") {
		new_title = $("#new_title").val().toString()
		new_genres = $("#new_genres").val().toString()
		new_rating = $("#new_rating").val()
		$.post("newbook", JSON.stringify({"title": new_title, "genres": new_genres, "rating": new_rating, "user_id": id}), function(data) {
			alert("Thanks for your submission!")
			closeNewBook()
		})
	} else {
		document.getElementById("newBookModal").style.display = "block"
		document.getElementById("newBookModal").style.opacity = "1"
	}
}

function closeNewBook() {
	document.getElementById("newBookModal").style.display = "none"
}

